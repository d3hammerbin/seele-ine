#!/usr/bin/env python3
"""
Database Session Management

Provides database session management for FastAPI dependency injection.
"""

from typing import Generator, Optional, AsyncGenerator
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from contextlib import contextmanager, asynccontextmanager

from .base import get_database, get_session
from ...core.config.settings import get_settings

# Initialize database on module import
settings = get_settings()

# Global database initialization flag
_db_initialized = False


class SessionManager:
    """
    Manages database sessions for async operations.
    """
    
    def __init__(self):
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker] = None
    
    def initialize(self, engine: AsyncEngine) -> None:
        """
        Initialize session manager with database engine.
        """
        self._engine = engine
        self._session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    def get_session(self) -> AsyncSession:
        """
        Get a new database session.
        """
        if not self._session_factory:
            raise RuntimeError("Session manager not initialized")
        return self._session_factory()
    
    @property
    def is_initialized(self) -> bool:
        """
        Check if session manager is initialized.
        """
        return self._session_factory is not None


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """
    Get the global session manager instance.
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager

def init_db() -> None:
    """Initialize database connection."""
    global _db_initialized
    if not _db_initialized:
        from .base import init_database
        database_url = settings.database.sync_database_url
        init_database(database_url, echo=settings.DEBUG)
        _db_initialized = True

def get_db_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency to get database session.
    
    Yields:
        Database session
    """
    # Ensure database is initialized
    init_db()
    
    # Get session from database manager
    session = get_session()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency to get async database session.
    
    Yields:
        Async database session
    """
    # Get session manager
    session_manager = get_session_manager()
    
    if not session_manager.is_initialized:
        raise RuntimeError("Session manager not initialized")
    
    # Get async session
    session = session_manager.get_session()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()

@asynccontextmanager
async def get_async_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database session.
    
    Yields:
        Async database session
    """
    # Get session manager
    session_manager = get_session_manager()
    
    if not session_manager.is_initialized:
        raise RuntimeError("Session manager not initialized")
    
    # Get async session
    session = session_manager.get_session()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database session.
    
    Yields:
        Database session
    """
    # Ensure database is initialized
    init_db()
    
    # Get session from database manager
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def create_tables() -> None:
    """
    Create all database tables.
    """
    init_db()
    db = get_database()
    db.create_tables()

def drop_tables() -> None:
    """
    Drop all database tables.
    """
    init_db()
    db = get_database()
    db.drop_tables()