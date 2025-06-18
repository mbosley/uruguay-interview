"""
Repository pattern for database operations.
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date
import logging

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from src.database.models import (
    Interview, Annotation, Priority, Emotion, Theme,
    Concern, Suggestion, GeographicMention, DemographicIndicator,
    ProcessingLog, DailySummary, Turn
)
from src.pipeline.extraction.data_extractor import ExtractedData
from src.pipeline.parsing.conversation_parser import ConversationParser

logger = logging.getLogger(__name__)


class InterviewRepository:
    """Repository for interview-related database operations."""
    
    def __init__(self, db_connection=None, session=None):
        """Initialize repository with optional database connection or session."""
        self.db_connection = db_connection
        self.session = session
    
    def create_interview(self, interview_data: Dict[str, Any]) -> Interview:
        """Create a new interview record."""
        interview = Interview(**interview_data)
        self.session.add(interview)
        self.session.flush()
        return interview
    
    def get_interview_by_id(self, interview_id: str) -> Optional[Interview]:
        """Get interview by its ID."""
        return self.session.query(Interview).filter(
            Interview.interview_id == interview_id
        ).first()
    
    def get_pending_interviews(self, limit: Optional[int] = None) -> List[Interview]:
        """Get interviews pending processing."""
        query = self.session.query(Interview).filter(
            Interview.status == 'pending'
        ).order_by(Interview.created_at)
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def update_interview_status(self, interview_id: int, status: str, 
                              error_message: Optional[str] = None) -> None:
        """Update interview processing status."""
        interview = self.session.query(Interview).get(interview_id)
        if interview:
            interview.status = status
            interview.updated_at = datetime.utcnow()
            if status == 'completed':
                interview.processed_at = datetime.utcnow()
            if error_message:
                interview.error_message = error_message
            self.session.flush()
    
    def get_interviews_by_date_range(self, start_date: str, end_date: str) -> List[Interview]:
        """Get interviews within a date range."""
        return self.session.query(Interview).filter(
            and_(
                Interview.date >= start_date,
                Interview.date <= end_date
            )
        ).order_by(Interview.date, Interview.time).all()
    
    def get_interviews_by_location(self, location: str) -> List[Interview]:
        """Get interviews from a specific location."""
        return self.session.query(Interview).filter(
            Interview.location == location
        ).order_by(Interview.date).all()
    
    def get_all(self, session: Optional[Session] = None) -> List[Interview]:
        """Get all interviews with their relationships."""
        from sqlalchemy.orm import joinedload
        s = session or self.session
        return s.query(Interview).options(
            joinedload(Interview.annotations),
            joinedload(Interview.priorities),
            joinedload(Interview.themes),
            joinedload(Interview.emotions)
        ).all()
    
    def get_interview_statistics(self) -> Dict[str, Any]:
        """Get overall interview statistics."""
        total = self.session.query(func.count(Interview.id)).scalar()
        completed = self.session.query(func.count(Interview.id)).filter(
            Interview.status == 'completed'
        ).scalar()
        
        locations = self.session.query(
            Interview.location,
            func.count(Interview.id).label('count')
        ).group_by(Interview.location).all()
        
        return {
            'total_interviews': total,
            'completed_interviews': completed,
            'completion_rate': (completed / total * 100) if total > 0 else 0,
            'locations': {loc: count for loc, count in locations}
        }


class AnnotationRepository:
    """Repository for annotation-related operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_annotation(self, interview_id: int, annotation_data: Dict[str, Any]) -> Annotation:
        """Create a new annotation."""
        annotation = Annotation(interview_id=interview_id, **annotation_data)
        self.session.add(annotation)
        self.session.flush()
        return annotation
    
    def get_annotation_by_interview(self, interview_id: int, 
                                  model_provider: Optional[str] = None) -> Optional[Annotation]:
        """Get annotation for an interview."""
        query = self.session.query(Annotation).filter(
            Annotation.interview_id == interview_id
        )
        
        if model_provider:
            query = query.filter(Annotation.model_provider == model_provider)
        
        return query.first()
    
    def get_sentiment_distribution(self) -> Dict[str, int]:
        """Get distribution of sentiments across all annotations."""
        results = self.session.query(
            Annotation.overall_sentiment,
            func.count(Annotation.id).label('count')
        ).group_by(Annotation.overall_sentiment).all()
        
        return {sentiment: count for sentiment, count in results}
    
    def get_low_confidence_annotations(self, threshold: float = 0.7) -> List[Annotation]:
        """Get annotations with low confidence scores."""
        return self.session.query(Annotation).filter(
            Annotation.confidence_score < threshold
        ).order_by(Annotation.confidence_score).all()


class PriorityRepository:
    """Repository for priority-related operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def bulk_create_priorities(self, interview_id: int, priorities: List[Dict[str, Any]]) -> None:
        """Create multiple priority records."""
        for priority_data in priorities:
            priority = Priority(interview_id=interview_id, **priority_data)
            self.session.add(priority)
        self.session.flush()
    
    def get_top_priorities(self, scope: str, limit: int = 10) -> List[Tuple[str, int]]:
        """Get most common priorities by scope (national/local)."""
        results = self.session.query(
            Priority.category,
            func.count(Priority.id).label('count')
        ).filter(
            Priority.scope == scope
        ).group_by(
            Priority.category
        ).order_by(
            func.count(Priority.id).desc()
        ).limit(limit).all()
        
        return [(category, count) for category, count in results]
    
    def get_priorities_by_location(self, location: str, scope: str) -> List[Priority]:
        """Get priorities mentioned in a specific location."""
        return self.session.query(Priority).join(Interview).filter(
            and_(
                Interview.location == location,
                Priority.scope == scope
            )
        ).order_by(Priority.rank).all()
    
    def get_priority_sentiment_analysis(self) -> Dict[str, Dict[str, int]]:
        """Analyze sentiment distribution for each priority category."""
        results = self.session.query(
            Priority.category,
            Priority.sentiment,
            func.count(Priority.id).label('count')
        ).filter(
            Priority.sentiment.isnot(None)
        ).group_by(
            Priority.category,
            Priority.sentiment
        ).all()
        
        # Organize results
        analysis = {}
        for category, sentiment, count in results:
            if category not in analysis:
                analysis[category] = {}
            analysis[category][sentiment] = count
        
        return analysis


class ThemeRepository:
    """Repository for theme-related operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def bulk_create_themes(self, interview_id: int, themes: List[str]) -> None:
        """Create theme records for an interview."""
        # Count theme frequency
        theme_counts = {}
        for theme in themes:
            theme_counts[theme] = theme_counts.get(theme, 0) + 1
        
        # Create records
        for theme, frequency in theme_counts.items():
            theme_record = Theme(
                interview_id=interview_id,
                theme=theme,
                frequency=frequency
            )
            self.session.add(theme_record)
        self.session.flush()
    
    def get_theme_frequency(self, limit: int = 20) -> List[Tuple[str, int]]:
        """Get most frequent themes across all interviews."""
        results = self.session.query(
            Theme.theme,
            func.sum(Theme.frequency).label('total_frequency')
        ).group_by(
            Theme.theme
        ).order_by(
            func.sum(Theme.frequency).desc()
        ).limit(limit).all()
        
        return [(theme, int(freq)) for theme, freq in results]
    
    def get_themes_by_date_range(self, start_date: str, end_date: str) -> List[Theme]:
        """Get themes within a date range."""
        return self.session.query(Theme).join(Interview).filter(
            and_(
                Interview.date >= start_date,
                Interview.date <= end_date
            )
        ).all()


class ConversationRepository:
    """Repository for conversation turn operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def save_conversation_turns(self, interview_id: int, turns: List[Dict[str, Any]]) -> None:
        """Save conversation turns for an interview."""
        for turn_data in turns:
            turn = Turn(
                interview_id=interview_id,
                turn_number=turn_data['turn_number'],
                speaker=turn_data['speaker'],
                speaker_id=turn_data.get('speaker_id'),
                text=turn_data['text'],
                word_count=turn_data['word_count'],
                start_time=turn_data.get('start_time'),
                end_time=turn_data.get('end_time')
            )
            self.session.add(turn)
        self.session.flush()
    
    def get_conversation_turns(self, interview_id: int) -> List[Turn]:
        """Get all turns for an interview."""
        return self.session.query(Turn).filter(
            Turn.interview_id == interview_id
        ).order_by(Turn.turn_number).all()
    
    def get_speaker_statistics(self, interview_id: int) -> Dict[str, Any]:
        """Get speaker statistics for an interview."""
        turns = self.get_conversation_turns(interview_id)
        
        if not turns:
            return {}
        
        speakers = {}
        total_words = 0
        
        for turn in turns:
            speaker_key = f"{turn.speaker}_{turn.speaker_id}" if turn.speaker_id else turn.speaker
            if speaker_key not in speakers:
                speakers[speaker_key] = {
                    'speaker': turn.speaker,
                    'speaker_id': turn.speaker_id,
                    'turn_count': 0,
                    'word_count': 0
                }
            
            speakers[speaker_key]['turn_count'] += 1
            speakers[speaker_key]['word_count'] += turn.word_count
            total_words += turn.word_count
        
        return {
            'total_turns': len(turns),
            'total_words': total_words,
            'unique_speakers': len(speakers),
            'speakers': list(speakers.values()),
            'avg_words_per_turn': total_words / len(turns) if turns else 0
        }


class ExtractedDataRepository:
    """Repository for saving extracted data to database."""
    
    def __init__(self, session: Session):
        self.session = session
        self.interview_repo = InterviewRepository(session=session)
        self.annotation_repo = AnnotationRepository(session=session)
        self.priority_repo = PriorityRepository(session=session)
        self.theme_repo = ThemeRepository(session=session)
        self.conversation_repo = ConversationRepository(session=session)
    
    def save_extracted_data(self, extracted_data: ExtractedData, 
                          xml_content: Optional[str] = None,
                          raw_text: Optional[str] = None) -> None:
        """
        Save extracted data to database.
        
        Args:
            extracted_data: ExtractedData object
            xml_content: Original XML annotation content
            raw_text: Original interview text
        """
        try:
            # Get or create interview
            interview = self.interview_repo.get_interview_by_id(extracted_data.interview_id)
            if not interview:
                interview = self.interview_repo.create_interview({
                    'interview_id': extracted_data.interview_id,
                    'date': extracted_data.interview_date,
                    'time': extracted_data.interview_time,
                    'location': extracted_data.location,
                    'department': extracted_data.department,
                    'participant_count': extracted_data.participant_count,
                    'raw_text': raw_text,
                    'word_count': len(raw_text.split()) if raw_text else 0,
                    'status': 'completed'
                })
            
            # Parse and save conversation turns if raw text is available
            if raw_text:
                try:
                    parser = ConversationParser()
                    turns = parser.parse_conversation(raw_text)
                    
                    # Convert turns to dict format for saving
                    turn_dicts = []
                    for turn in turns:
                        turn_dicts.append({
                            'turn_number': turn.turn_number,
                            'speaker': turn.speaker,
                            'speaker_id': turn.speaker_id,
                            'text': turn.text,
                            'word_count': turn.word_count,
                            'start_time': None,  # Could be enhanced later
                            'end_time': None
                        })
                    
                    self.conversation_repo.save_conversation_turns(interview.id, turn_dicts)
                    logger.info(f"Saved {len(turns)} conversation turns for interview {extracted_data.interview_id}")
                    
                except Exception as e:
                    logger.warning(f"Failed to parse conversation turns for interview {extracted_data.interview_id}: {e}")
            
            # Create annotation
            annotation = self.annotation_repo.create_annotation(interview.id, {
                'model_provider': extracted_data.model_used.split('/')[0] if '/' in extracted_data.model_used else 'unknown',
                'model_name': extracted_data.model_used,
                'xml_content': xml_content,
                'dominant_emotion': extracted_data.dominant_emotion,
                'overall_sentiment': extracted_data.overall_sentiment,
                'confidence_score': extracted_data.confidence_score,
                'annotation_completeness': extracted_data.annotation_completeness,
                'has_validation_errors': extracted_data.has_validation_errors,
                'validation_notes': extracted_data.validation_notes
            })
            
            # Save priorities
            national_priorities = [
                {
                    'scope': 'national',
                    'rank': p.rank,
                    'category': p.category,
                    'subcategory': p.subcategory,
                    'description': p.description,
                    'sentiment': p.sentiment,
                    'evidence_type': p.evidence_type,
                    'confidence': p.confidence
                }
                for p in extracted_data.national_priorities
            ]
            
            local_priorities = [
                {
                    'scope': 'local',
                    'rank': p.rank,
                    'category': p.category,
                    'subcategory': p.subcategory,
                    'description': p.description,
                    'sentiment': p.sentiment,
                    'evidence_type': p.evidence_type,
                    'confidence': p.confidence
                }
                for p in extracted_data.local_priorities
            ]
            
            self.priority_repo.bulk_create_priorities(
                interview.id, 
                national_priorities + local_priorities
            )
            
            # Save themes
            if extracted_data.themes:
                self.theme_repo.bulk_create_themes(interview.id, extracted_data.themes)
            
            # Save emotions
            for emotion in extracted_data.emotions:
                emotion_record = Emotion(
                    interview_id=interview.id,
                    type=emotion.type,
                    intensity=emotion.intensity,
                    target=emotion.target,
                    context=emotion.context
                )
                self.session.add(emotion_record)
            
            # Save concerns
            for concern in extracted_data.concerns:
                concern_record = Concern(
                    interview_id=interview.id,
                    description=concern.get('description', ''),
                    category=concern.get('category'),
                    severity=concern.get('severity')
                )
                self.session.add(concern_record)
            
            # Save suggestions
            for suggestion in extracted_data.suggestions:
                suggestion_record = Suggestion(
                    interview_id=interview.id,
                    description=suggestion.get('description', ''),
                    target=suggestion.get('target'),
                    feasibility=suggestion.get('feasibility')
                )
                self.session.add(suggestion_record)
            
            # Save geographic mentions
            for location in extracted_data.geographic_mentions:
                geo_record = GeographicMention(
                    interview_id=interview.id,
                    location_name=location
                )
                self.session.add(geo_record)
            
            # Save demographic indicators
            if extracted_data.inferred_age_group or extracted_data.inferred_socioeconomic:
                demo_record = DemographicIndicator(
                    interview_id=interview.id,
                    age_group=extracted_data.inferred_age_group,
                    socioeconomic_level=extracted_data.inferred_socioeconomic
                )
                self.session.add(demo_record)
            
            # Update interview status
            self.interview_repo.update_interview_status(interview.id, 'completed')
            
            # Commit all changes
            self.session.commit()
            
            logger.info(f"Successfully saved extracted data for interview {extracted_data.interview_id}")
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to save extracted data: {e}")
            raise


class SummaryRepository:
    """Repository for summary and aggregate operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def update_daily_summary(self, summary_date: str) -> None:
        """Update or create daily summary for a specific date."""
        # Get existing summary or create new
        summary = self.session.query(DailySummary).filter(
            DailySummary.date == summary_date
        ).first()
        
        if not summary:
            summary = DailySummary(date=summary_date)
            self.session.add(summary)
        
        # Calculate statistics for the date
        interviews = self.session.query(Interview).filter(
            Interview.date == summary_date
        ).all()
        
        summary.interviews_processed = len(interviews)
        summary.total_participants = sum(i.participant_count for i in interviews)
        
        # Sentiment distribution
        sentiments = self.session.query(
            Annotation.overall_sentiment,
            func.count(Annotation.id)
        ).join(Interview).filter(
            Interview.date == summary_date
        ).group_by(Annotation.overall_sentiment).all()
        
        for sentiment, count in sentiments:
            if sentiment == 'positive':
                summary.positive_count = count
            elif sentiment == 'negative':
                summary.negative_count = count
            elif sentiment == 'neutral':
                summary.neutral_count = count
            elif sentiment == 'mixed':
                summary.mixed_count = count
        
        # Top priorities
        national_priorities = self.session.query(
            Priority.category,
            func.count(Priority.id).label('count')
        ).join(Interview).filter(
            and_(
                Interview.date == summary_date,
                Priority.scope == 'national'
            )
        ).group_by(Priority.category).order_by(
            func.count(Priority.id).desc()
        ).limit(5).all()
        
        summary.top_national_priorities = [
            {'category': cat, 'count': count} 
            for cat, count in national_priorities
        ]
        
        # Location coverage
        locations = self.session.query(
            Interview.location,
            func.count(Interview.id)
        ).filter(
            Interview.date == summary_date
        ).group_by(Interview.location).all()
        
        summary.locations_covered = [
            {'location': loc, 'count': count}
            for loc, count in locations
        ]
        
        summary.updated_at = datetime.utcnow()
        self.session.commit()
    
    def get_summary_range(self, start_date: str, end_date: str) -> List[DailySummary]:
        """Get daily summaries for a date range."""
        return self.session.query(DailySummary).filter(
            and_(
                DailySummary.date >= start_date,
                DailySummary.date <= end_date
            )
        ).order_by(DailySummary.date).all()