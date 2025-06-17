#!/usr/bin/env python3
"""
Add raw text to interview 058 in the database
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.database.connection import DatabaseConnection
from src.database.models import Interview
from src.config.config_loader import get_config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_raw_text():
    """Add raw text from the processed interview file."""
    config = get_config()
    db = DatabaseConnection(config.database.url)
    
    # Path to the text file
    text_file = Path("data/processed/interviews_txt/20250528_0900_058.txt")
    
    if not text_file.exists():
        logger.error(f"Text file not found: {text_file}")
        return False
    
    try:
        # Read the raw text
        with open(text_file, 'r', encoding='utf-8') as f:
            raw_text = f.read()
        
        logger.info(f"Read {len(raw_text)} characters from {text_file}")
        
        # Update the database
        with db.get_session() as session:
            interview = session.query(Interview).filter_by(interview_id="058").first()
            
            if not interview:
                logger.error("Interview 058 not found in database")
                return False
            
            # Update the raw text
            interview.raw_text = raw_text
            session.commit()
            
            logger.info(f"Successfully updated interview {interview.interview_id} with raw text")
            logger.info(f"Raw text length: {len(interview.raw_text)} characters")
            
        return True
        
    except Exception as e:
        logger.error(f"Failed to add raw text: {e}")
        return False

if __name__ == "__main__":
    success = add_raw_text()
    sys.exit(0 if success else 1)