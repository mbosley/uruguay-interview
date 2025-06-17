#!/usr/bin/env python3
"""
Initialize the database schema for Uruguay Interview Analysis
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.database.connection import DatabaseConnection
from src.database.models import Base
from src.config.config_loader import get_config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize database with all required tables."""
    config = get_config()
    db = DatabaseConnection(config.database.url)
    
    try:
        # Drop all tables if they exist (for clean start)
        logger.info("Dropping existing tables...")
        Base.metadata.drop_all(db.engine)
        
        # Create all tables
        logger.info("Creating database schema...")
        Base.metadata.create_all(db.engine)
        
        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        logger.info(f"Created {len(tables)} tables:")
        for table in sorted(tables):
            logger.info(f"  - {table}")
        
        # Test connection
        with db.get_session() as session:
            from src.database.models import Interview
            count = session.query(Interview).count()
            logger.info(f"Database initialized successfully. Current interviews: {count}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)