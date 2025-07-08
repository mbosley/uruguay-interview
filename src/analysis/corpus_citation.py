"""
Corpus-level citation system for cross-interview analysis.
"""
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

# Try to import numpy, but make it optional
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

@dataclass
class InterviewCitation:
    """Citation from corpus insight to interview insight."""
    interview_id: str
    insight_type: str
    insight_id: str
    relevance_score: float
    contribution_note: str
    
    def to_dict(self) -> Dict:
        return {
            "interview_id": self.interview_id,
            "insight_type": self.insight_type,
            "insight_id": self.insight_id,
            "relevance_score": self.relevance_score,
            "contribution_note": self.contribution_note
        }
    
@dataclass 
class CorpusInsight:
    """Corpus-level insight with interview citations."""
    insight_id: str
    insight_type: str  # trend, pattern, distribution, exception
    content: Dict
    supporting_interviews: List[InterviewCitation]
    prevalence: float  # % of interviews showing this
    confidence: float
    regional_variation: Optional[Dict] = None
    demographic_variation: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        return {
            "insight_id": self.insight_id,
            "insight_type": self.insight_type,
            "content": self.content,
            "supporting_interviews": [i.to_dict() for i in self.supporting_interviews],
            "prevalence": self.prevalence,
            "confidence": self.confidence,
            "regional_variation": self.regional_variation,
            "demographic_variation": self.demographic_variation
        }
    
    def get_full_citation_chain(self, db_session) -> Dict:
        """Trace citations all the way to turns."""
        from src.database.models import InterviewInsightCitation
        
        chain = {
            "corpus_insight": self.content,
            "interview_citations": []
        }
        
        for interview_cite in self.supporting_interviews:
            # Get interview insight
            interview_insight = db_session.query(InterviewInsightCitation).filter_by(
                interview_id=interview_cite.interview_id,
                insight_id=interview_cite.insight_id
            ).first()
            
            if interview_insight:
                citation_data = interview_insight.citation_data
                chain["interview_citations"].append({
                    "interview_id": interview_cite.interview_id,
                    "insight": citation_data,
                    "turn_ids": citation_data.get("primary_turn_ids", [])
                })
        
        return chain

class CorpusAnalyzer:
    """Analyze corpus with citation tracking."""
    
    def __init__(self, interviews: List[Dict]):
        self.interviews = {i['id']: i for i in interviews}
        self.insight_index = self._build_insight_index()
        
    def _build_insight_index(self) -> Dict:
        """Build searchable index of all interview insights."""
        index = {
            'by_theme': {},
            'by_type': {},
            'by_tag': {},
            'by_location': {}
        }
        
        for interview_id, interview in self.interviews.items():
            # Get citation-aware insights
            citation_insights = interview.get('citation_aware_insights', {})
            
            # Index national priorities
            for priority in citation_insights.get('national_priorities', []):
                theme = priority.get('theme')
                if theme not in index['by_theme']:
                    index['by_theme'][theme] = []
                index['by_theme'][theme].append({
                    'interview_id': interview_id,
                    'insight': priority,
                    'type': 'national_priority',
                    'location': interview.get('metadata', {}).get('department', 'Unknown')
                })
            
            # Index local priorities
            for priority in citation_insights.get('local_priorities', []):
                theme = priority.get('theme')
                if theme not in index['by_theme']:
                    index['by_theme'][theme] = []
                index['by_theme'][theme].append({
                    'interview_id': interview_id,
                    'insight': priority,
                    'type': 'local_priority',
                    'location': interview.get('metadata', {}).get('municipality', 'Unknown')
                })
        
        return index
    
    def find_pattern(self, pattern_type: str, min_prevalence: float = 0.1) -> List[CorpusInsight]:
        """Find patterns across interviews with citations."""
        patterns = []
        
        if pattern_type == 'common_priorities':
            patterns.extend(self._find_common_priorities(min_prevalence))
        elif pattern_type == 'emotional_patterns':
            patterns.extend(self._find_emotional_patterns(min_prevalence))
        elif pattern_type == 'regional_differences':
            patterns.extend(self._find_regional_differences())
            
        return patterns
    
    def _find_common_priorities(self, min_prevalence: float) -> List[CorpusInsight]:
        """Find commonly mentioned priorities with citations."""
        insights = []
        
        # Count theme occurrences
        for theme, instances in self.insight_index['by_theme'].items():
            count = len(instances)
            prevalence = count / len(self.interviews)
            
            if prevalence >= min_prevalence:
                # Create corpus insight
                insight = CorpusInsight(
                    insight_id=f"common_priority_{theme}",
                    insight_type="pattern",
                    content={
                        "pattern": f"{theme} is a common priority",
                        "prevalence": prevalence,
                        "count": count,
                        "total": len(self.interviews),
                        "theme": theme
                    },
                    supporting_interviews=[
                        InterviewCitation(
                            interview_id=inst['interview_id'],
                            insight_type=inst['type'],
                            insight_id=f"{theme}_{inst['insight'].get('rank', 1)}",
                            relevance_score=inst['insight'].get('emotional_intensity', 0.5),
                            contribution_note=f"Ranked {inst['insight'].get('rank', 'N/A')} priority: {theme}"
                        )
                        for inst in instances
                    ],
                    prevalence=prevalence,
                    confidence=min(0.9, prevalence * 2)  # Higher prevalence = higher confidence
                )
                
                # Add regional variation
                insight.regional_variation = self._calculate_regional_variation(instances)
                
                insights.append(insight)
        
        return sorted(insights, key=lambda x: x.prevalence, reverse=True)
    
    def _find_emotional_patterns(self, min_prevalence: float) -> List[CorpusInsight]:
        """Find common emotional patterns with citations."""
        insights = []
        
        # Analyze emotional intensity across themes
        theme_emotions = {}
        
        for theme, instances in self.insight_index['by_theme'].items():
            intensities = [inst['insight'].get('emotional_intensity', 0) for inst in instances]
            if intensities:
                avg_intensity = sum(intensities) / len(intensities) if not HAS_NUMPY else np.mean(intensities)
                high_emotion_count = sum(1 for i in intensities if i > 0.7)
                
                if high_emotion_count / len(self.interviews) >= min_prevalence:
                    theme_emotions[theme] = {
                        'avg_intensity': avg_intensity,
                        'high_emotion_count': high_emotion_count,
                        'instances': instances
                    }
        
        # Create insights for high-emotion themes
        for theme, data in theme_emotions.items():
            insight = CorpusInsight(
                insight_id=f"emotional_pattern_{theme}",
                insight_type="emotional_pattern",
                content={
                    "pattern": f"High emotional intensity around {theme}",
                    "average_intensity": data['avg_intensity'],
                    "high_emotion_interviews": data['high_emotion_count'],
                    "theme": theme
                },
                supporting_interviews=[
                    InterviewCitation(
                        interview_id=inst['interview_id'],
                        insight_type=inst['type'],
                        insight_id=f"{theme}_emotion",
                        relevance_score=inst['insight'].get('emotional_intensity', 0),
                        contribution_note=f"Emotional intensity: {inst['insight'].get('emotional_intensity', 0):.2f}"
                    )
                    for inst in data['instances']
                    if inst['insight'].get('emotional_intensity', 0) > 0.7
                ],
                prevalence=data['high_emotion_count'] / len(self.interviews),
                confidence=0.85
            )
            insights.append(insight)
        
        return insights
    
    def _find_regional_differences(self) -> List[CorpusInsight]:
        """Find patterns that vary by region."""
        insights = []
        
        # Analyze theme prevalence by department
        for theme, instances in self.insight_index['by_theme'].items():
            regional_data = self._calculate_regional_variation(instances)
            
            # Check for significant regional differences
            if regional_data and len(regional_data) > 1:
                prevalences = list(regional_data.values())
                if max(prevalences) - min(prevalences) > 0.3:  # Significant difference
                    insight = CorpusInsight(
                        insight_id=f"regional_pattern_{theme}",
                        insight_type="regional_difference",
                        content={
                            "pattern": f"{theme} shows regional variation",
                            "theme": theme,
                            "highest_region": max(regional_data, key=regional_data.get),
                            "lowest_region": min(regional_data, key=regional_data.get),
                            "variation_range": max(prevalences) - min(prevalences)
                        },
                        supporting_interviews=[
                            InterviewCitation(
                                interview_id=inst['interview_id'],
                                insight_type=inst['type'],
                                insight_id=f"{theme}_regional",
                                relevance_score=0.8,
                                contribution_note=f"From {inst['location']}"
                            )
                            for inst in instances
                        ],
                        prevalence=len(instances) / len(self.interviews),
                        confidence=0.8,
                        regional_variation=regional_data
                    )
                    insights.append(insight)
        
        return insights
    
    def _calculate_regional_variation(self, instances: List[Dict]) -> Dict[str, float]:
        """Calculate prevalence by region."""
        regional_counts = {}
        total_by_region = {}
        
        # Count instances by location
        for inst in instances:
            location = inst.get('location', 'Unknown')
            regional_counts[location] = regional_counts.get(location, 0) + 1
        
        # Count total interviews by location
        for interview in self.interviews.values():
            location = interview.get('metadata', {}).get('department', 'Unknown')
            total_by_region[location] = total_by_region.get(location, 0) + 1
        
        # Calculate prevalence
        regional_prevalence = {}
        for location, count in regional_counts.items():
            if location in total_by_region and total_by_region[location] > 0:
                regional_prevalence[location] = count / total_by_region[location]
        
        return regional_prevalence
    
    def generate_corpus_report(self) -> Dict:
        """Generate complete corpus analysis with full citations."""
        report = {
            "corpus_size": len(self.interviews),
            "analysis_timestamp": datetime.now().isoformat(),
            "patterns": {
                "common_priorities": [p.to_dict() for p in self.find_pattern('common_priorities', 0.2)],
                "emotional_patterns": [p.to_dict() for p in self.find_pattern('emotional_patterns', 0.15)],
                "regional_differences": [p.to_dict() for p in self.find_pattern('regional_differences')]
            },
            "citation_summary": self._generate_citation_summary()
        }
        
        return report
    
    def _generate_citation_summary(self) -> Dict:
        """Generate summary statistics about citations."""
        total_insights = 0
        insights_with_citations = 0
        
        for interview in self.interviews.values():
            citation_insights = interview.get('citation_aware_insights', {})
            for insight_type in ['national_priorities', 'local_priorities']:
                insights = citation_insights.get(insight_type, [])
                total_insights += len(insights)
                for insight in insights:
                    if 'structured_citations' in insight or 'citations' in insight:
                        insights_with_citations += 1
        
        return {
            "total_interviews": len(self.interviews),
            "total_insights": total_insights,
            "insights_with_citations": insights_with_citations,
            "citation_coverage": insights_with_citations / max(total_insights, 1),
            "average_insights_per_interview": total_insights / max(len(self.interviews), 1)
        }