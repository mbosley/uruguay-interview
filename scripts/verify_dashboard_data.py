#!/usr/bin/env python3
"""
Verify dashboard can access data
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.database.connection import DatabaseConnection
from src.database.repository import InterviewRepository
from src.config.config_loader import get_config

def verify_data():
    """Verify data is accessible for dashboard."""
    config = get_config()
    db = DatabaseConnection(config.database.url)
    repo = InterviewRepository(db)
    
    with db.get_session() as session:
        interviews = repo.get_all(session)
        
        print(f"Found {len(interviews)} interviews in database")
        
        for interview in interviews:
            print(f"\nInterview {interview.interview_id}:")
            print(f"  - Date: {interview.date}")
            print(f"  - Location: {interview.location}")
            print(f"  - Department: {interview.department}")
            print(f"  - Annotations: {len(interview.annotations)}")
            
            for annotation in interview.annotations:
                print(f"  - Model: {annotation.model_provider}/{annotation.model_name}")
                print(f"  - Sentiment: {annotation.overall_sentiment}")
                print(f"  - Confidence: {annotation.confidence_score}")
                print(f"  - Priorities: {len(interview.priorities)}")
                print(f"  - Themes: {len(interview.themes)}")

if __name__ == "__main__":
    verify_data()