#!/usr/bin/env python3
"""
Database Connection Manager

Manages database connections, initialization, and lifecycle for the SEELE-E application.
"""

from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool, StaticPool, NullPool
from loguru import logger

from ...core.config.settings import get_settings
from .base import Base, metadata
from .session import get_session_manager


class DatabaseManager:
    """
    Manages database connections and initialization.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._engine: Optional[AsyncEngine] = None
        self._sync_engine = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """
        Initialize database connections and create tables if needed.
        """
        if self._initialized:
            logger.info("Database already initialized")
            return
        
        try:
            # Create async engine with appropriate pool for SQLite
            if "sqlite" in self.settings.database.database_url:
                # Use StaticPool for SQLite async connections
                self._engine = create_async_engine(
                    self.settings.database.database_url,
                    poolclass=StaticPool,
                    connect_args={"check_same_thread": False},
                    echo=self.settings.DEBUG,
                    future=True
                )
            else:
                # Use default pool for PostgreSQL
                self._engine = create_async_engine(
                    self.settings.database.database_url,
                    pool_size=self.settings.database.DB_POOL_SIZE,
                    max_overflow=self.settings.database.DB_MAX_OVERFLOW,
                    pool_timeout=self.settings.database.DB_POOL_TIMEOUT,
                    pool_recycle=self.settings.database.DB_POOL_RECYCLE,
                    echo=self.settings.DEBUG,
                    future=True
                )
            
            # Create sync engine for migrations
            self._sync_engine = create_engine(
                self.settings.database.sync_database_url,
                poolclass=QueuePool,
                pool_size=self.settings.database.DB_POOL_SIZE,
                max_overflow=self.settings.database.DB_MAX_OVERFLOW,
                pool_timeout=self.settings.database.DB_POOL_TIMEOUT,
                pool_recycle=self.settings.database.DB_POOL_RECYCLE,
                echo=self.settings.DEBUG,
                future=True
            )
            
            # Test connection
            await self._test_connection()
            
            # Initialize session manager
            session_manager = get_session_manager()
            session_manager.initialize(self._engine)
            
            self._initialized = True
            logger.info("✅ Database connection initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            raise
    
    async def _test_connection(self) -> None:
        """
        Test database connection.
        """
        try:
            async with self._engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                # For SQLite, fetchone() returns the result directly
                row = result.fetchone()
            logger.info("✅ Database connection test successful")
        except Exception as e:
            logger.error(f"❌ Database connection test failed: {e}")
            raise
    
    async def create_tables(self) -> None:
        """
        Create all database tables.
        """
        if not self._engine:
            raise RuntimeError("Database not initialized")
        
        try:
            async with self._engine.begin() as conn:
                await conn.run_sync(metadata.create_all)
            logger.info("✅ Database tables created successfully")
        except Exception as e:
            logger.error(f"❌ Failed to create database tables: {e}")
            raise
    
    async def drop_tables(self) -> None:
        """
        Drop all database tables.
        """
        if not self._engine:
            raise RuntimeError("Database not initialized")
        
        try:
            async with self._engine.begin() as conn:
                await conn.run_sync(metadata.drop_all)
            logger.info("✅ Database tables dropped successfully")
        except Exception as e:
            logger.error(f"❌ Failed to drop database tables: {e}")
            raise
    
    async def close(self) -> None:
        """
        Close database connections.
        """
        if self._engine:
            await self._engine.dispose()
            logger.info("✅ Database connections closed")
        
        if self._sync_engine:
            self._sync_engine.dispose()
        
        self._initialized = False
    
    @property
    def engine(self) -> AsyncEngine:
        """
        Get the async database engine.
        """
        if not self._engine:
            raise RuntimeError("Database not initialized")
        return self._engine
    
    @property
    def sync_engine(self):
        """
        Get the sync database engine.
        """
        if not self._sync_engine:
            raise RuntimeError("Database not initialized")
        return self._sync_engine
    
    @property
    def is_initialized(self) -> bool:
        """
        Check if database is initialized.
        """
        return self._initialized


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """
    Get the global database manager instance.
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager