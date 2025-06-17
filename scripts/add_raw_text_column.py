#!/usr/bin/env python3
"""
Add raw_text column to interviews table
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.database.connection import DatabaseConnection
from src.config.config_loader import get_config
from sqlalchemy import text

def main():
    """Add raw_text column to interviews table."""
    config = get_config()
    db = DatabaseConnection(config.database.url)
    
    with db.engine.connect() as conn:
        # Check if column already exists (SQLite)
        result = conn.execute(text("""
            SELECT name FROM pragma_table_info('interviews') WHERE name='raw_text'
        """))
        
        if result.fetchone() is None:
            # Add the column
            conn.execute(text("ALTER TABLE interviews ADD COLUMN raw_text TEXT"))
            conn.commit()
            print("✅ Added raw_text column to interviews table")
        else:
            print("ℹ️  raw_text column already exists")

if __name__ == "__main__":
    main()