#!/usr/bin/env python3
"""
Add Moral Foundations Theory (MFT) tables to the existing database.
"""

import sqlite3
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.models_mft import CREATE_TABLES_SQL


def add_mft_tables():
    """Add MFT tables to the existing database."""
    
    # Database path
    db_path = project_root / "data" / "uruguay_interviews.db"
    
    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        return False
    
    print(f"📊 Adding MFT tables to database: {db_path}")
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Execute CREATE TABLE statements
        for statement in CREATE_TABLES_SQL.strip().split(';'):
            if statement.strip():
                print(f"  Executing: {statement.strip()[:50]}...")
                cursor.execute(statement)
        
        # Commit changes
        conn.commit()
        
        # Verify tables were created
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name LIKE '%moral_foundations%'
            ORDER BY name
        """)
        
        tables = cursor.fetchall()
        print(f"\n✅ Successfully created {len(tables)} MFT tables:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Check if we need to add relationship columns to existing tables
        cursor.execute("PRAGMA table_info(turns)")
        turn_columns = [col[1] for col in cursor.fetchall()]
        
        if 'moral_foundations' not in turn_columns:
            print("\n📝 Note: You may need to update the Turn model to include the moral_foundations relationship")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error adding MFT tables: {e}")
        return False


def check_database_schema():
    """Display current database schema for verification."""
    
    db_path = project_root / "data" / "uruguay_interviews.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n📋 Current database schema:")
    
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        ORDER BY name
    """)
    
    tables = cursor.fetchall()
    for table in tables:
        print(f"\n  Table: {table[0]}")
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        for col in columns[:5]:  # Show first 5 columns
            print(f"    - {col[1]} ({col[2]})")
        if len(columns) > 5:
            print(f"    ... and {len(columns) - 5} more columns")
    
    conn.close()


if __name__ == "__main__":
    print("🔧 MFT Database Table Creation Script")
    print("=" * 50)
    
    # Add MFT tables
    success = add_mft_tables()
    
    if success:
        # Show updated schema
        check_database_schema()
        print("\n✅ MFT tables successfully added to database!")
        print("   Ready to store moral foundations analysis.")
    else:
        print("\n❌ Failed to add MFT tables.")