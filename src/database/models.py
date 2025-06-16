"""
SQLAlchemy database models for interview analysis.
"""
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime, 
    ForeignKey, JSON, UniqueConstraint, Index
)
from sqlalchemy.ext.declarative import declarative_base
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