"""
Semantic tagging system for conversation turns.
Tags turns with standardized labels for citation matching.
"""
from typing import List, Dict, Tuple
import re

class SemanticTagger:
    """Extract semantic tags from annotated turns."""
    
    # Define tag taxonomy
    TAG_TAXONOMY = {
        "concerns": [
            "security_concern",
            "economic_worry",
            "health_anxiety",
            "education_concern",
            "infrastructure_complaint"
        ],
        "emotions": [
            "hope_expression",
            "frustration_statement",
            "nostalgia_reference",
            "pride_expression",
            "fear_articulation"
        ],
        "evidence_types": [
            "personal_experience",
            "community_observation",
            "statistical_claim",
            "media_reference",
            "historical_comparison"
        ],
        "solution_types": [
            "policy_proposal",
            "individual_action",
            "community_initiative",
            "government_request"
        ]
    }
    
    def extract_tags(self, turn_annotation: Dict) -> List[str]:
        """Extract semantic tags from turn annotation."""
        tags = []
        
        # Extract from functional analysis
        function = turn_annotation.get("functional_analysis", {}).get("primary_function", "")
        tags.extend(self._map_function_to_tags(function))
        
        # Extract from content analysis
        topics = turn_annotation.get("content_analysis", {}).get("topics", [])
        tags.extend(self._map_topics_to_tags(topics))
        
        # Extract from emotional analysis
        emotions = turn_annotation.get("emotional_analysis", {}).get("emotions_expressed", [])
        tags.extend(self._map_emotions_to_tags(emotions))
        
        # Extract from evidence type
        evidence = turn_annotation.get("evidence_analysis", {}).get("evidence_type", "")
        tags.extend(self._map_evidence_to_tags(evidence))
        
        return list(set(tags))  # Remove duplicates
    
    def extract_key_phrases(self, turn_text: str, turn_annotation: Dict) -> List[Dict]:
        """Extract quotable key phrases from turn."""
        phrases = []
        
        # Use annotation to identify important segments
        # This is a simplified version - enhance with NLP techniques
        sentences = re.split(r'[.!?]+', turn_text)
        
        for sentence in sentences:
            if len(sentence.strip()) > 20:  # Meaningful length
                importance = self._calculate_phrase_importance(sentence, turn_annotation)
                if importance > 0.5:
                    phrases.append({
                        "text": sentence.strip(),
                        "start_char": turn_text.find(sentence),
                        "end_char": turn_text.find(sentence) + len(sentence),
                        "importance": importance
                    })
        
        return sorted(phrases, key=lambda x: x["importance"], reverse=True)[:5]
    
    def _calculate_phrase_importance(self, phrase: str, annotation: Dict) -> float:
        """Calculate importance score for a phrase."""
        score = 0.5  # Base score
        
        # Boost for emotional intensity
        emotional_intensity = annotation.get("emotional_analysis", {}).get("intensity", 0)
        score += emotional_intensity * 0.2
        
        # Boost for key topics
        if any(topic in phrase.lower() for topic in ["seguridad", "trabajo", "salud", "educación"]):
            score += 0.2
            
        # Boost for personal experience
        if annotation.get("evidence_analysis", {}).get("evidence_type") == "experiencia_personal":
            score += 0.1
            
        return min(score, 1.0)
    
    def _map_function_to_tags(self, function: str) -> List[str]:
        """Map primary function to semantic tags."""
        function_tag_map = {
            "problem_identification": ["concern", "issue_statement"],
            "solution_proposal": ["policy_proposal", "solution_suggestion"],
            "personal_narrative": ["personal_experience", "life_story"],
            "evaluation": ["assessment", "judgment"],
            "agreement": ["support", "endorsement"],
            "disagreement": ["opposition", "critique"]
        }
        return function_tag_map.get(function, [])
    
    def _map_topics_to_tags(self, topics: List[str]) -> List[str]:
        """Map topics to semantic tags."""
        tags = []
        topic_map = {
            "security": "security_concern",
            "seguridad": "security_concern",
            "economy": "economic_worry",
            "economía": "economic_worry",
            "trabajo": "economic_worry",
            "health": "health_anxiety",
            "salud": "health_anxiety",
            "education": "education_concern",
            "educación": "education_concern",
            "infrastructure": "infrastructure_complaint",
            "infraestructura": "infrastructure_complaint"
        }
        
        for topic in topics:
            topic_lower = topic.lower()
            for key, tag in topic_map.items():
                if key in topic_lower:
                    tags.append(tag)
        
        return tags
    
    def _map_emotions_to_tags(self, emotions: List[str]) -> List[str]:
        """Map emotions to semantic tags."""
        emotion_map = {
            "hope": "hope_expression",
            "esperanza": "hope_expression",
            "frustration": "frustration_statement",
            "frustración": "frustration_statement",
            "nostalgia": "nostalgia_reference",
            "pride": "pride_expression",
            "orgullo": "pride_expression",
            "fear": "fear_articulation",
            "miedo": "fear_articulation",
            "concern": "concern_expression",
            "preocupación": "concern_expression"
        }
        
        tags = []
        for emotion in emotions:
            emotion_lower = emotion.lower()
            for key, tag in emotion_map.items():
                if key in emotion_lower:
                    tags.append(tag)
        
        return tags
    
    def _map_evidence_to_tags(self, evidence_type: str) -> List[str]:
        """Map evidence type to semantic tags."""
        evidence_map = {
            "personal_experience": ["personal_experience"],
            "experiencia_personal": ["personal_experience"],
            "family_experience": ["personal_experience", "family_story"],
            "community_observation": ["community_observation"],
            "observación_comunitaria": ["community_observation"],
            "media_reference": ["media_reference"],
            "statistical_claim": ["statistical_claim"],
            "historical_comparison": ["historical_comparison"]
        }
        
        return evidence_map.get(evidence_type, [])
    
    def _find_semantic_matches(self, insight: Dict, turn: Dict) -> List[str]:
        """Find semantic tag matches between insight and turn."""
        insight_tags = set(insight.get('semantic_tags', []))
        turn_tags = set(turn.get('citation_metadata', {}).get('semantic_tags', []))
        return list(insight_tags & turn_tags)