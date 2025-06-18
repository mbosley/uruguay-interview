"""
SQLAlchemy database models for interview analysis.
"""
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime, 
    ForeignKey, JSON, UniqueConstraint, Index
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Interview(Base):
    """Core interview record."""
    __tablename__ = 'interviews'
    
    id = Column(Integer, primary_key=True)
    interview_id = Column(String(50), unique=True, nullable=False)
    date = Column(String(10), nullable=False)
    time = Column(String(5), nullable=False)
    location = Column(String(100), nullable=False)
    department = Column(String(100))
    participant_count = Column(Integer, default=1)
    
    # File information
    file_path = Column(String(500))
    file_type = Column(String(10))
    word_count = Column(Integer)
    raw_text = Column(Text)  # Full interview text
    
    # Processing status
    status = Column(String(20), default='pending')  # pending, processing, completed, error
    processed_at = Column(DateTime)
    error_message = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    annotations = relationship("Annotation", back_populates="interview", cascade="all, delete-orphan")
    priorities = relationship("Priority", back_populates="interview", cascade="all, delete-orphan")
    emotions = relationship("Emotion", back_populates="interview", cascade="all, delete-orphan")
    themes = relationship("Theme", back_populates="interview", cascade="all, delete-orphan")
    # Turn relationship defined with string to avoid circular import
    # The Turn model is defined in models_turns.py
    
    # Indexes
    __table_args__ = (
        Index('idx_interview_date', 'date'),
        Index('idx_interview_location', 'location'),
        Index('idx_interview_status', 'status'),
    )


class Annotation(Base):
    """AI-generated annotation for an interview."""
    __tablename__ = 'annotations'
    
    id = Column(Integer, primary_key=True)
    interview_id = Column(Integer, ForeignKey('interviews.id'), nullable=False)
    
    # Model information
    model_provider = Column(String(50), nullable=False)
    model_name = Column(String(100), nullable=False)
    temperature = Column(Float)
    
    # Annotation content
    xml_content = Column(Text)  # Full XML annotation
    
    # Analysis results
    dominant_emotion = Column(String(50))
    overall_sentiment = Column(String(20))  # positive, negative, neutral, mixed
    confidence_score = Column(Float)
    
    # Quality metrics
    annotation_completeness = Column(Float)
    has_validation_errors = Column(Boolean, default=False)
    validation_notes = Column(JSON)
    
    # Processing metadata
    processing_time = Column(Float)  # seconds
    token_count = Column(Integer)
    cost_estimate = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    interview = relationship("Interview", back_populates="annotations")
    
    # Ensure one annotation per interview per model
    __table_args__ = (
        UniqueConstraint('interview_id', 'model_provider', 'model_name', name='uq_annotation_model'),
        Index('idx_annotation_sentiment', 'overall_sentiment'),
        Index('idx_annotation_confidence', 'confidence_score'),
    )


class Priority(Base):
    """Citizen priorities extracted from interviews."""
    __tablename__ = 'priorities'
    
    id = Column(Integer, primary_key=True)
    interview_id = Column(Integer, ForeignKey('interviews.id'), nullable=False)
    
    # Priority details
    scope = Column(String(20), nullable=False)  # national, local
    rank = Column(Integer, nullable=False)
    category = Column(String(50), nullable=False)
    subcategory = Column(String(50))
    description = Column(Text, nullable=False)
    
    # Additional attributes
    sentiment = Column(String(20))
    evidence_type = Column(String(50))
    confidence = Column(Float, default=1.0)
    
    # Relationships
    interview = relationship("Interview", back_populates="priorities")
    
    # Indexes
    __table_args__ = (
        Index('idx_priority_scope_rank', 'scope', 'rank'),
        Index('idx_priority_category', 'category'),
        Index('idx_priority_sentiment', 'sentiment'),
    )


class Emotion(Base):
    """Emotional expressions in interviews."""
    __tablename__ = 'emotions'
    
    id = Column(Integer, primary_key=True)
    interview_id = Column(Integer, ForeignKey('interviews.id'), nullable=False)
    
    # Emotion details
    type = Column(String(50), nullable=False)
    intensity = Column(String(20), nullable=False)  # low, medium, high
    target = Column(String(100))
    context = Column(Text)
    
    # Position in interview
    turn_number = Column(Integer)
    
    # Relationships
    interview = relationship("Interview", back_populates="emotions")
    
    # Indexes
    __table_args__ = (
        Index('idx_emotion_type', 'type'),
        Index('idx_emotion_intensity', 'intensity'),
    )


class Theme(Base):
    """Themes and topics discussed in interviews."""
    __tablename__ = 'themes'
    
    id = Column(Integer, primary_key=True)
    interview_id = Column(Integer, ForeignKey('interviews.id'), nullable=False)
    
    # Theme details
    theme = Column(String(100), nullable=False)
    category = Column(String(50))
    frequency = Column(Integer, default=1)
    
    # Relationships
    interview = relationship("Interview", back_populates="themes")
    
    # Indexes
    __table_args__ = (
        Index('idx_theme_name', 'theme'),
        Index('idx_theme_category', 'category'),
    )


class Concern(Base):
    """Specific concerns raised by citizens."""
    __tablename__ = 'concerns'
    
    id = Column(Integer, primary_key=True)
    interview_id = Column(Integer, ForeignKey('interviews.id'), nullable=False)
    
    # Concern details
    description = Column(Text, nullable=False)
    category = Column(String(50))
    severity = Column(String(20))  # low, medium, high, critical
    
    # Geographic scope
    geographic_scope = Column(String(50))  # local, regional, national
    specific_location = Column(String(100))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_concern_category', 'category'),
        Index('idx_concern_severity', 'severity'),
    )


class Suggestion(Base):
    """Policy suggestions from citizens."""
    __tablename__ = 'suggestions'
    
    id = Column(Integer, primary_key=True)
    interview_id = Column(Integer, ForeignKey('interviews.id'), nullable=False)
    
    # Suggestion details
    description = Column(Text, nullable=False)
    target = Column(String(100))  # government level or entity
    category = Column(String(50))
    feasibility = Column(String(20))  # low, medium, high, unknown
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_suggestion_category', 'category'),
        Index('idx_suggestion_target', 'target'),
    )


class GeographicMention(Base):
    """Geographic locations mentioned in interviews."""
    __tablename__ = 'geographic_mentions'
    
    id = Column(Integer, primary_key=True)
    interview_id = Column(Integer, ForeignKey('interviews.id'), nullable=False)
    
    # Location details
    location_name = Column(String(100), nullable=False)
    location_type = Column(String(50))  # city, neighborhood, department, landmark
    context = Column(Text)
    sentiment = Column(String(20))  # positive, negative, neutral
    
    # Coordinates (if geocoded)
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Indexes
    __table_args__ = (
        Index('idx_geo_location', 'location_name'),
        Index('idx_geo_type', 'location_type'),
    )


class DemographicIndicator(Base):
    """Inferred demographic information."""
    __tablename__ = 'demographic_indicators'
    
    id = Column(Integer, primary_key=True)
    interview_id = Column(Integer, ForeignKey('interviews.id'), nullable=False)
    
    # Inferred demographics
    age_group = Column(String(20))  # youth, adult, senior
    socioeconomic_level = Column(String(20))  # low, middle, high
    education_level = Column(String(50))
    occupation_category = Column(String(50))
    
    # Confidence scores
    age_confidence = Column(Float)
    socioeconomic_confidence = Column(Float)
    
    # Indexes
    __table_args__ = (
        Index('idx_demo_age', 'age_group'),
        Index('idx_demo_socio', 'socioeconomic_level'),
    )


class ProcessingLog(Base):
    """Log of all processing activities."""
    __tablename__ = 'processing_logs'
    
    id = Column(Integer, primary_key=True)
    interview_id = Column(Integer, ForeignKey('interviews.id'))
    
    # Activity details
    activity_type = Column(String(50), nullable=False)  # ingestion, annotation, extraction, export
    status = Column(String(20), nullable=False)  # started, completed, failed
    
    # Metadata
    details = Column(JSON)
    error_message = Column(Text)
    duration = Column(Float)  # seconds
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Indexes
    __table_args__ = (
        Index('idx_log_activity', 'activity_type'),
        Index('idx_log_status', 'status'),
        Index('idx_log_started', 'started_at'),
    )


# Summary/Aggregate tables for dashboard performance

class DailySummary(Base):
    """Daily aggregated statistics."""
    __tablename__ = 'daily_summaries'
    
    id = Column(Integer, primary_key=True)
    date = Column(String(10), unique=True, nullable=False)
    
    # Interview counts
    interviews_processed = Column(Integer, default=0)
    total_participants = Column(Integer, default=0)
    
    # Sentiment distribution
    positive_count = Column(Integer, default=0)
    negative_count = Column(Integer, default=0)
    neutral_count = Column(Integer, default=0)
    mixed_count = Column(Integer, default=0)
    
    # Top priorities (JSON)
    top_national_priorities = Column(JSON)
    top_local_priorities = Column(JSON)
    
    # Geographic distribution
    locations_covered = Column(JSON)
    
    # Processing metrics
    avg_processing_time = Column(Float)
    total_cost = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_summary_date', 'date'),
    )


# ============================================================================
# TURN-LEVEL MODELS
# Models for storing multi-turn conversation data
# ============================================================================

class Turn(Base):
    """Individual conversation turn within an interview."""
    __tablename__ = 'turns'
    
    id = Column(Integer, primary_key=True)
    interview_id = Column(Integer, ForeignKey('interviews.id'), nullable=False)
    annotation_id = Column(Integer, ForeignKey('annotations.id'))
    
    # Turn metadata
    turn_number = Column(Integer, nullable=False)  # Sequential order in conversation
    speaker = Column(String(50), nullable=False)  # participant, interviewer, moderator
    speaker_id = Column(String(50))  # If multiple participants
    
    # Content
    text = Column(Text, nullable=False)  # Actual spoken text
    word_count = Column(Integer)
    duration_seconds = Column(Float)  # If timing data available
    
    # Timestamps
    start_time = Column(String(10))  # Time offset from interview start
    end_time = Column(String(10))
    
    # Relationships
    interview = relationship("Interview", backref="turns")
    annotation = relationship("Annotation", backref="turns")
    
    # Child relationships
    functional_annotations = relationship("TurnFunctionalAnnotation", back_populates="turn", cascade="all, delete-orphan")
    content_annotations = relationship("TurnContentAnnotation", back_populates="turn", cascade="all, delete-orphan")
    evidence_annotations = relationship("TurnEvidence", back_populates="turn", cascade="all, delete-orphan")
    stance_annotations = relationship("TurnStance", back_populates="turn", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_turn_interview', 'interview_id'),
        Index('idx_turn_number', 'interview_id', 'turn_number'),
        Index('idx_turn_speaker', 'speaker'),
    )


class TurnFunctionalAnnotation(Base):
    """Functional analysis of a turn (what the speaker is doing)."""
    __tablename__ = 'turn_functional_annotations'
    
    id = Column(Integer, primary_key=True)
    turn_id = Column(Integer, ForeignKey('turns.id'), nullable=False)
    
    # Primary function
    primary_function = Column(String(50), nullable=False)
    # Options: greeting, problem_identification, solution_proposal, agreement, 
    # disagreement, question, clarification, narrative, evaluation, closing
    
    # Secondary functions (if multiple functions in one turn)
    secondary_functions = Column(JSON)  # List of additional functions
    
    # Uncertainty tracking
    coding_confidence = Column(Float, default=1.0)
    ambiguous_function = Column(Boolean, default=False)
    uncertainty_notes = Column(Text)
    
    # Relationships
    turn = relationship("Turn", back_populates="functional_annotations")
    
    # Indexes
    __table_args__ = (
        Index('idx_turn_func_primary', 'primary_function'),
    )


class TurnContentAnnotation(Base):
    """Content analysis of a turn (what the speaker is talking about)."""
    __tablename__ = 'turn_content_annotations'
    
    id = Column(Integer, primary_key=True)
    turn_id = Column(Integer, ForeignKey('turns.id'), nullable=False)
    
    # Topics discussed
    topics = Column(JSON, nullable=False)  # List of topic strings
    topic_narrative = Column(Text)  # Explanation of topic coding
    
    # Geographic scope
    geographic_scope = Column(JSON)  # List: [local, regional, national, international]
    geographic_mentions = Column(JSON)  # Specific places mentioned
    
    # Temporal references
    temporal_reference = Column(String(20))  # past, present, future, timeless
    temporal_specifics = Column(JSON)  # Specific time references
    
    # Actors mentioned
    actors_mentioned = Column(JSON)  # Government, citizens, organizations, etc.
    actor_relationships = Column(JSON)  # How actors relate to each other
    
    # Priority indication
    indicates_priority = Column(Boolean, default=False)
    priority_rank_mentioned = Column(Integer)
    
    # Relationships
    turn = relationship("Turn", back_populates="content_annotations")


class TurnEvidence(Base):
    """Evidence and argumentation tracking in turns."""
    __tablename__ = 'turn_evidence'
    
    id = Column(Integer, primary_key=True)
    turn_id = Column(Integer, ForeignKey('turns.id'), nullable=False)
    
    # Evidence type
    evidence_type = Column(String(50), nullable=False)
    # Options: personal_experience, community_observation, statistics, 
    # expert_opinion, media_report, government_data, hearsay, none
    
    evidence_narrative = Column(Text)  # Description of evidence
    
    # Evidence quality
    specificity = Column(String(20))  # very_specific, somewhat_specific, vague, none
    verifiability = Column(String(20))  # verifiable, possibly_verifiable, unverifiable
    
    # Argumentation
    argument_type = Column(String(50))  # causal, comparative, evaluative, descriptive
    logical_connectors = Column(JSON)  # Words like "because", "therefore", etc.
    
    # Relationships
    turn = relationship("Turn", back_populates="evidence_annotations")
    
    # Indexes
    __table_args__ = (
        Index('idx_turn_evidence_type', 'evidence_type'),
    )


class TurnStance(Base):
    """Emotional and evaluative stance in turns."""
    __tablename__ = 'turn_stance'
    
    id = Column(Integer, primary_key=True)
    turn_id = Column(Integer, ForeignKey('turns.id'), nullable=False)
    
    # Emotional content
    emotional_valence = Column(String(20))  # positive, negative, neutral, mixed
    emotional_intensity = Column(Float)  # 0.0 to 1.0
    emotional_categories = Column(JSON)  # List: anger, fear, sadness, joy, etc.
    
    # Stance toward topics
    stance_target = Column(String(100))  # What they're taking a stance toward
    stance_polarity = Column(String(20))  # supportive, critical, ambivalent, neutral
    
    # Certainty
    certainty_level = Column(String(20))  # certain, probable, possible, uncertain
    hedging_markers = Column(JSON)  # Words indicating uncertainty
    
    # Narrative summary
    emotional_narrative = Column(Text)
    
    # Relationships
    turn = relationship("Turn", back_populates="stance_annotations")


class ConversationDynamics(Base):
    """Analysis of conversation patterns and dynamics."""
    __tablename__ = 'conversation_dynamics'
    
    id = Column(Integer, primary_key=True)
    interview_id = Column(Integer, ForeignKey('interviews.id'), nullable=False)
    annotation_id = Column(Integer, ForeignKey('annotations.id'))
    
    # Turn-taking patterns
    total_turns = Column(Integer)
    interviewer_turns = Column(Integer)
    participant_turns = Column(Integer)
    average_turn_length = Column(Float)  # words
    
    # Interaction patterns
    question_count = Column(Integer)
    response_rate = Column(Float)  # % of questions answered
    topic_shifts = Column(Integer)
    
    # Dominance patterns
    speaker_balance = Column(Float)  # 0.0 = interviewer dominates, 1.0 = participant
    longest_turn_speaker = Column(String(50))
    longest_turn_words = Column(Integer)
    
    # Flow characteristics
    conversation_flow = Column(String(20))  # smooth, choppy, mixed
    interruption_count = Column(Integer)
    silence_count = Column(Integer)
    
    # Topic progression
    topic_introduction_pattern = Column(String(50))  # interviewer_led, participant_led, collaborative
    topic_depth = Column(String(20))  # surface, moderate, deep
    
    # Relationships
    interview = relationship("Interview")
    annotation = relationship("Annotation")