#!/usr/bin/env python3
"""
Verify turn data is properly stored and accessible
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.database.connection import DatabaseConnection
from src.database.models import Interview, Turn, TurnFunctionalAnnotation, ConversationDynamics
from src.config.config_loader import get_config

def verify_turns():
    """Verify turn data is accessible."""
    config = get_config()
    db = DatabaseConnection(config.database.url)
    
    with db.get_session() as session:
        # Find interview 058
        interview = session.query(Interview).filter_by(interview_id="058").first()
        if not interview:
            print("Interview 058 not found")
            return
        
        print(f"Interview {interview.interview_id}:")
        print(f"  Location: {interview.location}")
        print(f"  Date: {interview.date}")
        
        # Check turns
        turns = session.query(Turn).filter_by(interview_id=interview.id).order_by(Turn.turn_number).all()
        print(f"\nFound {len(turns)} turns:")
        
        for turn in turns:
            func_anno = session.query(TurnFunctionalAnnotation).filter_by(turn_id=turn.id).first()
            print(f"\nTurn {turn.turn_number} ({turn.speaker}):")
            print(f"  Words: {turn.word_count}")
            print(f"  Function: {func_anno.primary_function if func_anno else 'N/A'}")
            print(f"  Text preview: {turn.text[:50]}...")
        
        # Check conversation dynamics
        dynamics = session.query(ConversationDynamics).filter_by(interview_id=interview.id).first()
        if dynamics:
            print(f"\nConversation Dynamics:")
            print(f"  Total turns: {dynamics.total_turns}")
            print(f"  Speaker balance: {dynamics.speaker_balance:.2f}")
            print(f"  Avg turn length: {dynamics.average_turn_length:.1f} words")
            print(f"  Conversation flow: {dynamics.conversation_flow}")

if __name__ == "__main__":
    verify_turns()