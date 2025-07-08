"""
Citation tracking system for interview-level insights.
Maps insights to supporting turns with confidence scores.
"""
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import json

@dataclass
class TurnCitation:
    """Citation linking an insight to a specific turn."""
    turn_id: int
    contribution_type: str  # primary_evidence, supporting, contextual, contradictory
    relevance_score: float  # 0.0-1.0
    specific_element: str   # Quoted text or description
    semantic_match: List[str]  # Matching semantic tags
    
    def to_dict(self) -> Dict:
        return {
            "turn_id": self.turn_id,
            "contribution_type": self.contribution_type,
            "relevance_score": self.relevance_score,
            "specific_element": self.specific_element,
            "semantic_match": self.semantic_match
        }

@dataclass
class InsightCitation:
    """Complete citation information for an interview insight."""
    insight_type: str  # priority, narrative_frame, emotional_arc, etc.
    insight_content: Dict
    primary_citations: List[TurnCitation]
    supporting_citations: List[TurnCitation]
    synthesis_note: str  # How turns combine to support insight
    confidence: float
    
    def to_dict(self) -> Dict:
        return {
            "insight_type": self.insight_type,
            "insight_content": self.insight_content,
            "primary_citations": [c.to_dict() for c in self.primary_citations],
            "supporting_citations": [c.to_dict() for c in self.supporting_citations],
            "synthesis_note": self.synthesis_note,
            "confidence": self.confidence
        }

class CitationTracker:
    """Track and validate citations between insights and turns."""
    
    def __init__(self, turns: List[Dict]):
        self.turns = {t['turn_id']: t for t in turns}
        self.turn_tags = self._extract_turn_tags()
        
    def _extract_turn_tags(self) -> Dict[int, List[str]]:
        """Extract semantic tags for each turn."""
        tags = {}
        for turn_id, turn in self.turns.items():
            citation_meta = turn.get('citation_metadata', {})
            tags[turn_id] = citation_meta.get('semantic_tags', [])
        return tags
    
    def create_citation(
        self,
        insight: Dict,
        cited_turn_ids: List[int],
        citation_details: List[Dict]
    ) -> InsightCitation:
        """Create validated citation for an insight."""
        primary_citations = []
        supporting_citations = []
        
        for turn_id, details in zip(cited_turn_ids, citation_details):
            if turn_id not in self.turns:
                continue
                
            turn = self.turns[turn_id]
            citation = TurnCitation(
                turn_id=turn_id,
                contribution_type=details.get('contribution_type', 'supporting'),
                relevance_score=self._calculate_relevance(insight, turn, details),
                specific_element=details.get('quote', ''),
                semantic_match=self._find_semantic_matches(insight, turn)
            )
            
            if citation.contribution_type == 'primary_evidence':
                primary_citations.append(citation)
            else:
                supporting_citations.append(citation)
        
        return InsightCitation(
            insight_type=insight.get('type', 'unknown'),
            insight_content=insight,
            primary_citations=primary_citations,
            supporting_citations=supporting_citations,
            synthesis_note=self._generate_synthesis_note(primary_citations, supporting_citations),
            confidence=self._calculate_overall_confidence(primary_citations, supporting_citations)
        )
    
    def _calculate_relevance(self, insight: Dict, turn: Dict, details: Dict) -> float:
        """Calculate relevance score between insight and turn."""
        base_score = 0.5
        
        # Check semantic tag overlap
        insight_tags = insight.get('semantic_tags', [])
        turn_tags = turn.get('citation_metadata', {}).get('semantic_tags', [])
        tag_overlap = len(set(insight_tags) & set(turn_tags)) / max(len(insight_tags), 1)
        base_score += tag_overlap * 0.3
        
        # Check if quoted text exists in turn
        quote = details.get('quote', '')
        if quote and quote in turn.get('text', ''):
            base_score += 0.2
            
        return min(base_score, 1.0)
    
    def _find_semantic_matches(self, insight: Dict, turn: Dict) -> List[str]:
        """Find semantic tag matches between insight and turn."""
        insight_tags = set(insight.get('semantic_tags', []))
        turn_tags = set(turn.get('citation_metadata', {}).get('semantic_tags', []))
        return list(insight_tags & turn_tags)
    
    def _generate_synthesis_note(self, primary: List[TurnCitation], supporting: List[TurnCitation]) -> str:
        """Generate a synthesis note explaining how citations support the insight."""
        if not primary:
            return "No primary evidence found"
            
        primary_turns = [f"turn {c.turn_id}" for c in primary]
        supporting_turns = [f"turn {c.turn_id}" for c in supporting]
        
        note = f"Primary evidence from {', '.join(primary_turns)}"
        if supporting:
            note += f", with supporting context from {', '.join(supporting_turns)}"
            
        return note
    
    def _calculate_overall_confidence(self, primary: List[TurnCitation], supporting: List[TurnCitation]) -> float:
        """Calculate overall confidence based on citation quality."""
        if not primary:
            return 0.3  # Low confidence without primary evidence
            
        # Base confidence from primary citations
        primary_scores = [c.relevance_score for c in primary]
        confidence = sum(primary_scores) / len(primary_scores)
        
        # Boost for supporting evidence
        if supporting:
            support_bonus = min(0.2, len(supporting) * 0.05)
            confidence = min(confidence + support_bonus, 1.0)
            
        return confidence
    
    def validate_citations(self, citations: List[InsightCitation]) -> List[Dict]:
        """Validate all citations and return issues found."""
        issues = []
        
        for citation in citations:
            # Check if cited turns exist
            for turn_cite in citation.primary_citations + citation.supporting_citations:
                if turn_cite.turn_id not in self.turns:
                    issues.append({
                        "type": "missing_turn",
                        "insight": citation.insight_type,
                        "turn_id": turn_cite.turn_id
                    })
                    
                # Verify quoted text
                elif turn_cite.specific_element:
                    turn_text = self.turns[turn_cite.turn_id].get('text', '')
                    if turn_cite.specific_element not in turn_text:
                        issues.append({
                            "type": "quote_mismatch",
                            "insight": citation.insight_type,
                            "turn_id": turn_cite.turn_id,
                            "quote": turn_cite.specific_element
                        })
        
        return issues