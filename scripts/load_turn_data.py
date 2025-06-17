#!/usr/bin/env python3
"""
Load turn-level data from XML annotation into database
"""
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.database.connection import DatabaseConnection
from src.database.models import (
    Interview, Annotation, Turn, TurnFunctionalAnnotation,
    TurnContentAnnotation, TurnEvidence, TurnStance, ConversationDynamics
)
from src.config.config_loader import get_config
from src.pipeline.extraction.turn_extractor import TurnExtractor
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_turn_data():
    """Load turn data from existing XML annotation."""
    config = get_config()
    db = DatabaseConnection(config.database.url)
    extractor = TurnExtractor()
    
    # Path to existing XML annotation
    xml_path = Path("data/processed/annotations/xml/058_annotation.xml")
    
    if not xml_path.exists():
        logger.error(f"XML file not found: {xml_path}")
        return False
    
    try:
        # Extract turn data
        logger.info(f"Extracting turn data from {xml_path}")
        turns, dynamics = extractor.extract_turns(xml_path)
        logger.info(f"Found {len(turns)} turns")
        
        with db.get_session() as session:
            # Find the interview and annotation
            interview = session.query(Interview).filter_by(interview_id="058").first()
            if not interview:
                logger.error("Interview 058 not found in database")
                return False
            
            annotation = session.query(Annotation).filter_by(interview_id=interview.id).first()
            if not annotation:
                logger.error("Annotation not found for interview 058")
                return False
            
            # Add each turn
            for turn_data in turns:
                # Create Turn record
                turn = Turn(
                    interview_id=interview.id,
                    annotation_id=annotation.id,
                    turn_number=turn_data.turn_number,
                    speaker=turn_data.speaker,
                    speaker_id=None,  # Not available in current data
                    text=turn_data.text,
                    word_count=turn_data.word_count
                )
                session.add(turn)
                session.flush()  # Get turn.id
                
                # Add functional annotation
                if turn_data.primary_function:
                    func_anno = TurnFunctionalAnnotation(
                        turn_id=turn.id,
                        primary_function=turn_data.primary_function,
                        secondary_functions=turn_data.secondary_functions if turn_data.secondary_functions else None,
                        coding_confidence=turn_data.coding_confidence,
                        ambiguous_function=turn_data.ambiguous_function,
                        uncertainty_notes=turn_data.uncertainty_notes
                    )
                    session.add(func_anno)
                
                # Add content annotation
                if turn_data.topics or turn_data.geographic_scope:
                    content_anno = TurnContentAnnotation(
                        turn_id=turn.id,
                        topics=turn_data.topics,
                        topic_narrative=turn_data.topic_narrative,
                        geographic_scope=turn_data.geographic_scope if turn_data.geographic_scope else None,
                        temporal_reference=turn_data.temporal_reference,
                        actors_mentioned=turn_data.actors_mentioned if turn_data.actors_mentioned else None,
                        indicates_priority=turn_data.indicates_priority
                    )
                    session.add(content_anno)
                
                # Add evidence annotation
                if turn_data.evidence_type:
                    evidence_anno = TurnEvidence(
                        turn_id=turn.id,
                        evidence_type=turn_data.evidence_type,
                        evidence_narrative=turn_data.evidence_narrative,
                        specificity=turn_data.specificity
                    )
                    session.add(evidence_anno)
                
                # Add stance annotation
                if turn_data.emotional_valence:
                    stance_anno = TurnStance(
                        turn_id=turn.id,
                        emotional_valence=turn_data.emotional_valence,
                        emotional_intensity=turn_data.emotional_intensity,
                        emotional_categories=turn_data.emotional_categories if turn_data.emotional_categories else None,
                        stance_target=turn_data.stance_target,
                        stance_polarity=turn_data.stance_polarity,
                        certainty_level=turn_data.certainty_level,
                        emotional_narrative=None  # Not extracted yet
                    )
                    session.add(stance_anno)
            
            # Add conversation dynamics
            conv_dynamics = ConversationDynamics(
                interview_id=interview.id,
                annotation_id=annotation.id,
                total_turns=dynamics.total_turns,
                interviewer_turns=dynamics.interviewer_turns,
                participant_turns=dynamics.participant_turns,
                average_turn_length=dynamics.average_turn_length,
                question_count=dynamics.question_count,
                topic_shifts=dynamics.topic_shifts,
                speaker_balance=dynamics.speaker_balance,
                longest_turn_speaker=dynamics.longest_turn_speaker,
                longest_turn_words=dynamics.longest_turn_words,
                conversation_flow=dynamics.conversation_flow,
                topic_introduction_pattern=dynamics.topic_introduction_pattern,
                topic_depth=dynamics.topic_depth
            )
            session.add(conv_dynamics)
            
            session.commit()
            logger.info(f"Successfully loaded {len(turns)} turns for interview 058")
            
            # Verify data was loaded
            turn_count = session.query(Turn).filter_by(interview_id=interview.id).count()
            func_count = session.query(TurnFunctionalAnnotation).count()
            content_count = session.query(TurnContentAnnotation).count()
            
            logger.info(f"Database now contains:")
            logger.info(f"  - {turn_count} turns")
            logger.info(f"  - {func_count} functional annotations")
            logger.info(f"  - {content_count} content annotations")
            
        return True
        
    except Exception as e:
        logger.error(f"Failed to load turn data: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = load_turn_data()
    sys.exit(0 if success else 1)