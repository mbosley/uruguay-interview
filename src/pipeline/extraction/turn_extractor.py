"""
Turn-level data extraction from XML annotations.
Extracts conversation turns and their detailed annotations.
"""
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class TurnData:
    """Represents a single conversation turn with all annotations."""
    turn_number: int
    speaker: str
    text: str
    
    # Functional annotation
    primary_function: Optional[str] = None
    secondary_functions: List[str] = field(default_factory=list)
    coding_confidence: float = 1.0
    ambiguous_function: bool = False
    
    # Content annotation
    topics: List[str] = field(default_factory=list)
    topic_narrative: Optional[str] = None
    geographic_scope: List[str] = field(default_factory=list)
    temporal_reference: Optional[str] = None
    actors_mentioned: List[str] = field(default_factory=list)
    indicates_priority: bool = False
    
    # Evidence annotation
    evidence_type: Optional[str] = None
    evidence_narrative: Optional[str] = None
    specificity: Optional[str] = None
    
    # Stance annotation
    emotional_valence: Optional[str] = None
    emotional_intensity: float = 0.0
    emotional_categories: List[str] = field(default_factory=list)
    stance_target: Optional[str] = None
    stance_polarity: Optional[str] = None
    certainty_level: Optional[str] = None
    
    # Metadata
    word_count: int = 0
    uncertainty_notes: Optional[str] = None


@dataclass
class ConversationData:
    """Aggregated conversation dynamics data."""
    total_turns: int = 0
    interviewer_turns: int = 0
    participant_turns: int = 0
    average_turn_length: float = 0.0
    
    question_count: int = 0
    topic_shifts: int = 0
    
    speaker_balance: float = 0.5
    longest_turn_speaker: Optional[str] = None
    longest_turn_words: int = 0
    
    conversation_flow: str = "mixed"
    topic_introduction_pattern: str = "collaborative"
    topic_depth: str = "moderate"


class TurnExtractor:
    """Extracts turn-level data from XML annotations."""
    
    def extract_turns(self, xml_path: Path) -> Tuple[List[TurnData], ConversationData]:
        """
        Extract all turns and conversation dynamics from XML.
        
        Args:
            xml_path: Path to the XML annotation file
            
        Returns:
            Tuple of (list of turns, conversation dynamics)
        """
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # Extract all turns
            turns = self._extract_turn_data(root)
            
            # Calculate conversation dynamics
            dynamics = self._calculate_dynamics(turns)
            
            return turns, dynamics
            
        except Exception as e:
            logger.error(f"Failed to extract turns from {xml_path}: {e}")
            raise
    
    def _extract_turn_data(self, root: ET.Element) -> List[TurnData]:
        """Extract all turn data from XML."""
        turns = []
        
        # Find turn_level section
        turn_level = root.find(".//turn_level")
        if turn_level is None:
            logger.warning("No turn_level section found in XML")
            return turns
        
        # Process each turn
        for turn_elem in turn_level.findall(".//turn"):
            turn_data = self._parse_single_turn(turn_elem)
            if turn_data:
                turns.append(turn_data)
        
        return turns
    
    def _parse_single_turn(self, turn_elem: ET.Element) -> Optional[TurnData]:
        """Parse a single turn element."""
        # Get turn ID and basic info
        turn_id_elem = turn_elem.find("turn_id")
        if turn_id_elem is None:
            return None
        
        try:
            turn_number = int(turn_id_elem.text)
        except (ValueError, TypeError):
            logger.warning(f"Invalid turn_id: {turn_id_elem.text}")
            return None
        
        # Get speaker
        speaker_elem = turn_elem.find("speaker")
        if speaker_elem is None or not speaker_elem.text:
            return None
        speaker = speaker_elem.text.strip()
        
        # Get text
        text_elem = turn_elem.find("text")
        if text_elem is None or not text_elem.text:
            return None
        text = text_elem.text.strip()
        
        # Create turn data
        turn_data = TurnData(
            turn_number=turn_number,
            speaker=speaker,
            text=text,
            word_count=len(text.split())
        )
        
        # Extract functional annotation
        self._extract_functional_annotation(turn_elem, turn_data)
        
        # Extract content annotation
        self._extract_content_annotation(turn_elem, turn_data)
        
        # Extract evidence annotation
        self._extract_evidence_annotation(turn_elem, turn_data)
        
        # Extract stance annotation
        self._extract_stance_annotation(turn_elem, turn_data)
        
        # Extract uncertainty tracking
        self._extract_uncertainty(turn_elem, turn_data)
        
        return turn_data
    
    def _extract_functional_annotation(self, turn_elem: ET.Element, turn_data: TurnData) -> None:
        """Extract functional annotation from turn."""
        func_elem = turn_elem.find(".//functional_annotation")
        if func_elem is None:
            return
        
        # Primary function
        primary_elem = func_elem.find("primary_function")
        if primary_elem is not None and primary_elem.text:
            turn_data.primary_function = primary_elem.text.strip()
        
        # Secondary functions
        secondary_elem = func_elem.find("secondary_functions")
        if secondary_elem is not None:
            for func in secondary_elem.findall("function"):
                if func.text:
                    turn_data.secondary_functions.append(func.text.strip())
    
    def _extract_content_annotation(self, turn_elem: ET.Element, turn_data: TurnData) -> None:
        """Extract content annotation from turn."""
        content_elem = turn_elem.find(".//content_annotation")
        if content_elem is None:
            return
        
        # Topics
        topics_elem = content_elem.find("topics")
        if topics_elem is not None and topics_elem.text:
            # Parse topics from text like "[employment, social_issues]"
            topics_text = topics_elem.text.strip()
            if topics_text.startswith("[") and topics_text.endswith("]"):
                topics_text = topics_text[1:-1]
                turn_data.topics = [t.strip() for t in topics_text.split(",")]
        
        # Topic narrative
        narrative_elem = content_elem.find("topic_narrative")
        if narrative_elem is not None and narrative_elem.text:
            turn_data.topic_narrative = narrative_elem.text.strip()
        
        # Geographic scope
        geo_elem = content_elem.find("geographic_scope")
        if geo_elem is not None and geo_elem.text:
            # Parse like topics
            geo_text = geo_elem.text.strip()
            if geo_text.startswith("[") and geo_text.endswith("]"):
                geo_text = geo_text[1:-1]
                turn_data.geographic_scope = [g.strip() for g in geo_text.split(",")]
        
        # Temporal reference
        temporal_elem = content_elem.find("temporal_reference")
        if temporal_elem is not None and temporal_elem.text:
            turn_data.temporal_reference = temporal_elem.text.strip()
        
        # Actors mentioned
        actors_elem = content_elem.find("actors_mentioned")
        if actors_elem is not None and actors_elem.text:
            actors_text = actors_elem.text.strip()
            if actors_text.startswith("[") and actors_text.endswith("]"):
                actors_text = actors_text[1:-1]
                turn_data.actors_mentioned = [a.strip() for a in actors_text.split(",")]
    
    def _extract_evidence_annotation(self, turn_elem: ET.Element, turn_data: TurnData) -> None:
        """Extract evidence annotation from turn."""
        evidence_elem = turn_elem.find(".//evidence_annotation")
        if evidence_elem is None:
            return
        
        # Evidence type
        type_elem = evidence_elem.find("evidence_type")
        if type_elem is not None and type_elem.text:
            turn_data.evidence_type = type_elem.text.strip()
        
        # Evidence narrative
        narrative_elem = evidence_elem.find("evidence_narrative")
        if narrative_elem is not None and narrative_elem.text:
            turn_data.evidence_narrative = narrative_elem.text.strip()
        
        # Specificity
        spec_elem = evidence_elem.find("specificity")
        if spec_elem is not None and spec_elem.text:
            turn_data.specificity = spec_elem.text.strip()
    
    def _extract_stance_annotation(self, turn_elem: ET.Element, turn_data: TurnData) -> None:
        """Extract stance/emotional annotation from turn."""
        stance_elem = turn_elem.find(".//stance_annotation")
        if stance_elem is None:
            return
        
        # Emotional valence
        valence_elem = stance_elem.find("emotional_valence")
        if valence_elem is not None and valence_elem.text:
            turn_data.emotional_valence = valence_elem.text.strip()
        
        # Emotional intensity
        intensity_elem = stance_elem.find("emotional_intensity")
        if intensity_elem is not None and intensity_elem.text:
            try:
                turn_data.emotional_intensity = float(intensity_elem.text)
            except (ValueError, TypeError):
                pass
        
        # Emotional narrative
        narrative_elem = stance_elem.find("emotional_narrative")
        if narrative_elem is not None and narrative_elem.text:
            # Could parse this for emotional categories
            narrative = narrative_elem.text.strip()
            # Simple extraction of emotions mentioned
            emotions = ["anger", "fear", "sadness", "joy", "frustration", "hope", "anxiety"]
            for emotion in emotions:
                if emotion in narrative.lower():
                    turn_data.emotional_categories.append(emotion)
    
    def _extract_uncertainty(self, turn_elem: ET.Element, turn_data: TurnData) -> None:
        """Extract uncertainty tracking from turn."""
        uncertainty_elem = turn_elem.find(".//uncertainty_tracking")
        if uncertainty_elem is None:
            return
        
        # Coding confidence
        confidence_elem = uncertainty_elem.find("coding_confidence")
        if confidence_elem is not None and confidence_elem.text:
            try:
                turn_data.coding_confidence = float(confidence_elem.text)
            except (ValueError, TypeError):
                pass
        
        # Ambiguous function
        ambiguous_elem = uncertainty_elem.find(".//ambiguous_function")
        if ambiguous_elem is not None and ambiguous_elem.text:
            turn_data.ambiguous_function = ambiguous_elem.text.lower() == "true"
        
        # Uncertainty notes
        notes_elem = uncertainty_elem.find("uncertainty_notes")
        if notes_elem is not None and notes_elem.text:
            turn_data.uncertainty_notes = notes_elem.text.strip()
    
    def _calculate_dynamics(self, turns: List[TurnData]) -> ConversationData:
        """Calculate conversation dynamics from turns."""
        dynamics = ConversationData()
        
        if not turns:
            return dynamics
        
        # Basic counts
        dynamics.total_turns = len(turns)
        dynamics.interviewer_turns = sum(1 for t in turns if t.speaker.lower() in ["interviewer", "entrevistador"])
        dynamics.participant_turns = dynamics.total_turns - dynamics.interviewer_turns
        
        # Average turn length
        total_words = sum(t.word_count for t in turns)
        dynamics.average_turn_length = total_words / len(turns) if turns else 0
        
        # Question count (turns with question function)
        dynamics.question_count = sum(1 for t in turns if t.primary_function == "question")
        
        # Topic shifts (simplified - when consecutive turns have different topics)
        topic_shifts = 0
        for i in range(1, len(turns)):
            if turns[i].topics and turns[i-1].topics:
                if not set(turns[i].topics).intersection(set(turns[i-1].topics)):
                    topic_shifts += 1
        dynamics.topic_shifts = topic_shifts
        
        # Speaker balance
        if dynamics.total_turns > 0:
            dynamics.speaker_balance = dynamics.participant_turns / dynamics.total_turns
        
        # Longest turn
        if turns:
            longest_turn = max(turns, key=lambda t: t.word_count)
            dynamics.longest_turn_speaker = longest_turn.speaker
            dynamics.longest_turn_words = longest_turn.word_count
        
        # Conversation flow (simplified heuristic)
        if dynamics.average_turn_length < 20:
            dynamics.conversation_flow = "choppy"
        elif dynamics.average_turn_length > 50:
            dynamics.conversation_flow = "smooth"
        else:
            dynamics.conversation_flow = "mixed"
        
        # Topic introduction pattern
        if dynamics.interviewer_turns > dynamics.participant_turns * 1.5:
            dynamics.topic_introduction_pattern = "interviewer_led"
        elif dynamics.participant_turns > dynamics.interviewer_turns * 1.5:
            dynamics.topic_introduction_pattern = "participant_led"
        else:
            dynamics.topic_introduction_pattern = "collaborative"
        
        return dynamics


if __name__ == "__main__":
    # Test the turn extractor
    extractor = TurnExtractor()
    
    # Example usage
    xml_path = Path("data/processed/annotations/xml/058_annotation.xml")
    if xml_path.exists():
        turns, dynamics = extractor.extract_turns(xml_path)
        print(f"Extracted {len(turns)} turns")
        print(f"Conversation dynamics: {dynamics}")
        
        # Show first few turns
        for turn in turns[:3]:
            print(f"\nTurn {turn.turn_number} ({turn.speaker}):")
            print(f"  Text: {turn.text[:100]}...")
            print(f"  Function: {turn.primary_function}")
            print(f"  Topics: {turn.topics}")
            print(f"  Emotion: {turn.emotional_valence}")