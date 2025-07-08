#!/usr/bin/env python3
"""
Add citation tracking tables to support hierarchical citation system.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.models import Base, TurnCitationMetadata, InterviewInsightCitation
from src.database.connection import get_engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_citation_tables():
    """Add citation-related tables to database."""
    engine = get_engine()
    
    # Create new tables
    logger.info("Creating citation metadata tables...")
    Base.metadata.create_all(engine, tables=[
        TurnCitationMetadata.__table__,
        InterviewInsightCitation.__table__
    ])
    
    logger.info("Citation tables created successfully!")
    
    # Also create indexes using raw SQL for better control
    with engine.connect() as conn:
        logger.info("Creating indexes for citation tables...")
        
        # Index for turn citation metadata
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_turn_citation_turn_id 
            ON turn_citation_metadata(turn_id);
        """)
        
        # Indexes for interview insight citations
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_interview_citation_interview_id 
            ON interview_insight_citations(interview_id);
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_interview_citation_insight 
            ON interview_insight_citations(insight_type, insight_id);
        """)
        
        conn.commit()
        logger.info("Indexes created successfully!")

def verify_tables():
    """Verify that citation tables were created correctly."""
    engine = get_engine()
    
    with engine.connect() as conn:
        # Check turn citation metadata table
        result = conn.execute("""
            SELECT sql FROM sqlite_master 
            WHERE type='table' AND name='turn_citation_metadata';
        """)
        table_def = result.fetchone()
        
        if table_def:
            logger.info("turn_citation_metadata table created:")
            logger.info(table_def[0])
        else:
            logger.error("turn_citation_metadata table not found!")
            
        # Check interview insight citations table
        result = conn.execute("""
            SELECT sql FROM sqlite_master 
            WHERE type='table' AND name='interview_insight_citations';
        """)
        table_def = result.fetchone()
        
        if table_def:
            logger.info("interview_insight_citations table created:")
            logger.info(table_def[0])
        else:
            logger.error("interview_insight_citations table not found!")

if __name__ == "__main__":
    logger.info("Starting citation table migration...")
    
    try:
        add_citation_tables()
        verify_tables()
        logger.info("Migration completed successfully!")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)