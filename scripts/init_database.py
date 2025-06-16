#!/usr/bin/env python3
"""
Initialize the Uruguay interview analysis database.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.database.connection import get_db, init_database
from src.config.config_loader import get_config


def main():
    """Initialize database with tables."""
    print("Uruguay Interview Analysis - Database Initialization")
    print("=" * 50)
    
    # Load configuration
    config = get_config()
    print(f"Database: {config.database.name}")
    print(f"Host: {config.database.host}:{config.database.port}")
    
    # Test connection
    db = get_db()
    if not db.test_connection():
        print("\n❌ Failed to connect to database!")
        print("Please check your database configuration and ensure PostgreSQL is running.")
        return 1
    
    print("\n✓ Database connection successful")
    
    # Confirm initialization
    response = input("\nThis will create all database tables. Continue? [y/N]: ")
    if response.lower() != 'y':
        print("Initialization cancelled.")
        return 0
    
    # Initialize database
    try:
        init_database()
        print("\n✓ Database tables created successfully!")
        
        # Show created tables
        from src.database.models import Base
        print("\nCreated tables:")
        for table in Base.metadata.sorted_tables:
            print(f"  - {table.name}")
        
        print("\n✓ Database is ready for use!")
        
    except Exception as e:
        print(f"\n❌ Failed to initialize database: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())