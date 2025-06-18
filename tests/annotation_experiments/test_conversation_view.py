#!/usr/bin/env python3
"""
Test the conversation view independently
"""
import streamlit as st
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.database.connection import DatabaseConnection
from src.database.models import Interview, Turn, TurnFunctionalAnnotation
from src.config.config_loader import get_config
from src.dashboard.conversation_view import show_conversation_flow
from sqlalchemy.orm import joinedload

st.set_page_config(page_title="Test Conversation View", layout="wide")

def main():
    st.title("Test Conversation View")
    
    config = get_config()
    db = DatabaseConnection(config.database.url)
    
    # Get interview
    with db.get_session() as session:
        interview = session.query(Interview).filter_by(interview_id="058").first()
        
        if interview:
            st.success(f"Found interview {interview.interview_id}")
            
            # Check turns
            turns = session.query(Turn).filter_by(interview_id=interview.id).all()
            st.info(f"Interview has {len(turns)} turns")
            
            # Show conversation flow
            st.markdown("---")
            show_conversation_flow(interview.id, session)
        else:
            st.error("Interview 058 not found")

if __name__ == "__main__":
    main()