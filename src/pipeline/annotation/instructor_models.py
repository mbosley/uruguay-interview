"""
Comprehensive Pydantic models for Uruguay interview annotation schema.
Used with Instructor for structured LLM outputs.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Union
from enum import Enum


class LocationInfo(BaseModel):
    """Geographic location information."""
    municipality: str = Field(description="Municipality where interview was conducted")
    department: str = Field(description="Department (state/province) where interview was conducted") 
    locality_size: Literal["rural", "small_town", "medium_city", "large_city"] = Field(
        description="Size classification of the locality"
    )


class ParticipantProfile(BaseModel):
    """Participant demographic and background information."""
    age_range: Literal["18-29", "30-49", "50-64", "65+"] = Field(
        description="Participant's age range based on interview content"
    )
    gender: Literal["male", "female", "non_binary", "prefer_not_to_say"] = Field(
        description="Participant's gender based on interview content"
    )
    occupation_sector: Literal[
        "agriculture", "manufacturing", "services", "public_sector", "education", 
        "healthcare", "commerce", "construction", "transport", "unemployed", "retired", "other"
    ] = Field(description="Primary occupation sector")
    organizational_affiliation: Optional[str] = Field(
        default=None, description="Any organizational or group affiliations mentioned"
    )
    self_described_political_stance: Optional[str] = Field(
        default=None, description="Political stance if mentioned by participant"
    )


class Priority(BaseModel):
    """A priority issue with ranking and elaboration."""
    rank: Literal[1, 2, 3] = Field(description="Priority ranking (1=highest, 3=lowest)")
    theme: str = Field(description="Main thematic area of this priority")
    specific_issues: List[str] = Field(
        description="Specific issues or problems within this theme"
    )
    narrative_elaboration: str = Field(
        description="How the participant elaborated on this priority in their own words"
    )


class AgencyAttribution(BaseModel):
    """Analysis of how participant attributes responsibility and agency."""
    government_responsibility: str = Field(
        description="What the participant sees as government's responsibility"
    )
    individual_responsibility: str = Field(
        description="What the participant sees as individual's responsibility"
    )
    structural_factors: str = Field(
        description="Structural or systemic factors the participant identifies"
    )
    agency_narrative: str = Field(
        description="Overall narrative about who has power to create change"
    )


class KeyNarratives(BaseModel):
    """Key narrative themes from the interview."""
    identity_narrative: str = Field(
        description="How participant describes their identity and role in society"
    )
    problem_narrative: str = Field(
        description="How participant frames problems and their causes"
    )
    hope_narrative: str = Field(
        description="How participant expresses hopes, aspirations, or vision for the future"
    )
    memorable_quotes: List[str] = Field(
        description="Notable or representative quotes from the participant"
    )


class InterviewDynamics(BaseModel):
    """Assessment of interview quality and dynamics."""
    rapport: Literal["excellent", "good", "adequate", "poor"] = Field(
        description="Quality of rapport between interviewer and participant"
    )
    rapport_narrative: str = Field(
        description="Description of rapport quality and evidence"
    )
    participant_engagement: Literal["highly_engaged", "engaged", "moderately_engaged", "disengaged"] = Field(
        description="Level of participant engagement throughout interview"
    )
    engagement_narrative: str = Field(
        description="Description of engagement level and evidence"
    )
    coherence: Literal["highly_coherent", "coherent", "somewhat_coherent", "incoherent"] = Field(
        description="Coherence of participant's responses and narrative"
    )
    coherence_narrative: str = Field(
        description="Description of coherence level and evidence"
    )


class TurnUncertainty(BaseModel):
    """Uncertainty tracking for individual turn annotations."""
    coding_confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence level in the coding decisions for this turn"
    )
    ambiguous_function: bool = Field(
        description="Whether the turn's function is ambiguous or unclear"
    )


class FunctionalAnnotation(BaseModel):
    """Functional analysis of a conversation turn."""
    reasoning: str = Field(
        description="Chain-of-thought analysis: What is the speaker doing in this turn? What linguistic cues indicate this function?"
    )
    primary_function: Literal[
        "greeting", "problem_identification", "solution_proposal", "agreement", 
        "disagreement", "question", "clarification", "narrative", "evaluation", 
        "closing", "elaboration", "meta_commentary"
    ] = Field(description="Primary communicative function of this turn")


class ContentAnnotation(BaseModel):
    """Content and topic analysis of a conversation turn."""
    reasoning: str = Field(
        description="Chain-of-thought analysis: What topics are discussed? What is the main content focus?"
    )
    topics: List[str] = Field(
        description="Main topics or themes discussed in this turn"
    )
    topic_narrative: str = Field(
        description="How the participant discusses these topics"
    )
    geographic_scope: List[Literal["local", "national", "regional"]] = Field(
        description="Geographic scope(s) of the issues discussed"
    )


class EvidenceAnnotation(BaseModel):
    """Evidence and argumentation analysis of a conversation turn."""
    reasoning: str = Field(
        description="Chain-of-thought analysis: What type of evidence is provided? How specific is it?"
    )
    evidence_type: Literal[
        "personal_experience", "hearsay", "media_report", "official_data", 
        "general_knowledge", "observation", "none"
    ] = Field(description="Type of evidence provided in this turn")
    evidence_narrative: str = Field(
        description="Description of the evidence provided"
    )
    specificity: Literal["highly_specific", "moderately_specific", "general", "vague"] = Field(
        description="How specific is the evidence or information provided"
    )


class StanceAnnotation(BaseModel):
    """Emotional stance and certainty analysis of a conversation turn."""
    reasoning: str = Field(
        description="Chain-of-thought analysis: What emotions are expressed? How certain is the speaker?"
    )
    emotional_valence: Literal["positive", "negative", "neutral", "mixed"] = Field(
        description="Overall emotional tone of this turn"
    )
    emotional_intensity: Literal["low", "moderate", "high"] = Field(
        description="Intensity of emotions expressed"
    )
    emotional_narrative: str = Field(
        description="Description of emotions and their expression"
    )
    certainty: Literal["certain", "mostly_certain", "uncertain", "very_uncertain"] = Field(
        description="Speaker's level of certainty about what they're saying"
    )


class CompleteTurn(BaseModel):
    """Complete annotation for a single conversation turn."""
    turn_id: int = Field(description="Unique identifier for this turn")
    speaker: Literal["interviewer", "participant"] = Field(description="Who is speaking")
    text: str = Field(description="The actual text of what was said")
    
    # Uncertainty tracking
    uncertainty_tracking: TurnUncertainty
    
    # Core annotations with reasoning
    functional_annotation: FunctionalAnnotation
    content_annotation: ContentAnnotation  
    evidence_annotation: EvidenceAnnotation
    stance_annotation: StanceAnnotation
    
    # Summary
    turn_narrative_summary: str = Field(
        description="Brief summary of this turn's key contributions to the interview"
    )


class CompleteInterviewAnnotation(BaseModel):
    """Complete structured annotation for an entire interview."""
    
    # ===== INTERVIEW METADATA (7 elements) =====
    interview_id: str = Field(description="Interview identifier")
    date: str = Field(description="Date of interview (YYYY-MM-DD format)")
    location: LocationInfo
    duration_minutes: Optional[int] = Field(
        default=None, description="Interview duration in minutes if determinable"
    )
    interviewer_ids: List[str] = Field(
        description="List of interviewer identifiers or names"
    )
    
    # ===== PARTICIPANT PROFILE (5 elements) =====
    participant_profile: ParticipantProfile
    
    # ===== PRIORITY ANALYSIS (18 elements total) =====
    national_priorities: List[Priority] = Field(
        min_length=3, max_length=3,
        description="Top 3 national priorities identified by participant, ranked 1-3"
    )
    local_priorities: List[Priority] = Field(
        min_length=3, max_length=3,
        description="Top 3 local priorities identified by participant, ranked 1-3"
    )
    
    # ===== NARRATIVE FEATURES (10 elements) =====
    dominant_frame: str = Field(
        description="The dominant interpretive frame the participant uses to make sense of issues"
    )
    frame_narrative: str = Field(
        description="Description of how this frame manifests in the interview"
    )
    temporal_orientation: Literal["past_focused", "present_focused", "future_focused", "mixed"] = Field(
        description="Primary temporal orientation of the participant's narrative"
    )
    temporal_narrative: str = Field(
        description="How temporal orientation manifests in the participant's discourse"
    )
    agency_attribution: AgencyAttribution
    solution_orientation: Literal["problem_focused", "solution_focused", "balanced"] = Field(
        description="Whether participant focuses more on problems or solutions"
    )
    solution_narrative: str = Field(
        description="How the participant discusses solutions and change"
    )
    
    # ===== KEY NARRATIVES (4 elements) =====
    key_narratives: KeyNarratives
    
    # ===== ANALYTICAL NOTES (4 elements) =====
    tensions_contradictions: str = Field(
        description="Internal tensions or contradictions in the participant's discourse"
    )
    silences_omissions: str = Field(
        description="Notable silences, omissions, or topics avoided"
    )
    interviewer_reflections: str = Field(
        description="Reflections on interviewer performance and interview quality"
    )
    connections_to_broader_themes: str = Field(
        description="How this interview connects to broader social and political themes"
    )
    
    # ===== INTERVIEW DYNAMICS (6 elements) =====
    interview_dynamics: InterviewDynamics
    
    # ===== ALL CONVERSATION TURNS (1,602 elements = 18 per turn × 89 turns) =====
    turns: List[CompleteTurn] = Field(
        description="Complete annotation for every conversation turn in the interview"
    )
    
    # ===== OVERALL UNCERTAINTY TRACKING (3 elements) =====
    overall_confidence: float = Field(
        ge=0.0, le=1.0, 
        description="Overall confidence in the annotation quality (0.0 to 1.0)"
    )
    uncertainty_flags: List[str] = Field(
        description="List of specific uncertainties or challenges in this annotation"
    )
    uncertainty_narrative: str = Field(
        description="Narrative description of annotation uncertainties and limitations"
    )