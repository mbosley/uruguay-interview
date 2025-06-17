#!/usr/bin/env python3
"""
Add turn-level tables to the database for multi-turn conversation storage
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

def add_turn_tables():
    """Add turn-level tables to existing database."""
    config = get_config()
    db = DatabaseConnection(config.database.url)
    
    try:
        # Create only the new tables (not dropping existing ones)
        logger.info("Creating turn-level tables...")
        
        # Get metadata for all tables
        metadata = Base.metadata
        
        # List of new turn-related tables
        turn_tables = [
            'turns',
            'turn_functional_annotations',
            'turn_content_annotations',
            'turn_evidence',
            'turn_stance',
            'conversation_dynamics'
        ]
        
        # Create only the new tables
        for table_name in turn_tables:
            if table_name in metadata.tables:
                table = metadata.tables[table_name]
                logger.info(f"Creating table: {table_name}")
                table.create(db.engine, checkfirst=True)
        
        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        created_count = 0
        for table_name in turn_tables:
            if table_name in existing_tables:
                logger.info(f"  ✓ {table_name}")
                created_count += 1
            else:
                logger.warning(f"  ✗ {table_name} - not created")
        
        logger.info(f"\nSuccessfully created {created_count}/{len(turn_tables)} turn-level tables")
        
        # Test the new tables
        with db.get_session() as session:
            from src.database.models import Turn
            turn_count = session.query(Turn).count()
            logger.info(f"Turn table is accessible. Current turns: {turn_count}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to add turn tables: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = add_turn_tables()
    sys.exit(0 if success else 1)