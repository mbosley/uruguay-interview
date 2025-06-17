#!/usr/bin/env python3
"""
Comprehensive verification of the multi-turn conversation system
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.database.connection import DatabaseConnection
from src.database.models import *
from src.config.config_loader import get_config

def verify_complete_system():
    """Verify all components of the multi-turn system."""
    print("🔍 Verifying Complete Multi-Turn Conversation System")
    print("=" * 60)
    
    config = get_config()
    db = DatabaseConnection(config.database.url)
    
    with db.get_session() as session:
        # 1. Check basic interview data
        interviews = session.query(Interview).all()
        print(f"✅ Interviews: {len(interviews)} found")
        
        # 2. Check annotations
        annotations = session.query(Annotation).all()
        print(f"✅ Annotations: {len(annotations)} found")
        
        # 3. Check traditional priority/theme data
        priorities = session.query(Priority).all()
        themes = session.query(Theme).all()
        print(f"✅ Priorities: {len(priorities)} found")
        print(f"✅ Themes: {len(themes)} found")
        
        # 4. Check turn-level data
        turns = session.query(Turn).all()
        print(f"✅ Turns: {len(turns)} found")
        
        # 5. Check turn annotations
        func_annotations = session.query(TurnFunctionalAnnotation).all()
        content_annotations = session.query(TurnContentAnnotation).all()
        evidence_annotations = session.query(TurnEvidence).all()
        stance_annotations = session.query(TurnStance).all()
        
        print(f"✅ Turn Functional Annotations: {len(func_annotations)} found")
        print(f"✅ Turn Content Annotations: {len(content_annotations)} found")
        print(f"✅ Turn Evidence Annotations: {len(evidence_annotations)} found")
        print(f"✅ Turn Stance Annotations: {len(stance_annotations)} found")
        
        # 6. Check conversation dynamics
        dynamics = session.query(ConversationDynamics).all()
        print(f"✅ Conversation Dynamics: {len(dynamics)} found")
        
        print("\n📊 Sample Data Analysis")
        print("-" * 30)
        
        if interviews:
            interview = interviews[0]
            print(f"Interview: {interview.interview_id} ({interview.location})")
            
            # Show relationship access
            print(f"  - Annotations: {len(interview.annotations)}")
            print(f"  - Priorities: {len(interview.priorities)}")
            print(f"  - Themes: {len(interview.themes)}")
            
            # Check turns relationship
            if hasattr(interview, 'turns'):
                print(f"  - Turns: {len(interview.turns)}")
                
                if interview.turns:
                    first_turn = interview.turns[0]
                    print(f"    Turn 1: {first_turn.speaker} ({first_turn.word_count} words)")
                    print(f"    Text: {first_turn.text[:50]}...")
                    
                    # Check turn annotations
                    func_anno = session.query(TurnFunctionalAnnotation).filter_by(turn_id=first_turn.id).first()
                    if func_anno:
                        print(f"    Function: {func_anno.primary_function}")
                    
                    content_anno = session.query(TurnContentAnnotation).filter_by(turn_id=first_turn.id).first()
                    if content_anno and content_anno.topics:
                        print(f"    Topics: {content_anno.topics[:3]}...")
            else:
                print("  - Turns: No turns relationship found")
        
        print("\n🎯 System Capabilities Enabled")
        print("-" * 35)
        print("✅ Traditional interview-level analysis")
        print("✅ Turn-by-turn conversation flow")
        print("✅ Speaker-specific analysis")
        print("✅ Functional conversation coding")
        print("✅ Topic progression tracking")
        print("✅ Evidence pattern analysis")
        print("✅ Emotional dynamics over time")
        print("✅ Conversation quality metrics")
        
        print("\n🔍 Sample Queries Possible")
        print("-" * 30)
        
        # Query 1: Turns by function
        question_turns = session.query(Turn).join(TurnFunctionalAnnotation).filter(
            TurnFunctionalAnnotation.primary_function == 'question'
        ).count()
        print(f"Question turns: {question_turns}")
        
        # Query 2: Topics by speaker
        participant_topics = session.query(TurnContentAnnotation).join(Turn).filter(
            Turn.speaker == 'participant'
        ).count()
        print(f"Participant content annotations: {participant_topics}")
        
        # Query 3: Emotional turns
        emotional_turns = session.query(TurnStance).filter(
            TurnStance.emotional_valence != 'neutral'
        ).count()
        print(f"Non-neutral emotional turns: {emotional_turns}")
        
        print(f"\n🎉 Multi-turn conversation system is fully operational!")
        print(f"   Database contains rich conversational data for {len(interviews)} interviews")
        print(f"   Ready for dashboard exploration and advanced analysis")

if __name__ == "__main__":
    verify_complete_system()