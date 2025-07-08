# Hierarchical Citation System Implementation Guide

## Overview

This guide provides step-by-step instructions for implementing a hierarchical citation system that enables full traceability from corpus-level insights down to individual conversation turns in the Uruguay Interview Analysis project.

## Architecture Summary

The citation system implements a three-level hierarchy:
1. **Turn-Level**: Individual conversation turns with semantic tags and key phrases
2. **Interview-Level**: Synthesized insights with citations to supporting turns
3. **Corpus-Level**: Cross-interview patterns with citations to interview insights

Each level maintains citations to the level below, creating a complete chain of evidence from high-level insights to specific utterances.

## Prerequisites

- Familiarity with the existing annotation pipeline
- Understanding of the current database schema
- Python 3.9+ development environment
- Access to the Uruguay Interview codebase

## Phase 1: Turn-Level Citation Enhancement (Days 1-3)

### Objective
Modify turn annotation to include extractable citation elements and semantic tags.

### Step 1.1: Update Turn Annotation Schema

**File**: `src/pipeline/annotation/multipass_annotator.py`

Add citation-ready fields to the turn annotation schema:

```python
# In the TURN_ANALYSIS_SCHEMA section, add:
"citation_metadata": {{
    "key_phrases": ["List of 2-5 important phrases from this turn"],
    "semantic_tags": ["List of semantic labels like 'security_concern', 'economic_worry'"],
    "quotable_segments": [
        {{
            "text": "Exact quote",
            "start_char": 0,
            "end_char": 50,
            "importance": 0.9
        }}
    ],
    "context_dependency": 0.7,  # How much this turn depends on surrounding context
    "standalone_clarity": 0.8   # How clear this turn is without context
}},
```

### Step 1.2: Create Semantic Tagger

**New File**: `src/pipeline/annotation/semantic_tagger.py`

```python
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
```

### Step 1.3: Modify Turn Annotation Prompt

**File**: `src/pipeline/annotation/multipass_annotator.py`

Update the turn annotation prompt to request citation metadata:

```python
# Add to the turn annotation prompt:
CITATION_INSTRUCTION = """
Additionally, for each turn provide citation_metadata:

1. key_phrases: Extract 2-5 important phrases that capture the essence of this turn
   - Prefer complete thoughts over fragments
   - Include emotional expressions
   - Capture specific claims or proposals

2. semantic_tags: Apply standardized tags from these categories:
   - Concerns: security_concern, economic_worry, health_anxiety, etc.
   - Emotions: hope_expression, frustration_statement, etc.
   - Evidence: personal_experience, community_observation, etc.
   - Solutions: policy_proposal, government_request, etc.

3. quotable_segments: Identify the most important direct quotes
   - Mark exact text boundaries
   - Rate importance (0.0-1.0)
   - Prefer self-contained statements

4. context_dependency: How much this turn relies on previous turns (0.0-1.0)
5. standalone_clarity: How understandable this turn is alone (0.0-1.0)
"""
```

### Step 1.4: Update Database Schema

**File**: `src/database/models.py`

Add citation metadata storage:

```python
# Add new table for citation metadata
class TurnCitationMetadata(Base):
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
    
    # Relationships
    turn = relationship("Turn", back_populates="citation_metadata")

# Update Turn model
class Turn(Base):
    # ... existing fields ...
    citation_metadata = relationship("TurnCitationMetadata", uselist=False, back_populates="turn")
```

### Step 1.5: Create Migration Script

**New File**: `scripts/add_citation_tables.py`

```python
#!/usr/bin/env python3
"""
Add citation tracking tables to support hierarchical citation system.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.models import Base, TurnCitationMetadata
from src.database.connection import get_engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_citation_tables():
    """Add citation-related tables to database."""
    engine = get_engine()
    
    # Create new tables
    logger.info("Creating citation metadata tables...")
    Base.metadata.create_all(engine, tables=[
        TurnCitationMetadata.__table__
    ])
    
    logger.info("Citation tables created successfully!")

if __name__ == "__main__":
    add_citation_tables()
```

## Phase 2: Interview-Level Citation Implementation (Days 4-7)

### Objective
Modify interview-level annotation to cite specific turns when generating insights.

### Step 2.1: Create Citation Tracking Structure

**New File**: `src/pipeline/annotation/citation_tracker.py`

```python
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
```

### Step 2.2: Update Interview Annotation Prompt

**File**: `src/pipeline/annotation/multipass_annotator.py`

Modify the interview-level prompt to require citations:

```python
INTERVIEW_CITATION_PROMPT = """
Based on the annotated turns provided, generate interview-level insights.

CRITICAL: For EVERY insight you generate, you MUST provide citations to specific turns.

For each insight, provide:
1. The insight itself (following the existing schema)
2. Citation information:
   - turn_ids: List of turn IDs that support this insight
   - citation_details: For each cited turn:
     - contribution_type: "primary_evidence" | "supporting" | "contextual" | "contradictory"
     - quote: Relevant text from that turn (exact quote preferred)
     - reason: Why this turn supports the insight

Example structure:
{
  "national_priorities": [{
    "theme": "security",
    "specific_issues": ["neighborhood crime", "police presence"],
    "emotional_intensity": 0.8,
    "citations": {
      "turn_ids": [3, 7, 15],
      "citation_details": [
        {
          "turn_id": 3,
          "contribution_type": "primary_evidence",
          "quote": "I can't sleep at night worrying about break-ins",
          "reason": "Direct expression of security concern"
        },
        {
          "turn_id": 7,
          "contribution_type": "supporting",
          "quote": "We installed bars on all windows",
          "reason": "Behavioral evidence of security concern"
        },
        {
          "turn_id": 15,
          "contribution_type": "contextual",
          "quote": "The whole neighborhood feels unsafe",
          "reason": "Community-level validation"
        }
      ]
    }
  }]
}

Remember:
- Every major claim needs at least one primary_evidence citation
- Look for patterns across multiple turns
- Note when turns contradict each other
- Include emotional peaks as supporting evidence
"""
```

### Step 2.3: Implement Citation-Aware Interview Annotator

**File**: `src/pipeline/annotation/multipass_annotator.py`

Modify the `_annotate_interview_level` method:

```python
async def _annotate_interview_level(self, interview_text: str, turn_annotations: List[Dict]) -> Dict:
    """Generate interview-level insights with citations."""
    
    # Prepare turns with IDs for citation
    turns_with_ids = []
    for i, turn_anno in enumerate(turn_annotations):
        turn_anno['turn_id'] = i + 1  # 1-indexed for clarity
        turns_with_ids.append(turn_anno)
    
    # Create citation tracker
    from src.pipeline.annotation.citation_tracker import CitationTracker
    citation_tracker = CitationTracker(turns_with_ids)
    
    # Generate prompt with citation requirements
    prompt = self._build_interview_prompt_with_citations(interview_text, turns_with_ids)
    
    # Get annotation with citations
    response = await self._make_api_call(prompt)
    annotation = self._parse_json_response(response)
    
    # Extract and validate citations
    validated_annotation = self._process_citations(annotation, citation_tracker)
    
    return validated_annotation

def _process_citations(self, annotation: Dict, tracker: CitationTracker) -> Dict:
    """Process and validate citations in annotation."""
    
    # Process each insight type
    for insight_type in ['national_priorities', 'local_priorities', 'key_narratives']:
        if insight_type not in annotation:
            continue
            
        insights = annotation[insight_type]
        if isinstance(insights, list):
            for i, insight in enumerate(insights):
                if 'citations' in insight:
                    citation_data = insight['citations']
                    citation = tracker.create_citation(
                        insight=insight,
                        cited_turn_ids=citation_data.get('turn_ids', []),
                        citation_details=citation_data.get('citation_details', [])
                    )
                    
                    # Replace with structured citation
                    insights[i]['structured_citations'] = citation.to_dict()
    
    # Validate all citations
    issues = tracker.validate_citations(self._extract_all_citations(annotation))
    if issues:
        annotation['citation_validation_issues'] = issues
    
    return annotation
```

### Step 2.4: Create Citation Storage

**File**: `src/database/models.py`

Add interview citation tables:

```python
class InterviewInsightCitation(Base):
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
    
    # Relationships
    interview = relationship("Interview", back_populates="insight_citations")

# Update Interview model
class Interview(Base):
    # ... existing fields ...
    insight_citations = relationship("InterviewInsightCitation", back_populates="interview")
```

## Phase 3: Corpus-Level Citation Implementation (Days 8-10)

### Objective
Implement corpus-level analysis that cites interview-level insights.

### Step 3.1: Create Corpus Citation Structure

**New File**: `src/analysis/corpus_citation.py`

```python
"""
Corpus-level citation system for cross-interview analysis.
"""
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass
import numpy as np

@dataclass
class InterviewCitation:
    """Citation from corpus insight to interview insight."""
    interview_id: str
    insight_type: str
    insight_id: str
    relevance_score: float
    contribution_note: str
    
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
    
    def get_full_citation_chain(self, db_session) -> Dict:
        """Trace citations all the way to turns."""
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
            'by_tag': {}
        }
        
        for interview_id, interview in self.interviews.items():
            # Index priorities
            for priority in interview.get('national_priorities', []):
                theme = priority.get('theme')
                if theme not in index['by_theme']:
                    index['by_theme'][theme] = []
                index['by_theme'][theme].append({
                    'interview_id': interview_id,
                    'insight': priority,
                    'type': 'national_priority'
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
        theme_counts = {}
        theme_citations = {}
        
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
                        "total": len(self.interviews)
                    },
                    supporting_interviews=[
                        InterviewCitation(
                            interview_id=inst['interview_id'],
                            insight_type=inst['type'],
                            insight_id=theme,
                            relevance_score=inst['insight'].get('emotional_intensity', 0.5),
                            contribution_note=f"Mentioned {theme} as priority"
                        )
                        for inst in instances
                    ],
                    prevalence=prevalence,
                    confidence=min(0.9, prevalence * 2)  # Higher prevalence = higher confidence
                )
                insights.append(insight)
        
        return insights
    
    def generate_corpus_report(self) -> Dict:
        """Generate complete corpus analysis with full citations."""
        report = {
            "corpus_size": len(self.interviews),
            "analysis_timestamp": datetime.now().isoformat(),
            "patterns": {
                "common_priorities": self.find_pattern('common_priorities', 0.2),
                "emotional_patterns": self.find_pattern('emotional_patterns', 0.15),
                "regional_differences": self.find_pattern('regional_differences')
            },
            "citation_summary": self._generate_citation_summary()
        }
        
        return report
```

### Step 3.2: Implement Corpus Analysis Pipeline

**New File**: `scripts/analyze_corpus_with_citations.py`

```python
#!/usr/bin/env python3
"""
Analyze interview corpus with hierarchical citations.
"""
import asyncio
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import get_db
from src.database.models import Interview, InterviewInsightCitation
from src.analysis.corpus_citation import CorpusAnalyzer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def analyze_corpus():
    """Run corpus analysis with citation tracking."""
    
    # Load all interviews with annotations
    db = get_db()
    interviews = db.query(Interview).filter(
        Interview.annotation_json.isnot(None)
    ).all()
    
    logger.info(f"Analyzing corpus of {len(interviews)} interviews")
    
    # Convert to dicts with annotations
    interview_data = []
    for interview in interviews:
        data = {
            'id': interview.id,
            'metadata': {
                'location': interview.location,
                'municipality': interview.municipality,
                'department': interview.department
            }
        }
        
        # Parse annotation
        if interview.annotation_json:
            annotation = json.loads(interview.annotation_json)
            data.update(annotation)
            
        interview_data.append(data)
    
    # Run corpus analysis
    analyzer = CorpusAnalyzer(interview_data)
    corpus_report = analyzer.generate_corpus_report()
    
    # Save report
    output_path = Path('data/analysis/corpus_analysis_with_citations.json')
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(corpus_report, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Corpus analysis saved to {output_path}")
    
    # Generate citation visualization
    generate_citation_graph(corpus_report)
    
    return corpus_report

def generate_citation_graph(corpus_report: Dict):
    """Generate visualization of citation network."""
    import networkx as nx
    import matplotlib.pyplot as plt
    
    G = nx.DiGraph()
    
    # Add corpus insights as nodes
    for pattern_type, patterns in corpus_report['patterns'].items():
        for pattern in patterns:
            node_id = f"corpus_{pattern.insight_id}"
            G.add_node(node_id, 
                      level='corpus',
                      type=pattern_type,
                      prevalence=pattern.prevalence)
            
            # Add interview citations
            for cite in pattern.supporting_interviews[:10]:  # Limit for visibility
                interview_node = f"interview_{cite.interview_id}_{cite.insight_id}"
                G.add_node(interview_node, level='interview')
                G.add_edge(interview_node, node_id, weight=cite.relevance_score)
    
    # Layout and draw
    pos = nx.spring_layout(G, k=2, iterations=50)
    
    plt.figure(figsize=(15, 10))
    
    # Draw nodes by level
    corpus_nodes = [n for n, d in G.nodes(data=True) if d['level'] == 'corpus']
    interview_nodes = [n for n, d in G.nodes(data=True) if d['level'] == 'interview']
    
    nx.draw_networkx_nodes(G, pos, corpus_nodes, node_color='red', 
                          node_size=500, label='Corpus Insights')
    nx.draw_networkx_nodes(G, pos, interview_nodes, node_color='blue',
                          node_size=200, label='Interview Insights')
    
    # Draw edges
    nx.draw_networkx_edges(G, pos, alpha=0.5)
    
    plt.title("Citation Network: Corpus → Interview Insights")
    plt.legend()
    plt.savefig('data/analysis/citation_network.png', dpi=300, bbox_inches='tight')
    logger.info("Citation network visualization saved")

if __name__ == "__main__":
    asyncio.run(analyze_corpus())
```

## Phase 4: Citation Validation and UI (Days 11-14)

### Step 4.1: Create Citation Validator

**New File**: `src/pipeline/quality/citation_validator.py`

```python
"""
Validate citation quality and completeness.
"""
from typing import List, Dict, Tuple, Optional
import re
from difflib import SequenceMatcher

class CitationValidator:
    """Validate citations at all levels."""
    
    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        self.validation_report = {
            'total_citations': 0,
            'valid_citations': 0,
            'issues': []
        }
    
    def validate_turn_citation(
        self, 
        citation: Dict, 
        turn_text: str,
        insight_text: str
    ) -> Tuple[bool, List[str]]:
        """Validate a single turn citation."""
        issues = []
        
        # Check if quoted text exists
        quoted_text = citation.get('specific_element', '')
        if quoted_text:
            if quoted_text not in turn_text:
                # Try fuzzy matching
                similarity = self._fuzzy_match(quoted_text, turn_text)
                if similarity < 0.8:
                    issues.append(f"Quote not found in turn: '{quoted_text[:50]}...'")
        
        # Check relevance score
        relevance = citation.get('relevance_score', 0)
        if relevance < 0.3:
            issues.append(f"Low relevance score: {relevance}")
        
        # Check semantic alignment
        if not self._check_semantic_alignment(citation, insight_text):
            issues.append("Weak semantic alignment between turn and insight")
        
        self.validation_report['total_citations'] += 1
        if not issues:
            self.validation_report['valid_citations'] += 1
        else:
            self.validation_report['issues'].extend(issues)
        
        return len(issues) == 0, issues
    
    def _fuzzy_match(self, quote: str, text: str) -> float:
        """Find best fuzzy match for quote in text."""
        # Normalize texts
        quote_normalized = ' '.join(quote.lower().split())
        text_normalized = ' '.join(text.lower().split())
        
        # Sliding window search
        best_ratio = 0
        window_size = len(quote_normalized)
        
        for i in range(len(text_normalized) - window_size + 1):
            window = text_normalized[i:i + window_size]
            ratio = SequenceMatcher(None, quote_normalized, window).ratio()
            best_ratio = max(best_ratio, ratio)
        
        return best_ratio
    
    def validate_interview_citations(
        self,
        interview_annotation: Dict,
        turn_annotations: List[Dict]
    ) -> Dict:
        """Validate all citations in an interview."""
        report = {
            'interview_id': interview_annotation.get('interview_id'),
            'total_insights': 0,
            'insights_with_citations': 0,
            'citation_coverage': {},
            'issues': []
        }
        
        # Create turn lookup
        turns = {t['turn_id']: t for t in turn_annotations}
        
        # Check each insight type
        for insight_type in ['national_priorities', 'local_priorities', 'key_narratives']:
            insights = interview_annotation.get(insight_type, [])
            if not insights:
                continue
                
            type_coverage = {
                'total': len(insights),
                'with_citations': 0,
                'citation_quality': []
            }
            
            for insight in insights:
                report['total_insights'] += 1
                
                citations = insight.get('structured_citations', {})
                if citations:
                    report['insights_with_citations'] += 1
                    type_coverage['with_citations'] += 1
                    
                    # Validate each citation
                    quality_score = self._assess_citation_quality(
                        citations, 
                        turns,
                        insight
                    )
                    type_coverage['citation_quality'].append(quality_score)
                else:
                    report['issues'].append(
                        f"Missing citations for {insight_type}: {insight.get('theme', 'unknown')}"
                    )
            
            report['citation_coverage'][insight_type] = type_coverage
        
        return report
    
    def _assess_citation_quality(
        self,
        citations: Dict,
        turns: Dict,
        insight: Dict
    ) -> float:
        """Assess overall quality of citations for an insight."""
        quality_score = 0.5  # Base score
        
        # Check primary evidence exists
        primary_citations = citations.get('primary_citations', [])
        if primary_citations:
            quality_score += 0.2
        else:
            return 0.3  # Severely penalize missing primary evidence
        
        # Check citation distribution
        cited_turn_ids = set()
        for cite in primary_citations + citations.get('supporting_citations', []):
            cited_turn_ids.add(cite.get('turn_id'))
        
        # Reward diverse citations
        if len(cited_turn_ids) > 1:
            quality_score += min(0.2, len(cited_turn_ids) * 0.05)
        
        # Check if citations span the interview
        if cited_turn_ids:
            turn_spread = (max(cited_turn_ids) - min(cited_turn_ids)) / len(turns)
            quality_score += turn_spread * 0.1
        
        return min(quality_score, 1.0)
    
    def generate_validation_report(self) -> Dict:
        """Generate comprehensive validation report."""
        return {
            'summary': {
                 'total_citations': self.validation_report['total_citations'],
                'valid_citations': self.validation_report['valid_citations'],
                'validity_rate': self.validation_report['valid_citations'] / 
                                max(self.validation_report['total_citations'], 1)
            },
            'issues_by_type': self._categorize_issues(),
            'recommendations': self._generate_recommendations()
        }
    
    def _categorize_issues(self) -> Dict:
        """Categorize validation issues."""
        categories = {
            'missing_quotes': [],
            'low_relevance': [],
            'semantic_mismatch': [],
            'missing_citations': []
        }
        
        for issue in self.validation_report['issues']:
            if 'Quote not found' in issue:
                categories['missing_quotes'].append(issue)
            elif 'Low relevance' in issue:
                categories['low_relevance'].append(issue)
            elif 'semantic alignment' in issue:
                categories['semantic_mismatch'].append(issue)
            elif 'Missing citations' in issue:
                categories['missing_citations'].append(issue)
        
        return categories
```

### Step 4.2: Create Citation Explorer UI

**New File**: `src/dashboard/citation_explorer.py`

```python
"""
Streamlit UI for exploring citation chains.
"""
import streamlit as st
import json
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import networkx as nx

class CitationExplorer:
    """Interactive citation exploration interface."""
    
    def __init__(self):
        st.set_page_config(
            page_title="Citation Explorer",
            page_icon="🔍",
            layout="wide"
        )
        self.load_data()
    
    def load_data(self):
        """Load corpus analysis and interview data."""
        # Load corpus analysis
        corpus_path = Path('data/analysis/corpus_analysis_with_citations.json')
        if corpus_path.exists():
            with open(corpus_path) as f:
                self.corpus_data = json.load(f)
        else:
            self.corpus_data = None
            
        # Load interview annotations
        # This would connect to the database in production
        self.interviews = {}
    
    def run(self):
        """Main UI flow."""
        st.title("🔍 Hierarchical Citation Explorer")
        st.markdown("""
        Explore how insights are derived from interview data through our 
        hierarchical citation system.
        """)
        
        # Sidebar navigation
        view_mode = st.sidebar.selectbox(
            "View Mode",
            ["Corpus Overview", "Pattern Deep Dive", "Interview Explorer", "Citation Validator"]
        )
        
        if view_mode == "Corpus Overview":
            self.show_corpus_overview()
        elif view_mode == "Pattern Deep Dive":
            self.show_pattern_analysis()
        elif view_mode == "Interview Explorer":
            self.show_interview_explorer()
        elif view_mode == "Citation Validator":
            self.show_citation_validator()
    
    def show_corpus_overview(self):
        """Display corpus-level insights with citations."""
        st.header("Corpus-Level Patterns")
        
        if not self.corpus_data:
            st.error("No corpus analysis data found. Run analyze_corpus_with_citations.py first.")
            return
        
        # Display pattern summary
        patterns = self.corpus_data.get('patterns', {})
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Common Priorities",
                len(patterns.get('common_priorities', []))
            )
        
        with col2:
            st.metric(
                "Emotional Patterns", 
                len(patterns.get('emotional_patterns', []))
            )
        
        with col3:
            st.metric(
                "Regional Differences",
                len(patterns.get('regional_differences', []))
            )
        
        # Pattern details
        st.subheader("Pattern Analysis")
        
        pattern_type = st.selectbox(
            "Select Pattern Type",
            list(patterns.keys())
        )
        
        if pattern_type in patterns:
            for pattern in patterns[pattern_type]:
                with st.expander(
                    f"{pattern['content']['pattern']} "
                    f"(Prevalence: {pattern['prevalence']:.1%})"
                ):
                    self.show_pattern_details(pattern)
    
    def show_pattern_details(self, pattern: Dict):
        """Show detailed view of a pattern with citations."""
        # Pattern summary
        st.write("**Pattern Details:**")
        st.json(pattern['content'])
        
        # Citation summary
        st.write("**Supporting Evidence:**")
        st.write(f"Supported by {len(pattern['supporting_interviews'])} interviews")
        
        # Sample citations
        st.write("**Sample Interview Citations:**")
        for cite in pattern['supporting_interviews'][:5]:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"Interview {cite['interview_id']}")
                st.caption(f"Contribution: {cite['contribution_note']}")
            with col2:
                st.metric("Relevance", f"{cite['relevance_score']:.2f}")
            
            # Allow drilling down
            if st.button(f"Explore Interview {cite['interview_id']}", 
                        key=f"explore_{cite['interview_id']}"):
                st.session_state['selected_interview'] = cite['interview_id']
                st.session_state['view_mode'] = "Interview Explorer"
                st.experimental_rerun()
    
    def show_interview_explorer(self):
        """Explore individual interview with citations."""
        st.header("Interview Citation Explorer")
        
        # Interview selector
        interview_id = st.selectbox(
            "Select Interview",
            options=list(self.interviews.keys()),
            index=0 if 'selected_interview' not in st.session_state else 
                  list(self.interviews.keys()).index(st.session_state['selected_interview'])
        )
        
        if interview_id:
            interview = self.interviews[interview_id]
            
            # Show interview metadata
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Location", interview.get('location', 'Unknown'))
            with col2:
                st.metric("Duration", f"{interview.get('duration', 0)} min")
            with col3:
                st.metric("Turns", len(interview.get('turns', [])))
            
            # Show insights with citation visualization
            st.subheader("Interview Insights with Citations")
            
            # Create tabs for different insight types
            tabs = st.tabs(["Priorities", "Narratives", "Emotional Arc", "Citation Map"])
            
            with tabs[0]:
                self.show_priorities_with_citations(interview)
            
            with tabs[1]:
                self.show_narratives_with_citations(interview)
            
            with tabs[2]:
                self.show_emotional_arc(interview)
                
            with tabs[3]:
                self.show_citation_map(interview)
    
    def show_citation_map(self, interview: Dict):
        """Visualize citation network for an interview."""
        st.write("**Citation Network Visualization**")
        
        # Build network graph
        G = nx.DiGraph()
        
        # Add turn nodes
        for turn in interview.get('turns', []):
            turn_id = f"turn_{turn['turn_id']}"
            G.add_node(turn_id, 
                      type='turn',
                      text=turn['text'][:50] + '...')
        
        # Add insight nodes and edges
        for insight_type in ['national_priorities', 'local_priorities']:
            insights = interview.get(insight_type, [])
            for i, insight in enumerate(insights):
                insight_id = f"{insight_type}_{i}"
                G.add_node(insight_id,
                          type='insight',
                          text=insight.get('theme', 'Unknown'))
                
                # Add citation edges
                citations = insight.get('structured_citations', {})
                for cite in citations.get('primary_citations', []):
                    G.add_edge(f"turn_{cite['turn_id']}", 
                              insight_id,
                              weight=cite['relevance_score'])
        
        # Create Plotly visualization
        pos = nx.spring_layout(G)
        
        # Create edge trace
        edge_trace = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_trace.append(go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode='lines',
                line=dict(width=2, color='#888'),
                hoverinfo='none'
            ))
        
        # Create node trace
        node_trace = go.Scatter(
            x=[pos[node][0] for node in G.nodes()],
            y=[pos[node][1] for node in G.nodes()],
            mode='markers+text',
            hoverinfo='text',
            text=[G.nodes[node].get('text', '') for node in G.nodes()],
            marker=dict(
                size=[20 if G.nodes[node]['type'] == 'insight' else 10 
                      for node in G.nodes()],
                color=['red' if G.nodes[node]['type'] == 'insight' else 'blue'
                       for node in G.nodes()]
            )
        )
        
        # Create figure
        fig = go.Figure(data=edge_trace + [node_trace],
                       layout=go.Layout(
                           title='Citation Network',
                           showlegend=False,
                           hovermode='closest',
                           margin=dict(b=0, l=0, r=0, t=40),
                           xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                       ))
        
        st.plotly_chart(fig, use_container_width=True)
    
    def show_citation_validator(self):
        """Interface for validating citations."""
        st.header("Citation Validation Tool")
        
        st.markdown("""
        This tool helps validate the quality and accuracy of citations
        throughout the system.
        """)
        
        # Validation options
        validation_mode = st.radio(
            "Validation Mode",
            ["Single Interview", "Batch Validation", "Corpus Validation"]
        )
        
        if validation_mode == "Single Interview":
            interview_id = st.selectbox(
                "Select Interview to Validate",
                options=list(self.interviews.keys())
            )
            
            if st.button("Run Validation"):
                with st.spinner("Validating citations..."):
                    report = self.validate_interview_citations(interview_id)
                    self.display_validation_report(report)
        
        elif validation_mode == "Batch Validation":
            if st.button("Validate All Interviews"):
                progress_bar = st.progress(0)
                reports = []
                
                for i, interview_id in enumerate(self.interviews.keys()):
                    report = self.validate_interview_citations(interview_id)
                    reports.append(report)
                    progress_bar.progress((i + 1) / len(self.interviews))
                
                self.display_batch_validation_summary(reports)
    
    def validate_interview_citations(self, interview_id: str) -> Dict:
        """Run validation on a single interview."""
        from src.pipeline.quality.citation_validator import CitationValidator
        
        validator = CitationValidator()
        interview = self.interviews[interview_id]
        
        # Validate interview citations
        report = validator.validate_interview_citations(
            interview,
            interview.get('turns', [])
        )
        
        return report

if __name__ == "__main__":
    explorer = CitationExplorer()
    explorer.run()
```

## Phase 5: Integration and Testing (Days 15-16)

### Step 5.1: Update Makefile

**File**: `Makefile`

Add citation-related targets:

```makefile
# Citation system targets
citation-setup: db-check
	@echo "$(YELLOW)Setting up citation system...$(NC)"
	@$(PYTHON_VENV) scripts/add_citation_tables.py
	@echo "✅ Citation tables ready"

annotate-with-citations: citation-setup
	@echo "$(BLUE)Running annotation with citation tracking...$(NC)"
	@$(PYTHON_VENV) scripts/run_citation_pipeline.py

analyze-corpus: check
	@echo "$(BLUE)Analyzing corpus with citations...$(NC)"
	@$(PYTHON_VENV) scripts/analyze_corpus_with_citations.py

citation-explorer: check
	@echo "$(GREEN)Launching Citation Explorer...$(NC)"
	@$(PYTHON_VENV) -m streamlit run src/dashboard/citation_explorer.py

validate-citations: check
	@echo "$(YELLOW)Validating all citations...$(NC)"
	@$(PYTHON_VENV) scripts/validate_all_citations.py
```

### Step 5.2: Create Integration Tests

**New File**: `tests/test_citation_system.py`

```python
"""
Test suite for hierarchical citation system.
"""
import pytest
import json
from src.pipeline.annotation.semantic_tagger import SemanticTagger
from src.pipeline.annotation.citation_tracker import CitationTracker, TurnCitation
from src.pipeline.quality.citation_validator import CitationValidator

class TestSemanticTagger:
    """Test semantic tagging functionality."""
    
    def test_extract_tags(self):
        """Test tag extraction from turn annotation."""
        tagger = SemanticTagger()
        
        turn_annotation = {
            "functional_analysis": {"primary_function": "problem_identification"},
            "content_analysis": {"topics": ["seguridad", "economía"]},
            "emotional_analysis": {"emotions_expressed": ["frustración", "preocupación"]},
            "evidence_analysis": {"evidence_type": "experiencia_personal"}
        }
        
        tags = tagger.extract_tags(turn_annotation)
        
        assert "security_concern" in tags
        assert "frustration_statement" in tags
        assert "personal_experience" in tags
    
    def test_extract_key_phrases(self):
        """Test key phrase extraction."""
        tagger = SemanticTagger()
        
        turn_text = "No puedo dormir pensando en la seguridad. Es terrible."
        turn_annotation = {
            "emotional_analysis": {"intensity": 0.8}
        }
        
        phrases = tagger.extract_key_phrases(turn_text, turn_annotation)
        
        assert len(phrases) > 0
        assert phrases[0]['importance'] > 0.5

class TestCitationTracker:
    """Test citation tracking functionality."""
    
    def test_create_citation(self):
        """Test citation creation."""
        turns = [
            {
                'turn_id': 1,
                'text': 'La seguridad es mi principal preocupación.',
                'citation_metadata': {
                    'semantic_tags': ['security_concern']
                }
            }
        ]
        
        tracker = CitationTracker(turns)
        
        insight = {
            'type': 'priority',
            'theme': 'security',
            'semantic_tags': ['security_concern']
        }
        
        citation_details = [{
            'contribution_type': 'primary_evidence',
            'quote': 'La seguridad es mi principal preocupación'
        }]
        
        citation = tracker.create_citation(insight, [1], citation_details)
        
        assert len(citation.primary_citations) == 1
        assert citation.primary_citations[0].turn_id == 1
        assert citation.primary_citations[0].relevance_score > 0.7

class TestCitationValidator:
    """Test citation validation."""
    
    def test_validate_turn_citation(self):
        """Test single turn citation validation."""
        validator = CitationValidator()
        
        citation = {
            'specific_element': 'security concern',
            'relevance_score': 0.8
        }
        
        turn_text = "My main security concern is the neighborhood."
        insight_text = "Security is a top priority"
        
        is_valid, issues = validator.validate_turn_citation(
            citation, turn_text, insight_text
        )
        
        assert is_valid
        assert len(issues) == 0
    
    def test_fuzzy_match(self):
        """Test fuzzy text matching."""
        validator = CitationValidator()
        
        quote = "security is important"
        text = "I think that security is very important for our community"
        
        score = validator._fuzzy_match(quote, text)
        
        assert score > 0.8

@pytest.mark.integration
class TestEndToEndCitation:
    """Test complete citation flow."""
    
    async def test_full_annotation_with_citations(self, sample_interview):
        """Test full annotation pipeline with citations."""
        from src.pipeline.annotation.multipass_annotator import MultiPassAnnotator
        
        annotator = MultiPassAnnotator()
        
        # Run annotation
        result = await annotator.annotate(
            sample_interview['text'],
            sample_interview['metadata']
        )
        
        # Check citations exist
        assert 'national_priorities' in result
        for priority in result['national_priorities']:
            assert 'structured_citations' in priority
            citations = priority['structured_citations']
            assert len(citations['primary_citations']) > 0
            
        # Validate citations
        validator = CitationValidator()
        report = validator.validate_interview_citations(
            result,
            result['turn_annotations']
        )
        
        assert report['insights_with_citations'] > 0
        assert len(report['issues']) == 0
```

### Step 5.3: Create Migration Guide

**New File**: `docs/CITATION_MIGRATION_GUIDE.md`

```markdown
# Citation System Migration Guide

## Overview

This guide helps migrate existing annotations to include citation support.

## For Existing Annotations

### Option 1: Re-annotate with Citations

Run the re-annotation script:
```bash
python scripts/reannotate_with_citations.py --interview-ids all
```

### Option 2: Add Citations to Existing Annotations

For annotations you want to preserve:
```bash
python scripts/add_citations_to_existing.py --interview-id INTERVIEW_123
```

## Database Migration

1. Backup your database:
```bash
cp data/uruguay_interviews.db data/uruguay_interviews_backup.db
```

2. Run migration:
```bash
python scripts/add_citation_tables.py
```

3. Verify migration:
```bash
python scripts/verify_citation_schema.py
```

## Validation

After migration, validate citations:
```bash
make validate-citations
```

## Rollback

If needed, restore from backup:
```bash
cp data/uruguay_interviews_backup.db data/uruguay_interviews.db
```
```

## Implementation Timeline

### Week 1 (Days 1-5)
- Days 1-3: Implement turn-level citation enhancements
- Days 4-5: Begin interview-level citation implementation

### Week 2 (Days 6-10)
- Days 6-7: Complete interview-level citations
- Days 8-10: Implement corpus-level analysis

### Week 3 (Days 11-16)
- Days 11-12: Build citation validation system
- Days 13-14: Create Citation Explorer UI
- Days 15-16: Integration testing and documentation

## Success Metrics

1. **Coverage**: 95%+ of insights have citations
2. **Accuracy**: 90%+ citation validation pass rate
3. **Depth**: Average 3+ turns cited per insight
4. **Performance**: <20% increase in annotation time

## Maintenance Considerations

1. **Prompt Updates**: Keep citation instructions in sync with schema
2. **Validation**: Run citation validation after each batch
3. **UI Updates**: Keep Citation Explorer in sync with schema changes
4. **Documentation**: Update examples when citation format evolves

## Conclusion

This implementation creates a robust, hierarchical citation system that provides full traceability from corpus-level insights down to individual conversation turns. The system balances automation with validation, ensuring both efficiency and accuracy in large-scale qualitative research.