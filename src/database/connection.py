"""
Database connection and session management.
"""
import logging
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import Pool

from src.config.config_loader import get_config
from src.database.models import Base

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Manages database connections and sessions."""
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database connection.
        
        Args:
            database_url: Database URL (uses config if not provided)
        """
        self.config = get_config()
        self.database_url = database_url or self.config.database.url
        
        # Create engine
        self.engine = create_engine(
            self.database_url,
            pool_size=self.config.database.pool_size,
            echo=self.config.database.echo,
            pool_pre_ping=True  # Verify connections before using
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        # Set up event listeners
        self._setup_listeners()
        
        logger.info(f"Database connection initialized: {self._safe_url()}")
    
    def _safe_url(self) -> str:
        """Return database URL with password masked."""
        url = str(self.database_url)
        if '@' in url:
            # Mask password
            parts = url.split('@')
            if ':' in parts[0]:
                prefix = parts[0].split(':')
                prefix[-1] = '****'
                parts[0] = ':'.join(prefix)
            return '@'.join(parts)
        return url
    
    def _setup_listeners(self):
        """Set up SQLAlchemy event listeners."""
        @event.listens_for(Pool, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            """Enable foreign keys for SQLite."""
            if 'sqlite' in self.database_url:
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
    
    def create_tables(self):
        """Create all database tables."""
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")
    
    def drop_tables(self):
        """Drop all database tables."""
        logger.warning("Dropping all database tables...")
        Base.metadata.drop_all(bind=self.engine)
        logger.info("Database tables dropped")
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Get a database session with automatic cleanup.
        
        Yields:
            Database session
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def test_connection(self) -> bool:
        """
        Test database connection.
        
        Returns:
            True if connection successful
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False


# Global database connection instance
_db_connection: Optional[DatabaseConnection] = None


def get_db() -> DatabaseConnection:
    """Get the global database connection instance."""
    global _db_connection
    if _db_connection is None:
        _db_connection = DatabaseConnection()
    return _db_connection


def get_session() -> Generator[Session, None, None]:
    """Get a database session."""
    db = get_db()
    with db.get_session() as session:
        yield session


def init_database():
    """Initialize database (create tables if needed)."""
    db = get_db()
    if db.test_connection():
        db.create_tables()
        return True
    return False


def reset_database():
    """Reset database (drop and recreate tables)."""
    db = get_db()
    db.drop_tables()
    db.create_tables()