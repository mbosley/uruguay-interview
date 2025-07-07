"""
Moral Foundations Theory (MFT) analyzer for interview annotations.
Implements the 6 moral foundations as a 6th dimension of turn-level analysis.
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class MoralFoundation:
    """Definition of a moral foundation."""
    name: str
    virtue: str
    vice: str
    keywords: List[str]
    spanish_keywords: List[str]
    example_phrases: List[str]


# Define the 6 moral foundations with Spanish/Uruguayan context
MORAL_FOUNDATIONS = {
    "care_harm": MoralFoundation(
        name="Care/Harm",
        virtue="Care, compassion, nurturing",
        vice="Harm, suffering, cruelty",
        keywords=["care", "protect", "safe", "harm", "hurt", "suffer", "cruel", "kind", "compassion"],
        spanish_keywords=["cuidar", "proteger", "seguro", "daño", "herir", "sufrir", "cruel", "amable", "compasión"],
        example_phrases=[
            "children need protection",
            "elderly are suffering",
            "we must take care of",
            "it hurts to see"
        ]
    ),
    "fairness_cheating": MoralFoundation(
        name="Fairness/Cheating",
        virtue="Fairness, justice, reciprocity",
        vice="Cheating, deception, unfairness",
        keywords=["fair", "equal", "justice", "rights", "cheat", "corrupt", "deserve", "earn"],
        spanish_keywords=["justo", "igual", "justicia", "derechos", "trampa", "corrupto", "merecer", "ganar"],
        example_phrases=[
            "everyone deserves equal",
            "it's not fair that",
            "corruption in government",
            "they earned it"
        ]
    ),
    "loyalty_betrayal": MoralFoundation(
        name="Loyalty/Betrayal",
        virtue="Loyalty, patriotism, self-sacrifice",
        vice="Betrayal, treason, abandonment",
        keywords=["loyal", "betray", "abandon", "together", "united", "solidarity", "community", "nation"],
        spanish_keywords=["leal", "traicionar", "abandonar", "juntos", "unidos", "solidaridad", "comunidad", "nación"],
        example_phrases=[
            "we must stick together",
            "abandoned by the state",
            "our community needs",
            "unity is important"
        ]
    ),
    "authority_subversion": MoralFoundation(
        name="Authority/Subversion",
        virtue="Authority, respect, tradition",
        vice="Subversion, disobedience, disrespect",
        keywords=["respect", "authority", "tradition", "order", "chaos", "obey", "hierarchy", "elder"],
        spanish_keywords=["respeto", "autoridad", "tradición", "orden", "caos", "obedecer", "jerarquía", "mayor"],
        example_phrases=[
            "respect for elders",
            "law and order",
            "traditional values",
            "need strong leadership"
        ]
    ),
    "sanctity_degradation": MoralFoundation(
        name="Sanctity/Degradation",
        virtue="Sanctity, purity, elevation",
        vice="Degradation, contamination, debasement",
        keywords=["sacred", "pure", "clean", "dirty", "contaminate", "degrade", "noble", "base"],
        spanish_keywords=["sagrado", "puro", "limpio", "sucio", "contaminar", "degradar", "noble", "bajo"],
        example_phrases=[
            "sacred values",
            "moral decay",
            "contaminating our youth",
            "pure intentions"
        ]
    ),
    "liberty_oppression": MoralFoundation(
        name="Liberty/Oppression",
        virtue="Liberty, freedom, autonomy",
        vice="Oppression, tyranny, restriction",
        keywords=["freedom", "liberty", "oppression", "control", "autonomy", "restrict", "independent", "tyranny"],
        spanish_keywords=["libertad", "libre", "opresión", "control", "autonomía", "restringir", "independiente", "tiranía"],
        example_phrases=[
            "our freedom to",
            "government control",
            "restricting our rights",
            "need independence"
        ]
    )
}


class MoralFoundationsAnalyzer:
    """Analyzes text for moral foundations content."""
    
    def __init__(self):
        """Initialize the MFT analyzer."""
        self.foundations = MORAL_FOUNDATIONS
        logger.info("Initialized Moral Foundations analyzer")
    
    def analyze_turn(self, turn_text: str, context: Optional[str] = None) -> Dict[str, any]:
        """
        Analyze a conversation turn for moral foundations.
        
        Args:
            turn_text: The text of the conversation turn
            context: Optional context from previous turns
            
        Returns:
            Dictionary with MFT analysis including:
            - Scores for each foundation (0.0-1.0)
            - Dominant foundation
            - Narrative explanation
            - Confidence score
        """
        # Normalize text for analysis
        text_lower = turn_text.lower()
        
        # Score each foundation
        foundation_scores = {}
        foundation_evidence = {}
        
        for key, foundation in self.foundations.items():
            score, evidence = self._score_foundation(text_lower, foundation)
            foundation_scores[key] = score
            foundation_evidence[key] = evidence
        
        # Identify dominant foundation
        dominant_foundation = max(foundation_scores.items(), key=lambda x: x[1])
        
        # Generate narrative explanation
        narrative = self._generate_narrative(
            turn_text, 
            foundation_scores, 
            foundation_evidence,
            dominant_foundation
        )
        
        # Calculate confidence based on evidence strength
        total_score = sum(foundation_scores.values())
        confidence = min(0.95, total_score / 2.0)  # Cap at 0.95
        
        return {
            "reasoning": f"Analyzed moral foundations in turn. Found {dominant_foundation[0]} as dominant.",
            "care_harm": foundation_scores["care_harm"],
            "fairness_cheating": foundation_scores["fairness_cheating"],
            "loyalty_betrayal": foundation_scores["loyalty_betrayal"],
            "authority_subversion": foundation_scores["authority_subversion"],
            "sanctity_degradation": foundation_scores["sanctity_degradation"],
            "liberty_oppression": foundation_scores["liberty_oppression"],
            "dominant_foundation": dominant_foundation[0] if dominant_foundation[1] > 0.1 else "none",
            "foundations_narrative": narrative,
            "mft_confidence": confidence
        }
    
    def _score_foundation(self, text: str, foundation: MoralFoundation) -> Tuple[float, List[str]]:
        """Score a single foundation based on keyword presence."""
        score = 0.0
        evidence = []
        
        # Check English keywords
        for keyword in foundation.keywords:
            if keyword in text:
                score += 0.15
                evidence.append(f"'{keyword}'")
        
        # Check Spanish keywords (weighted slightly higher for Uruguay)
        for keyword in foundation.spanish_keywords:
            if keyword in text:
                score += 0.2
                evidence.append(f"'{keyword}' (Spanish)")
        
        # Check example phrases
        for phrase in foundation.example_phrases:
            if phrase.lower() in text:
                score += 0.3
                evidence.append(f"phrase: '{phrase}'")
        
        # Cap score at 1.0
        return min(1.0, score), evidence
    
    def _generate_narrative(self, text: str, scores: Dict[str, float], 
                          evidence: Dict[str, List[str]], 
                          dominant: Tuple[str, float]) -> str:
        """Generate narrative explanation of moral foundations present."""
        
        # Count active foundations (score > 0.1)
        active_foundations = [(k, v) for k, v in scores.items() if v > 0.1]
        
        if not active_foundations:
            return "No clear moral foundations expressed in this turn."
        
        if len(active_foundations) == 1:
            foundation_name = self.foundations[active_foundations[0][0]].name
            return f"Primarily expresses {foundation_name} foundation through {', '.join(evidence[active_foundations[0][0]])}."
        
        # Multiple foundations
        narrative_parts = []
        for foundation_key, score in sorted(active_foundations, key=lambda x: x[1], reverse=True)[:3]:
            foundation = self.foundations[foundation_key]
            if evidence[foundation_key]:
                narrative_parts.append(f"{foundation.name} ({score:.1f})")
        
        return f"Multiple moral foundations: {', '.join(narrative_parts)}. " \
               f"Dominant theme is {self.foundations[dominant[0]].name}."
    
    def analyze_interview_aggregate(self, turn_analyses: List[Dict[str, any]]) -> Dict[str, any]:
        """
        Aggregate MFT analysis across all turns in an interview.
        
        Args:
            turn_analyses: List of turn-level MFT analyses
            
        Returns:
            Aggregated MFT profile for the interview
        """
        if not turn_analyses:
            return {}
        
        # Calculate average scores for each foundation
        foundation_sums = {
            "care_harm": 0.0,
            "fairness_cheating": 0.0,
            "loyalty_betrayal": 0.0,
            "authority_subversion": 0.0,
            "sanctity_degradation": 0.0,
            "liberty_oppression": 0.0
        }
        
        foundation_counts = {k: 0 for k in foundation_sums}
        
        # Sum up scores
        for analysis in turn_analyses:
            for foundation in foundation_sums:
                if foundation in analysis and analysis[foundation] > 0:
                    foundation_sums[foundation] += analysis[foundation]
                    foundation_counts[foundation] += 1
        
        # Calculate averages
        foundation_averages = {}
        for foundation, total in foundation_sums.items():
            count = foundation_counts[foundation]
            foundation_averages[foundation] = total / count if count > 0 else 0.0
        
        # Find primary moral profile
        sorted_foundations = sorted(foundation_averages.items(), key=lambda x: x[1], reverse=True)
        primary_foundations = [f for f, score in sorted_foundations[:3] if score > 0.1]
        
        return {
            "average_scores": foundation_averages,
            "primary_foundations": primary_foundations,
            "moral_profile_narrative": self._generate_profile_narrative(foundation_averages, primary_foundations),
            "total_moral_engagement": sum(foundation_averages.values()) / 6.0
        }
    
    def _generate_profile_narrative(self, averages: Dict[str, float], 
                                   primary: List[str]) -> str:
        """Generate narrative description of moral profile."""
        if not primary:
            return "Limited moral foundation language in this interview."
        
        if len(primary) == 1:
            foundation = self.foundations[primary[0]]
            return f"Strongly focused on {foundation.name} moral concerns throughout the interview."
        
        foundation_names = [self.foundations[f].name for f in primary]
        return f"Moral discourse centers on {', '.join(foundation_names[:2])} " \
               f"{'and ' + foundation_names[2] if len(foundation_names) > 2 else ''}."


# Example usage for testing
if __name__ == "__main__":
    analyzer = MoralFoundationsAnalyzer()
    
    # Test with sample text
    sample_text = "The government has abandoned our community. We need to take care of our elderly who are suffering. It's not fair that politicians are corrupt while we work hard."
    
    result = analyzer.analyze_turn(sample_text)
    print("MFT Analysis:")
    for key, value in result.items():
        print(f"  {key}: {value}")