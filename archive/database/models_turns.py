"""
Database models for multi-turn conversation storage.
Extension to the base models for handling turn-level data.
"""
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from src.database.models import Base


class Turn(Base):
    """Individual conversation turn within an interview."""
    __tablename__ = 'turns'
    
    id = Column(Integer, primary_key=True)
    interview_id = Column(Integer, ForeignKey('interviews.id'), nullable=False)
    annotation_id = Column(Integer, ForeignKey('annotations.id'), nullable=False)
    
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
    interview = relationship("Interview", back_populates="turns")
    annotation = relationship("Annotation", back_populates="turns")
    
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
    annotation_id = Column(Integer, ForeignKey('annotations.id'), nullable=False)
    
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


# Update the original models to include turn relationships
# This would be added to the existing models.py file
"""
# Add to Interview model:
turns = relationship("Turn", back_populates="interview", cascade="all, delete-orphan")

# Add to Annotation model:  
turns = relationship("Turn", back_populates="annotation", cascade="all, delete-orphan")
"""