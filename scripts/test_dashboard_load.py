#!/usr/bin/env python3
"""
Test dashboard data loading without running Streamlit
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.database.connection import DatabaseConnection
from src.database.repository import InterviewRepository
from src.database.models import Interview, Turn
from src.config.config_loader import get_config
from sqlalchemy.orm import joinedload
import pandas as pd

def test_dashboard_load():
    """Test the dashboard data loading logic."""
    config = get_config()
    db = DatabaseConnection(config.database.url)
    repo = InterviewRepository(db)
    
    print("Testing dashboard data loading...")
    
    # Test 1: Load overview data
    with db.get_session() as session:
        interviews = repo.get_all(session)
        print(f"\n1. Loaded {len(interviews)} interviews")
        
        # Extract interview list (like dashboard does)
        interview_list = []
        for interview in interviews:
            interview_list.append({
                'id': interview.id,
                'interview_id': interview.interview_id,
                'date': interview.date,
                'time': interview.time,
                'location': interview.location,
                'department': interview.department,
                'participant_count': interview.participant_count,
                'has_annotations': len(interview.annotations) > 0,
                'has_turns': len(interview.turns) > 0 if hasattr(interview, 'turns') else False
            })
        
        print(f"   Interview list created: {len(interview_list)} items")
        if interview_list:
            print(f"   First interview: {interview_list[0]}")
    
    # Test 2: Load specific interview with turns
    if interview_list:
        interview_id = interview_list[0]['id']
        print(f"\n2. Loading interview details for ID {interview_id}")
        
        with db.get_session() as session:
            interview = session.query(Interview).options(
                joinedload(Interview.annotations),
                joinedload(Interview.priorities),
                joinedload(Interview.themes),
                joinedload(Interview.emotions)
            ).filter(Interview.id == interview_id).first()
            
            if interview:
                print(f"   Interview loaded: {interview.interview_id}")
                print(f"   Has turns: {hasattr(interview, 'turns')}")
                
                # Test turn access
                turns = session.query(Turn).filter_by(interview_id=interview.id).all()
                print(f"   Direct turn query: {len(turns)} turns")
                
                # Extract data like dashboard does
                interview_data = {
                    'date': interview.date,
                    'time': interview.time,
                    'location': interview.location,
                    'department': interview.department,
                    'participant_count': interview.participant_count,
                    'word_count': interview.word_count,
                    'raw_text': interview.raw_text,
                    'annotations': [{
                        'overall_sentiment': ann.overall_sentiment,
                        'dominant_emotion': ann.dominant_emotion
                    } for ann in interview.annotations],
                    'priorities': [{
                        'scope': p.scope,
                        'rank': p.rank,
                        'category': p.category,
                        'description': p.description
                    } for p in interview.priorities]
                }
                
                print(f"   Data extracted successfully")
                print(f"   Priorities: {len(interview_data['priorities'])}")
                print(f"   Annotations: {len(interview_data['annotations'])}")
    
    print("\n✅ Dashboard data loading test completed successfully")

if __name__ == "__main__":
    test_dashboard_load()