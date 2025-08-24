#!/usr/bin/env python3
"""
Database Base Configuration

Contains base database configuration, session management, and common model utilities.
"""

from typing import Any, Dict, Optional
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import create_engine, MetaData, Column, DateTime, String
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.engine import Engine

# Database metadata with naming convention for constraints
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }
)

# Base class for all models
Base = declarative_base(metadata=metadata)


class BaseModel(Base):
    """Base model class with common fields and utilities."""
    
    __abstract__ = True
    
    # Common fields for all models
    id = Column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False
    )
    
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name."""
        # Convert CamelCase to snake_case
        import re
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
    
    def to_dict(self, exclude: Optional[set] = None) -> Dict[str, Any]:
        """Convert model instance to dictionary.
        
        Args:
            exclude: Set of field names to exclude
            
        Returns:
            Dictionary representation of the model
        """
        exclude = exclude or set()
        result = {}
        
        for column in self.__table__.columns:
            if column.name not in exclude:
                value = getattr(self, column.name)
                
                # Handle special types
                if isinstance(value, UUID):
                    value = str(value)
                elif isinstance(value, datetime):
                    value = value.isoformat()
                elif hasattr(value, 'value'):  # Enum types
                    value = value.value
                
                result[column.name] = value
        
        return result
    
    def update_from_dict(self, data: Dict[str, Any], exclude: Optional[set] = None) -> None:
        """Update model instance from dictionary.
        
        Args:
            data: Dictionary with field values
            exclude: Set of field names to exclude from update
        """
        exclude = exclude or {'id', 'created_at'}
        
        for key, value in data.items():
            if key not in exclude and hasattr(self, key):
                setattr(self, key, value)
        
        # Always update the updated_at timestamp
        self.updated_at = datetime.utcnow()
    
    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id={self.id})>"


class DatabaseManager:
    """Database connection and session management."""
    
    def __init__(self, database_url: str, echo: bool = False):
        """Initialize database manager.
        
        Args:
            database_url: Database connection URL
            echo: Whether to echo SQL statements
        """
        self.database_url = database_url
        self.echo = echo
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None
    
    @property
    def engine(self) -> Engine:
        """Get database engine."""
        if self._engine is None:
            self._engine = create_engine(
                self.database_url,
                echo=self.echo,
                pool_pre_ping=True,
                pool_recycle=3600,
                pool_size=10,
                max_overflow=20
            )
        return self._engine
    
    @property
    def session_factory(self) -> sessionmaker:
        """Get session factory."""
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False
            )
        return self._session_factory
    
    def get_session(self) -> Session:
        """Get database session.
        
        Returns:
            Database session
        """
        return self.session_factory()
    
    def create_tables(self) -> None:
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self) -> None:
        """Drop all database tables."""
        Base.metadata.drop_all(bind=self.engine)
    
    def close(self) -> None:
        """Close database connections."""
        if self._engine:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None


class SessionManager:
    """Context manager for database sessions."""
    
    def __init__(self, session_factory: sessionmaker):
        """Initialize session manager.
        
        Args:
            session_factory: SQLAlchemy session factory
        """
        self.session_factory = session_factory
        self.session: Optional[Session] = None
    
    def __enter__(self) -> Session:
        """Enter context manager.
        
        Returns:
            Database session
        """
        self.session = self.session_factory()
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager.
        
        Args:
            exc_type: Exception type
            exc_val: Exception value
            exc_tb: Exception traceback
        """
        if self.session:
            if exc_type is not None:
                self.session.rollback()
            else:
                try:
                    self.session.commit()
                except Exception:
                    self.session.rollback()
                    raise
                finally:
                    self.session.close()
                    self.session = None


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def init_database(database_url: str, echo: bool = False) -> DatabaseManager:
    """Initialize global database manager.
    
    Args:
        database_url: Database connection URL
        echo: Whether to echo SQL statements
        
    Returns:
        Database manager instance
    """
    global _db_manager
    _db_manager = DatabaseManager(database_url, echo)
    return _db_manager


def get_database() -> DatabaseManager:
    """Get global database manager.
    
    Returns:
        Database manager instance
        
    Raises:
        RuntimeError: If database not initialized
    """
    if _db_manager is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _db_manager


def get_session() -> Session:
    """Get database session.
    
    Returns:
        Database session
        
    Raises:
        RuntimeError: If database not initialized
    """
    return get_database().get_session()


def get_session_manager() -> SessionManager:
    """Get session manager.
    
    Returns:
        Session manager instance
        
    Raises:
        RuntimeError: If database not initialized
    """
    return SessionManager(get_database().session_factory)