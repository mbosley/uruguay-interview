# Citation System Architecture

## System Design

### Data Flow Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Corpus Analysis                        │
│  ┌─────────────────────────────────────────────────┐    │
│  │ Corpus Insight: "Security is top concern (73%)" │    │
│  └────────────────┬─────────────────────────────────┘    │
│                   │ cites (n=26 interviews)              │
└───────────────────┼─────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────┐
│                Interview Analysis                        │
│  ┌─────────────────────────────────────────────────┐    │
│  │ Priority: "Neighborhood security" (intensity=0.8)│    │
│  └────────────────┬─────────────────────────────────┘    │
│                   │ cites (turns: 3,7,15)               │
└───────────────────┼─────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────┐
│                  Turn Analysis                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │Turn 7: "I can't sleep worrying about break-ins" │    │
│  │Tags: [security_concern, fear_expression]        │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### Component Architecture

```
src/
├── pipeline/
│   └── annotation/
│       ├── multipass_annotator.py      [Modified: Citation-aware]
│       ├── json_annotator.py           [Modified: Citation output]
│       ├── semantic_tagger.py          [NEW: Tag extraction]
│       └── citation_tracker.py         [NEW: Citation management]
│
├── database/
│   └── models.py                       [Modified: Citation tables]
│       ├── TurnCitationMetadata        [NEW]
│       └── InterviewInsightCitation    [NEW]
│
├── analysis/
│   └── corpus_citation.py              [NEW: Corpus-level citations]
│
├── pipeline/quality/
│   └── citation_validator.py           [NEW: Citation validation]
│
└── dashboard/
    └── citation_explorer.py            [NEW: Citation UI]
```

## Database Schema

### Citation Tables

```sql
-- Turn-level citation metadata
CREATE TABLE turn_citation_metadata (
    id INTEGER PRIMARY KEY,
    turn_id INTEGER NOT NULL REFERENCES turns(id),
    semantic_tags JSON,              -- ["security_concern", "fear_expression"]
    key_phrases JSON,                -- [{"text": "...", "importance": 0.9}]
    quotable_segments JSON,          -- [{"text": "...", "start": 0, "end": 50}]
    context_dependency FLOAT,        -- 0.0-1.0
    standalone_clarity FLOAT         -- 0.0-1.0
);

-- Interview insight citations
CREATE TABLE interview_insight_citations (
    id INTEGER PRIMARY KEY,
    interview_id VARCHAR NOT NULL REFERENCES interviews(id),
    insight_type VARCHAR NOT NULL,   -- 'priority', 'narrative', etc.
    insight_id VARCHAR NOT NULL,
    citation_data JSON,              -- Full citation structure
    primary_turn_ids JSON,           -- Quick access: [3, 7]
    supporting_turn_ids JSON,        -- Quick access: [12, 15, 23]
    confidence_score FLOAT
);

-- Corpus insight citations (optional, could be JSON)
CREATE TABLE corpus_insight_citations (
    id INTEGER PRIMARY KEY,
    corpus_analysis_id VARCHAR,
    insight_id VARCHAR NOT NULL,
    insight_type VARCHAR,
    supporting_interview_ids JSON,   -- ["INT_001", "INT_002", ...]
    prevalence FLOAT,
    citation_chain JSON              -- Full hierarchical chain
);
```

## Citation Data Structures

### Turn Citation Metadata
```json
{
  "turn_id": 7,
  "semantic_tags": [
    "security_concern",
    "fear_expression",
    "personal_experience"
  ],
  "key_phrases": [
    {
      "text": "I can't sleep worrying about break-ins",
      "start_char": 0,
      "end_char": 38,
      "importance": 0.9
    }
  ],
  "quotable_segments": [
    {
      "text": "can't sleep worrying",
      "start_char": 2,
      "end_char": 22,
      "importance": 0.85
    }
  ],
  "context_dependency": 0.3,
  "standalone_clarity": 0.8
}
```

### Interview Insight Citation
```json
{
  "insight_type": "national_priority",
  "insight_id": "security_1",
  "primary_citations": [
    {
      "turn_id": 7,
      "contribution_type": "primary_evidence",
      "relevance_score": 0.9,
      "specific_element": "I can't sleep worrying about break-ins",
      "semantic_match": ["security_concern", "fear_expression"]
    }
  ],
  "supporting_citations": [
    {
      "turn_id": 15,
      "contribution_type": "contextual",
      "relevance_score": 0.7,
      "specific_element": "whole neighborhood feels unsafe",
      "semantic_match": ["security_concern", "community_observation"]
    }
  ],
  "synthesis_note": "Security concern expressed through personal impact (turn 7) and community validation (turn 15)",
  "confidence": 0.85
}
```

### Corpus Insight Citation
```json
{
  "insight_id": "pattern_security_prevalence",
  "insight_type": "common_priority",
  "content": {
    "pattern": "Security is top concern in urban areas",
    "prevalence": 0.73,
    "geographic_concentration": "Montevideo and Canelones"
  },
  "supporting_interviews": [
    {
      "interview_id": "INT_001",
      "insight_type": "national_priority",
      "insight_id": "security_1",
      "relevance_score": 0.9,
      "contribution_note": "Strong security priority with high emotional intensity"
    }
  ],
  "confidence": 0.88,
  "regional_variation": {
    "Montevideo": 0.81,
    "Canelones": 0.75,
    "Rural": 0.42
  }
}
```

## API Flow

### Annotation with Citations

```python
# 1. Annotate turns with citation metadata
turn_annotations = []
for turn in interview.turns:
    annotation = annotate_turn(turn)
    annotation['citation_metadata'] = extract_citation_metadata(turn, annotation)
    turn_annotations.append(annotation)

# 2. Generate interview insights with turn citations
interview_insights = generate_interview_insights(
    interview_text,
    turn_annotations,
    require_citations=True
)

# 3. Validate citations
validated_insights = validate_citations(interview_insights, turn_annotations)

# 4. Store with citation links
store_interview_with_citations(interview, validated_insights)
```

### Citation Retrieval

```python
# Get full citation chain for a corpus insight
def get_citation_chain(corpus_insight_id):
    corpus_insight = get_corpus_insight(corpus_insight_id)
    
    chains = []
    for interview_cite in corpus_insight.supporting_interviews:
        interview_insight = get_interview_insight(
            interview_cite.interview_id,
            interview_cite.insight_id
        )
        
        turn_texts = []
        for turn_cite in interview_insight.primary_citations:
            turn = get_turn(turn_cite.turn_id)
            turn_texts.append({
                'turn_id': turn.id,
                'text': turn.text,
                'quote': turn_cite.specific_element
            })
        
        chains.append({
            'interview': interview_cite.interview_id,
            'insight': interview_insight.content,
            'supporting_turns': turn_texts
        })
    
    return chains
```

## Performance Considerations

### Token Usage
- Turn annotation: +15% tokens for citation metadata
- Interview annotation: +20% tokens for citation requirements
- Total increase: ~18% in API costs

### Storage Impact
- Turn metadata: ~500 bytes per turn
- Interview citations: ~2KB per interview
- Corpus citations: ~5KB per pattern
- Total: ~30% increase in database size

### Processing Time
- Turn annotation: +10% for tag extraction
- Interview annotation: +15% for citation generation
- Validation: +5% for citation checking
- Total: ~20% increase in processing time

## Quality Assurance

### Citation Quality Metrics

1. **Coverage**: % of insights with citations
2. **Depth**: Average citations per insight
3. **Accuracy**: % of valid citations
4. **Diversity**: Citation distribution across interview

### Validation Rules

1. **Existence**: Cited turns must exist
2. **Relevance**: Semantic alignment required
3. **Accuracy**: Quotes must match (fuzzy allowed)
4. **Completeness**: Primary evidence required

## Security Considerations

1. **No PII in Citations**: Ensure quotes don't expose participant identity
2. **Access Control**: Citation chains respect interview permissions
3. **Audit Trail**: Track who accesses citation chains
4. **Data Minimization**: Only store necessary citation data

## Future Enhancements

1. **ML-Powered Citation**: Train model to suggest citations
2. **Citation Strength Learning**: Learn optimal relevance scoring
3. **Cross-Corpus Citations**: Link insights across studies
4. **Real-time Validation**: Validate during annotation
5. **Citation Analytics**: Analyze citation patterns