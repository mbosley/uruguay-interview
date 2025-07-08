"""
Database models for Moral Foundations Theory (MFT) analysis storage and Citation System.
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class TurnCitationMetadata(Base):
    """Citation metadata for individual conversation turns."""
    __tablename__ = 'turn_citation_metadata'
    
    id = Column(Integer, primary_key=True)
    turn_id = Column(Integer, ForeignKey('turns.id'), nullable=False)
    
    # Semantic tags as JSON array
    semantic_tags = Column(JSON, nullable=False, default=list)
    
    # Key phrases as JSON array of objects
    key_phrases = Column(JSON, nullable=False, default=list)
    
    # Quotable segments with positions
    quotable_segments = Column(JSON, nullable=False, default=list)
    
    # Context metrics
    context_dependency = Column(Float, nullable=False, default=0.5)
    standalone_clarity = Column(Float, nullable=False, default=0.5)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    turn = relationship("Turn", back_populates="citation_metadata")


class InterviewInsightCitation(Base):
    """Citations linking interview insights to supporting turns."""
    __tablename__ = 'interview_insight_citations'
    
    id = Column(Integer, primary_key=True)
    interview_id = Column(String, ForeignKey('interviews.id'), nullable=False)
    insight_type = Column(String, nullable=False)  # priority, narrative, etc.
    insight_id = Column(String, nullable=False)  # Unique ID for the insight
    
    # Citation data as JSON
    citation_data = Column(JSON, nullable=False)
    
    # Quick access fields
    primary_turn_ids = Column(JSON)  # Array of primary evidence turns
    supporting_turn_ids = Column(JSON)  # Array of supporting turns
    confidence_score = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    interview = relationship("Interview", back_populates="insight_citations")


class TurnMoralFoundations(Base):
    """Stores MFT analysis for individual conversation turns."""
    __tablename__ = 'turn_moral_foundations'
    
    id = Column(Integer, primary_key=True)
    turn_id = Column(Integer, ForeignKey('turns.id'), nullable=False)
    
    # MFT reasoning
    reasoning = Column(Text)
    
    # Foundation scores (0.0-1.0)
    care_harm = Column(Float, default=0.0)
    fairness_cheating = Column(Float, default=0.0)
    loyalty_betrayal = Column(Float, default=0.0)
    authority_subversion = Column(Float, default=0.0)
    sanctity_degradation = Column(Float, default=0.0)
    liberty_oppression = Column(Float, default=0.0)
    
    # Dominant foundation
    dominant_foundation = Column(String(50))
    foundations_narrative = Column(Text)
    mft_confidence = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    turn = relationship("Turn", back_populates="moral_foundations")


class InterviewMoralFoundations(Base):
    """Aggregated MFT profile for entire interviews."""
    __tablename__ = 'interview_moral_foundations'
    
    id = Column(Integer, primary_key=True)
    interview_id = Column(String(20), ForeignKey('interviews.interview_id'), nullable=False)
    
    # Average foundation scores across all turns
    avg_care_harm = Column(Float, default=0.0)
    avg_fairness_cheating = Column(Float, default=0.0)
    avg_loyalty_betrayal = Column(Float, default=0.0)
    avg_authority_subversion = Column(Float, default=0.0)
    avg_sanctity_degradation = Column(Float, default=0.0)
    avg_liberty_oppression = Column(Float, default=0.0)
    
    # Primary moral foundations (top 3)
    primary_foundation_1 = Column(String(50))
    primary_foundation_2 = Column(String(50))
    primary_foundation_3 = Column(String(50))
    
    # Aggregate metrics
    moral_profile_narrative = Column(Text)
    total_moral_engagement = Column(Float, default=0.0)
    
    # Counts of turns with each foundation present
    turns_with_care_harm = Column(Integer, default=0)
    turns_with_fairness = Column(Integer, default=0)
    turns_with_loyalty = Column(Integer, default=0)
    turns_with_authority = Column(Integer, default=0)
    turns_with_sanctity = Column(Integer, default=0)
    turns_with_liberty = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    interview = relationship("Interview", back_populates="moral_foundations_profile")


class MoralFoundationsPriority(Base):
    """Links moral foundations to priority themes."""
    __tablename__ = 'moral_foundations_priorities'
    
    id = Column(Integer, primary_key=True)
    priority_id = Column(Integer, ForeignKey('priorities.id'), nullable=False)
    
    # Which foundations are associated with this priority
    care_harm_relevance = Column(Float, default=0.0)
    fairness_relevance = Column(Float, default=0.0)
    loyalty_relevance = Column(Float, default=0.0)
    authority_relevance = Column(Float, default=0.0)
    sanctity_relevance = Column(Float, default=0.0)
    liberty_relevance = Column(Float, default=0.0)
    
    # Narrative explanation
    moral_framing = Column(Text)
    
    # Relationships
    priority = relationship("Priority", back_populates="moral_foundations")


# SQL to create tables
CREATE_TABLES_SQL = """
-- Turn-level citation metadata
CREATE TABLE IF NOT EXISTS turn_citation_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    turn_id INTEGER NOT NULL,
    semantic_tags JSON NOT NULL DEFAULT '[]',
    key_phrases JSON NOT NULL DEFAULT '[]',
    quotable_segments JSON NOT NULL DEFAULT '[]',
    context_dependency REAL NOT NULL DEFAULT 0.5,
    standalone_clarity REAL NOT NULL DEFAULT 0.5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (turn_id) REFERENCES turns(id)
);

-- Interview insight citations
CREATE TABLE IF NOT EXISTS interview_insight_citations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    interview_id VARCHAR NOT NULL,
    insight_type VARCHAR NOT NULL,
    insight_id VARCHAR NOT NULL,
    citation_data JSON NOT NULL,
    primary_turn_ids JSON,
    supporting_turn_ids JSON,
    confidence_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (interview_id) REFERENCES interviews(id)
);

-- Turn-level MFT analysis
CREATE TABLE IF NOT EXISTS turn_moral_foundations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    turn_id INTEGER NOT NULL,
    reasoning TEXT,
    care_harm REAL DEFAULT 0.0,
    fairness_cheating REAL DEFAULT 0.0,
    loyalty_betrayal REAL DEFAULT 0.0,
    authority_subversion REAL DEFAULT 0.0,
    sanctity_degradation REAL DEFAULT 0.0,
    liberty_oppression REAL DEFAULT 0.0,
    dominant_foundation VARCHAR(50),
    foundations_narrative TEXT,
    mft_confidence REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (turn_id) REFERENCES turns(id)
);

-- Interview-level MFT aggregates
CREATE TABLE IF NOT EXISTS interview_moral_foundations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    interview_id VARCHAR(20) NOT NULL,
    avg_care_harm REAL DEFAULT 0.0,
    avg_fairness_cheating REAL DEFAULT 0.0,
    avg_loyalty_betrayal REAL DEFAULT 0.0,
    avg_authority_subversion REAL DEFAULT 0.0,
    avg_sanctity_degradation REAL DEFAULT 0.0,
    avg_liberty_oppression REAL DEFAULT 0.0,
    primary_foundation_1 VARCHAR(50),
    primary_foundation_2 VARCHAR(50),
    primary_foundation_3 VARCHAR(50),
    moral_profile_narrative TEXT,
    total_moral_engagement REAL DEFAULT 0.0,
    turns_with_care_harm INTEGER DEFAULT 0,
    turns_with_fairness INTEGER DEFAULT 0,
    turns_with_loyalty INTEGER DEFAULT 0,
    turns_with_authority INTEGER DEFAULT 0,
    turns_with_sanctity INTEGER DEFAULT 0,
    turns_with_liberty INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (interview_id) REFERENCES interviews(interview_id)
);

-- MFT-Priority linkage
CREATE TABLE IF NOT EXISTS moral_foundations_priorities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    priority_id INTEGER NOT NULL,
    care_harm_relevance REAL DEFAULT 0.0,
    fairness_relevance REAL DEFAULT 0.0,
    loyalty_relevance REAL DEFAULT 0.0,
    authority_relevance REAL DEFAULT 0.0,
    sanctity_relevance REAL DEFAULT 0.0,
    liberty_relevance REAL DEFAULT 0.0,
    moral_framing TEXT,
    FOREIGN KEY (priority_id) REFERENCES priorities(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_turn_citation_turn_id ON turn_citation_metadata(turn_id);
CREATE INDEX IF NOT EXISTS idx_interview_citation_interview_id ON interview_insight_citations(interview_id);
CREATE INDEX IF NOT EXISTS idx_interview_citation_insight ON interview_insight_citations(insight_type, insight_id);
CREATE INDEX IF NOT EXISTS idx_turn_mft_turn_id ON turn_moral_foundations(turn_id);
CREATE INDEX IF NOT EXISTS idx_interview_mft_interview_id ON interview_moral_foundations(interview_id);
CREATE INDEX IF NOT EXISTS idx_mft_priority_id ON moral_foundations_priorities(priority_id);
"""