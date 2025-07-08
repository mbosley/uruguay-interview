"""
Enhanced SQLAlchemy database models for comprehensive JSON annotation data.
Captures the full analytical richness of our multi-pass annotation system.
"""
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime, 
    ForeignKey, JSON, UniqueConstraint, Index, DECIMAL
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


# ============================================================================
# CORE INTERVIEW MODELS (Enhanced)
# ============================================================================

class Interview(Base):
    """Core interview record with enhanced metadata."""
    __tablename__ = 'interviews'
    
    id = Column(Integer, primary_key=True)
    interview_id = Column(String(50), unique=True, nullable=False)
    date = Column(String(10), nullable=False)
    time = Column(String(5), nullable=False)
    location = Column(String(100), nullable=False)
    department = Column(String(100))
    municipality = Column(String(100))
    locality_size = Column(String(20))  # rural, small_town, medium_city, large_city
    
    # Interview context
    duration_minutes = Column(Integer)
    interviewer_ids = Column(JSON)  # List of interviewer names
    interview_context = Column(Text)
    participant_count = Column(Integer, default=1)
    
    # File information
    file_path = Column(String(500))
    file_type = Column(String(10))
    word_count = Column(Integer)
    raw_text = Column(Text)
    
    # Processing status
    status = Column(String(20), default='pending')
    processed_at = Column(DateTime)
    error_message = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Enhanced relationships
    annotations = relationship("Annotation", back_populates="interview", cascade="all, delete-orphan")
    participant_profile = relationship("ParticipantProfile", back_populates="interview", uselist=False, cascade="all, delete-orphan")
    narrative_features = relationship("NarrativeFeatures", back_populates="interview", uselist=False, cascade="all, delete-orphan")
    key_narratives = relationship("KeyNarratives", back_populates="interview", uselist=False, cascade="all, delete-orphan")
    interview_dynamics = relationship("InterviewDynamics", back_populates="interview", uselist=False, cascade="all, delete-orphan")
    analytical_synthesis = relationship("AnalyticalSynthesis", back_populates="interview", uselist=False, cascade="all, delete-orphan")
    priorities = relationship("Priority", back_populates="interview", cascade="all, delete-orphan")
    turns = relationship("Turn", back_populates="interview", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_interview_date', 'date'),
        Index('idx_interview_location', 'location'),
        Index('idx_interview_department', 'department'),
        Index('idx_interview_status', 'status'),
    )


class Annotation(Base):
    """Enhanced AI annotation with comprehensive metadata."""
    __tablename__ = 'annotations'
    
    id = Column(Integer, primary_key=True)
    interview_id = Column(Integer, ForeignKey('interviews.id'), nullable=False)
    
    # Model information
    model_provider = Column(String(50), nullable=False)
    model_name = Column(String(100), nullable=False)
    temperature = Column(Float)
    annotation_approach = Column(String(50))  # multipass_comprehensive, etc.
    
    # Core annotation metadata
    overall_confidence = Column(Float)
    uncertainty_flags = Column(JSON)  # List of uncertainty types
    uncertainty_narrative = Column(Text)
    
    # Quality assessment
    annotation_completeness = Column(Float)
    turn_coverage_percentage = Column(Float)
    analyzed_turns = Column(Integer)
    expected_turns = Column(Integer)
    all_turns_analyzed = Column(Boolean)
    
    # Processing metadata
    total_api_calls = Column(Integer)
    api_call_breakdown = Column(JSON)
    processing_time = Column(Float)  # seconds
    total_cost = Column(DECIMAL(10, 6))
    
    # Full annotation storage
    json_content = Column(JSON)  # Complete annotation JSON
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    interview = relationship("Interview", back_populates="annotations")
    quality_assessment = relationship("QualityAssessment", back_populates="annotation", uselist=False, cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('interview_id', 'model_provider', 'model_name', name='uq_annotation_model'),
        Index('idx_annotation_confidence', 'overall_confidence'),
        Index('idx_annotation_approach', 'annotation_approach'),
    )


# ============================================================================
# PARTICIPANT ANALYSIS MODELS
# ============================================================================

class ParticipantProfile(Base):
    """Comprehensive participant demographic and background analysis."""
    __tablename__ = 'participant_profiles'
    
    id = Column(Integer, primary_key=True)
    interview_id = Column(Integer, ForeignKey('interviews.id'), nullable=False)
    
    # Demographics
    age_range = Column(String(20))  # 18-29, 30-49, 50-64, 65+
    gender = Column(String(20))  # male, female, non_binary, prefer_not_to_say
    occupation_sector = Column(String(50))
    
    # Social context
    organizational_affiliation = Column(Text)
    self_described_political_stance = Column(Text)
    
    # Analysis metadata
    profile_confidence = Column(Float)
    profile_notes = Column(Text)
    
    # Relationships
    interview = relationship("Interview", back_populates="participant_profile")
    
    # Indexes
    __table_args__ = (
        Index('idx_profile_age', 'age_range'),
        Index('idx_profile_gender', 'gender'),
        Index('idx_profile_occupation', 'occupation_sector'),
    )


# ============================================================================
# NARRATIVE ANALYSIS MODELS
# ============================================================================

class NarrativeFeatures(Base):
    """Comprehensive narrative frame and temporal analysis."""
    __tablename__ = 'narrative_features'
    
    id = Column(Integer, primary_key=True)
    interview_id = Column(Integer, ForeignKey('interviews.id'), nullable=False)
    
    # Narrative framing
    dominant_frame = Column(String(20))  # decline, progress, stagnation, mixed
    frame_narrative = Column(Text)
    
    # Temporal orientation
    temporal_orientation = Column(String(20))  # past_focused, present_focused, future_focused, mixed
    temporal_narrative = Column(Text)
    
    # Agency attribution (0.0 to 1.0 scales)
    government_responsibility = Column(Float)
    individual_responsibility = Column(Float)
    structural_factors = Column(Float)
    agency_narrative = Column(Text)
    
    # Solution orientation
    solution_orientation = Column(String(20))  # highly_specific, moderately_specific, vague, none
    solution_narrative = Column(Text)
    
    # Cultural patterns
    cultural_patterns_identified = Column(JSON)  # List of cultural patterns
    
    # Analysis confidence
    narrative_confidence = Column(Float)
    
    # Relationships
    interview = relationship("Interview", back_populates="narrative_features")
    
    # Indexes
    __table_args__ = (
        Index('idx_narrative_frame', 'dominant_frame'),
        Index('idx_narrative_temporal', 'temporal_orientation'),
        Index('idx_narrative_solution', 'solution_orientation'),
    )


class KeyNarratives(Base):
    """Key narrative themes and rhetorical analysis."""
    __tablename__ = 'key_narratives'
    
    id = Column(Integer, primary_key=True)
    interview_id = Column(Integer, ForeignKey('interviews.id'), nullable=False)
    
    # Core narratives
    identity_narrative = Column(Text)
    problem_narrative = Column(Text)
    hope_narrative = Column(Text)
    
    # Notable quotes and rhetoric
    memorable_quotes = Column(JSON)  # List of striking quotes
    rhetorical_strategies = Column(JSON)  # List of rhetorical devices
    
    # Analysis confidence
    narrative_confidence = Column(Float)
    
    # Relationships
    interview = relationship("Interview", back_populates="key_narratives")


class InterviewDynamics(Base):
    """Interview interaction quality and dynamics."""
    __tablename__ = 'interview_dynamics'
    
    id = Column(Integer, primary_key=True)
    interview_id = Column(Integer, ForeignKey('interviews.id'), nullable=False)
    
    # Interaction quality
    rapport = Column(String(20))  # excellent, good, adequate, poor
    rapport_narrative = Column(Text)
    
    participant_engagement = Column(String(20))  # highly_engaged, engaged, moderately_engaged, disengaged
    engagement_narrative = Column(Text)
    
    coherence = Column(String(20))  # highly_coherent, coherent, somewhat_coherent, incoherent
    coherence_narrative = Column(Text)
    
    # External factors
    interviewer_effects = Column(Text)
    
    # Analysis confidence
    dynamics_confidence = Column(Float)
    
    # Relationships
    interview = relationship("Interview", back_populates="interview_dynamics")
    
    # Indexes
    __table_args__ = (
        Index('idx_dynamics_rapport', 'rapport'),
        Index('idx_dynamics_engagement', 'participant_engagement'),
    )


class AnalyticalSynthesis(Base):
    """High-level analytical synthesis and cultural context."""
    __tablename__ = 'analytical_synthesis'
    
    id = Column(Integer, primary_key=True)
    interview_id = Column(Integer, ForeignKey('interviews.id'), nullable=False)
    
    # Analytical observations
    tensions_contradictions = Column(Text)
    silences_omissions = Column(Text)
    cultural_context_notes = Column(Text)
    connections_to_broader_themes = Column(Text)
    
    # Analysis confidence
    analytical_confidence = Column(Float)
    
    # Relationships
    interview = relationship("Interview", back_populates="analytical_synthesis")


# ============================================================================
# PRIORITY ANALYSIS MODELS (Enhanced)
# ============================================================================

class Priority(Base):
    """Enhanced priority analysis with narrative context."""
    __tablename__ = 'priorities'
    
    id = Column(Integer, primary_key=True)
    interview_id = Column(Integer, ForeignKey('interviews.id'), nullable=False)
    
    # Priority identification
    scope = Column(String(20), nullable=False)  # national, local
    rank = Column(Integer, nullable=False)
    theme = Column(String(100), nullable=False)
    specific_issues = Column(JSON)  # List of specific issues
    
    # Narrative analysis
    narrative_elaboration = Column(Text)
    emotional_intensity = Column(Float)  # 0.0 to 1.0
    supporting_quotes = Column(JSON)  # List of participant quotes
    
    # Analysis metadata
    confidence = Column(Float)
    reasoning = Column(Text)  # Why this was coded as this priority
    
    # Relationships
    interview = relationship("Interview", back_populates="priorities")
    
    # Indexes
    __table_args__ = (
        Index('idx_priority_scope_rank', 'scope', 'rank'),
        Index('idx_priority_theme', 'theme'),
        Index('idx_priority_confidence', 'confidence'),
    )


# ============================================================================
# TURN-LEVEL ANALYSIS MODELS (Enhanced)
# ============================================================================

class Turn(Base):
    """Enhanced conversation turn with comprehensive analysis."""
    __tablename__ = 'turns'
    
    id = Column(Integer, primary_key=True)
    interview_id = Column(Integer, ForeignKey('interviews.id'), nullable=False)
    annotation_id = Column(Integer, ForeignKey('annotations.id'))
    
    # Turn metadata
    turn_id = Column(Integer, nullable=False)  # Turn number in conversation
    speaker = Column(String(50), nullable=False)  # participant, interviewer
    text = Column(Text, nullable=False)
    word_count = Column(Integer)
    significance = Column(String(20))  # high, medium, low
    
    # Turn analysis
    turn_significance = Column(Text)  # Why this turn matters
    
    # Relationships
    interview = relationship("Interview", back_populates="turns")
    annotation = relationship("Annotation")
    
    # Detailed analysis components
    functional_analysis = relationship("TurnFunctionalAnalysis", back_populates="turn", uselist=False, cascade="all, delete-orphan")
    content_analysis = relationship("TurnContentAnalysis", back_populates="turn", uselist=False, cascade="all, delete-orphan")
    evidence_analysis = relationship("TurnEvidenceAnalysis", back_populates="turn", uselist=False, cascade="all, delete-orphan")
    emotional_analysis = relationship("TurnEmotionalAnalysis", back_populates="turn", uselist=False, cascade="all, delete-orphan")
    uncertainty_tracking = relationship("TurnUncertaintyTracking", back_populates="turn", uselist=False, cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_turn_interview_id', 'interview_id', 'turn_id'),
        Index('idx_turn_speaker', 'speaker'),
        Index('idx_turn_significance', 'significance'),
    )


class TurnFunctionalAnalysis(Base):
    """Comprehensive functional analysis of conversation turns."""
    __tablename__ = 'turn_functional_analysis'
    
    id = Column(Integer, primary_key=True)
    turn_id = Column(Integer, ForeignKey('turns.id'), nullable=False)
    
    # Analysis reasoning
    reasoning = Column(Text)  # Chain-of-thought reasoning
    
    # Functional classification
    primary_function = Column(String(50), nullable=False)
    secondary_functions = Column(JSON)  # List of secondary functions
    function_confidence = Column(Float)
    
    # Relationships
    turn = relationship("Turn", back_populates="functional_analysis")
    
    # Indexes
    __table_args__ = (
        Index('idx_func_primary', 'primary_function'),
    )


class TurnContentAnalysis(Base):
    """Comprehensive content analysis of conversation turns."""
    __tablename__ = 'turn_content_analysis'
    
    id = Column(Integer, primary_key=True)
    turn_id = Column(Integer, ForeignKey('turns.id'), nullable=False)
    
    # Analysis reasoning
    reasoning = Column(Text)
    
    # Content classification
    topics = Column(JSON)  # List of topics
    geographic_scope = Column(JSON)  # List of geographic scopes
    temporal_reference = Column(String(20))  # past, present, future, comparison
    topic_narrative = Column(Text)
    
    # Analysis confidence
    content_confidence = Column(Float)
    
    # Relationships
    turn = relationship("Turn", back_populates="content_analysis")


class TurnEvidenceAnalysis(Base):
    """Evidence and argumentation analysis for turns."""
    __tablename__ = 'turn_evidence_analysis'
    
    id = Column(Integer, primary_key=True)
    turn_id = Column(Integer, ForeignKey('turns.id'), nullable=False)
    
    # Analysis reasoning
    reasoning = Column(Text)
    
    # Evidence classification
    evidence_type = Column(String(50))
    evidence_narrative = Column(Text)
    specificity = Column(String(20))  # very_specific, somewhat_specific, general, vague
    
    # Analysis confidence
    evidence_confidence = Column(Float)
    
    # Relationships
    turn = relationship("Turn", back_populates="evidence_analysis")
    
    # Indexes
    __table_args__ = (
        Index('idx_evidence_type', 'evidence_type'),
    )


class TurnEmotionalAnalysis(Base):
    """Comprehensive emotional analysis of turns."""
    __tablename__ = 'turn_emotional_analysis'
    
    id = Column(Integer, primary_key=True)
    turn_id = Column(Integer, ForeignKey('turns.id'), nullable=False)
    
    # Analysis reasoning
    reasoning = Column(Text)
    
    # Emotional classification
    emotional_valence = Column(String(20))  # positive, negative, neutral, mixed
    emotional_intensity = Column(Float)  # 0.0 to 1.0
    specific_emotions = Column(JSON)  # List of specific emotions
    emotional_narrative = Column(Text)
    
    # Certainty analysis
    certainty = Column(String(20))  # very_certain, somewhat_certain, uncertain, ambivalent
    rhetorical_features = Column(Text)
    
    # Relationships
    turn = relationship("Turn", back_populates="emotional_analysis")
    
    # Indexes
    __table_args__ = (
        Index('idx_emotional_valence', 'emotional_valence'),
        Index('idx_emotional_intensity', 'emotional_intensity'),
    )


class TurnUncertaintyTracking(Base):
    """Uncertainty tracking and alternative interpretations for turns."""
    __tablename__ = 'turn_uncertainty_tracking'
    
    id = Column(Integer, primary_key=True)
    turn_id = Column(Integer, ForeignKey('turns.id'), nullable=False)
    
    # Uncertainty metrics
    coding_confidence = Column(Float)
    ambiguous_aspects = Column(JSON)  # List of ambiguous aspects
    edge_case_flag = Column(Boolean, default=False)
    alternative_interpretations = Column(JSON)  # List of alternative readings
    resolution_strategy = Column(String(50))
    annotator_notes = Column(Text)
    
    # Relationships
    turn = relationship("Turn", back_populates="uncertainty_tracking")


# ============================================================================
# QUALITY ASSURANCE MODELS
# ============================================================================

class QualityAssessment(Base):
    """Comprehensive quality assessment for annotations."""
    __tablename__ = 'quality_assessments'
    
    id = Column(Integer, primary_key=True)
    annotation_id = Column(Integer, ForeignKey('annotations.id'), nullable=False)
    
    # Quality metrics
    overall_quality_score = Column(Float)
    quality_issues = Column(JSON)  # List of quality concerns
    
    # Coverage metrics
    turn_coverage_complete = Column(Boolean)
    priority_analysis_complete = Column(Boolean)
    narrative_analysis_complete = Column(Boolean)
    
    # Validation timestamp
    validated_at = Column(DateTime, default=datetime.utcnow)
    validator_version = Column(String(50))
    
    # Relationships
    annotation = relationship("Annotation", back_populates="quality_assessment")


# ============================================================================
# PROCESSING ANALYTICS MODELS
# ============================================================================

class ProcessingAnalytics(Base):
    """Detailed processing analytics and cost tracking."""
    __tablename__ = 'processing_analytics'
    
    id = Column(Integer, primary_key=True)
    interview_id = Column(Integer, ForeignKey('interviews.id'), nullable=False)
    
    # Processing configuration
    model_name = Column(String(100))
    annotation_approach = Column(String(50))
    max_workers = Column(Integer)
    timeout_used = Column(Integer)
    
    # Performance metrics
    total_api_calls = Column(Integer)
    processing_time_seconds = Column(Float)
    total_cost = Column(DECIMAL(10, 6))
    cost_per_api_call = Column(DECIMAL(10, 6))
    
    # Quality outcomes
    turn_coverage_percentage = Column(Float)
    overall_confidence = Column(Float)
    retry_count = Column(Integer, default=0)
    
    # Detailed breakdown
    api_call_breakdown = Column(JSON)
    
    # Timestamps
    processed_at = Column(DateTime, default=datetime.utcnow)
    pipeline_version = Column(String(50))
    
    # Indexes
    __table_args__ = (
        Index('idx_processing_model', 'model_name'),
        Index('idx_processing_cost', 'total_cost'),
        Index('idx_processing_time', 'processing_time_seconds'),
    )


# ============================================================================
# RESEARCH ANALYTICS VIEWS
# ============================================================================

# These would be implemented as SQL views for efficient research queries

class ResearchView:
    """Base class for research-oriented database views."""
    pass

# Example views to be created:
# - participant_narrative_summary
# - priority_theme_analysis
# - cultural_pattern_tracking
# - processing_cost_analysis
# - quality_trends_analysis