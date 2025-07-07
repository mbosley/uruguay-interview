# Uruguay Interview Analysis Pipeline with MFT Integration

## Complete Pipeline Overview

```
┌─────────────────────┐
│   Raw Interviews    │
│  (.docx/.odt files) │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 1. Document Ingestion│
│  - Convert to text  │
│  - Extract metadata │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 2. Turn Detection   │
│  - Parse speakers   │
│  - Segment turns    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 3. Multi-Pass AI    │
│    Annotation       │
├─────────────────────┤
│ Pass 1: Interview   │
│  - Metadata         │
│  - Priorities       │
│  - Turn inventory   │
├─────────────────────┤
│ Pass 2: Turn Batches│
│  6 DIMENSIONS:      │
│  1. Functional      │
│  2. Content         │
│  3. Evidence        │
│  4. Emotional       │
│  5. Uncertainty     │
│  6. MFT (NEW!)      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 4. Data Storage     │
│  - SQLite Database  │
│  - 20+ tables       │
│  - MFT tables (NEW) │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 5. Visualization    │
│  - Dashboard        │
│  - HTML Reports     │
│  - MFT Analytics    │
└─────────────────────┘
```

## Detailed Pipeline Stages

### Stage 1: Document Ingestion
**Module**: `src/pipeline/ingestion/document_processor.py`
```python
# Input: data/raw/interviews/T-20250528_0900_058.docx
# Output: InterviewDocument object with text and metadata
processor = DocumentProcessor()
interview = processor.process_interview(file_path)
```

### Stage 2: Turn Detection
**Module**: `src/pipeline/parsing/conversation_parser.py`
```python
# Detects conversation turns dynamically
# Output: List of turns with speaker identification
turns = parser.parse_conversation(interview.text)
# Typical interview: 20-100 turns
```

### Stage 3: Multi-Pass AI Annotation

#### Pass 1: Interview-Level Analysis
**Module**: `src/pipeline/annotation/multipass_annotator.py`
```json
{
  "interview_analysis": {
    "metadata": {...},
    "participant_profile": {...},
    "priority_analysis": {
      "national_priorities": [3 items],
      "local_priorities": [3 items]
    },
    "narrative_features": {...}
  },
  "turn_inventory": {
    "total_turns_detected": 47,
    "turn_list": [...]
  }
}
```

#### Pass 2: Turn-Level Analysis (6 Dimensions)
**Batches**: 6 turns at a time
```json
{
  "turn_id": 15,
  "speaker": "participant",
  "text": "El gobierno nos abandonó...",
  
  // Dimension 1: Functional
  "turn_analysis": {
    "primary_function": "problem_identification",
    "function_confidence": 0.9
  },
  
  // Dimension 2: Content
  "content_analysis": {
    "topics": ["government", "abandonment"],
    "geographic_scope": ["local", "national"]
  },
  
  // Dimension 3: Evidence
  "evidence_analysis": {
    "evidence_type": "community_observation",
    "specificity": "somewhat_specific"
  },
  
  // Dimension 4: Emotional
  "emotional_analysis": {
    "emotional_valence": "negative",
    "emotional_intensity": 0.8,
    "specific_emotions": ["frustration", "abandonment"]
  },
  
  // Dimension 5: Uncertainty
  "uncertainty_tracking": {
    "coding_confidence": 0.85,
    "ambiguous_aspects": []
  },
  
  // Dimension 6: Moral Foundations (NEW!)
  "moral_foundations_analysis": {
    "reasoning": "Strong loyalty/betrayal theme...",
    "care_harm": 0.3,
    "fairness_cheating": 0.2,
    "loyalty_betrayal": 0.8,  // Dominant
    "authority_subversion": 0.1,
    "sanctity_degradation": 0.0,
    "liberty_oppression": 0.4,
    "dominant_foundation": "loyalty_betrayal",
    "foundations_narrative": "Abandonment by state...",
    "mft_confidence": 0.85
  }
}
```

### Stage 4: Database Storage
**Module**: `src/database/models.py` + `models_mft.py`

#### Core Tables (Existing)
- `interviews` - Interview metadata
- `participants` - Participant demographics
- `priorities` - National/local priorities
- `turns` - Conversation turns
- `turn_functional_analysis` - Dimension 1
- `turn_content_analysis` - Dimension 2
- `turn_evidence_analysis` - Dimension 3
- `turn_emotional_analysis` - Dimension 4
- `turn_uncertainty_tracking` - Dimension 5

#### MFT Tables (NEW)
- `turn_moral_foundations` - Dimension 6 (turn-level)
- `interview_moral_foundations` - Interview aggregates
- `moral_foundations_priorities` - MFT-priority linkage

### Stage 5: Visualization & Analysis

#### Dashboard Components
**Module**: `src/dashboard/`
1. **Conversation Browser** - Turn-by-turn with 6 dimensions
2. **MFT Analytics** (NEW)
   - Foundation distribution charts
   - Moral profile by demographics
   - Priority-foundation correlations
3. **Quote Browser** - Filtered by foundation
4. **Research Analytics** - Cross-interview patterns

#### HTML Reports
**Module**: `scripts/generate_interview_html.py`
```html
<!-- Enhanced turn display -->
<div class="turn-analysis">
  <div class="dimensions-grid">
    <div class="functional">Problem ID (0.9)</div>
    <div class="content">Government, Security</div>
    <div class="evidence">Personal Experience</div>
    <div class="emotional">Frustration (0.8)</div>
    <div class="uncertainty">High Confidence</div>
    <div class="mft">Loyalty/Betrayal (0.8)</div>
  </div>
</div>
```

## Complete Execution Flow

### 1. Run Full Pipeline
```bash
# Process all interviews with MFT
python scripts/production_annotate_all.py --include-mft

# Individual interview
python -m src.cli.annotate 058 --multipass --mft
```

### 2. Database Population
```python
# Automated by pipeline
# Stores all 6 dimensions per turn
# ~50 turns × 36 interviews = 1,800 turn analyses
# Each with 6 dimensional analyses = 10,800 data points
```

### 3. Launch Dashboard
```bash
python scripts/run_dashboard.py
# Access at http://localhost:8501
```

## Cost Analysis with MFT

### Per Interview
- **Without MFT**: ~$0.008 (5 dimensions)
- **With MFT**: ~$0.009 (6 dimensions)
- **Increase**: ~12.5% ($0.001 per interview)

### Full Dataset (36 interviews)
- **Additional cost**: ~$0.036
- **Total with MFT**: ~$0.324

## Data Schema Example

### Turn-Level Storage
```sql
-- Example: Turn 15 from Interview 058
INSERT INTO turns (id, interview_id, turn_number, speaker, text)
VALUES (427, '058', 15, 'participant', 'El gobierno nos abandonó...');

-- 6 Dimensional Analyses
INSERT INTO turn_functional_analysis (turn_id, primary_function, confidence)
VALUES (427, 'problem_identification', 0.9);

INSERT INTO turn_content_analysis (turn_id, topics)
VALUES (427, '["government", "abandonment"]');

INSERT INTO turn_evidence_analysis (turn_id, evidence_type)
VALUES (427, 'community_observation');

INSERT INTO turn_emotional_analysis (turn_id, valence, intensity)
VALUES (427, 'negative', 0.8);

INSERT INTO turn_uncertainty_tracking (turn_id, confidence)
VALUES (427, 0.85);

-- NEW: MFT Dimension
INSERT INTO turn_moral_foundations (
  turn_id, care_harm, fairness_cheating, loyalty_betrayal,
  authority_subversion, sanctity_degradation, liberty_oppression,
  dominant_foundation
) VALUES (
  427, 0.3, 0.2, 0.8, 0.1, 0.0, 0.4, 'loyalty_betrayal'
);
```

## Analysis Capabilities with MFT

### 1. Moral Profile Analysis
```python
# Average moral foundations by demographic
SELECT 
  p.age_range,
  AVG(mf.loyalty_betrayal) as avg_loyalty,
  AVG(mf.fairness_cheating) as avg_fairness
FROM interview_moral_foundations mf
JOIN participants p ON mf.interview_id = p.interview_id
GROUP BY p.age_range;
```

### 2. Priority-Foundation Correlation
```python
# Which moral foundations drive which priorities?
SELECT 
  pr.theme,
  AVG(mfp.fairness_relevance) as fairness_score,
  AVG(mfp.care_harm_relevance) as care_score
FROM priorities pr
JOIN moral_foundations_priorities mfp ON pr.id = mfp.priority_id
GROUP BY pr.theme
ORDER BY fairness_score DESC;
```

### 3. Turn Sequence Analysis
```python
# How do moral foundations evolve through conversation?
SELECT 
  t.turn_number,
  mf.dominant_foundation,
  COUNT(*) as frequency
FROM turns t
JOIN turn_moral_foundations mf ON t.id = mf.turn_id
GROUP BY t.turn_number / 10, mf.dominant_foundation;
```

## Key Insights Enabled by MFT

1. **Moral Framing of Priorities**
   - Security → Care/Harm + Authority
   - Corruption → Fairness/Cheating
   - Community decline → Loyalty/Betrayal

2. **Demographic Patterns**
   - Older participants → More Authority/Tradition
   - Urban → More Liberty/Oppression concerns
   - Rural → Stronger Loyalty/Community

3. **Emotional-Moral Connections**
   - High frustration → Fairness violations
   - Sadness → Care/Harm + Loyalty/Betrayal
   - Anger → Liberty/Oppression

## Testing MFT Implementation

```bash
# 1. Add MFT tables to database
python scripts/add_mft_tables.py

# 2. Test on single interview
python scripts/test_mft_annotation.py 058

# 3. Verify all 6 dimensions captured
python scripts/verify_mft_integration.py

# 4. Generate enhanced HTML report
python scripts/generate_interview_html.py 058 --include-mft
```

## Summary

The pipeline now captures **6 dimensions** for every conversation turn:
1. **Functional** - What the speaker is doing
2. **Content** - What topics are discussed  
3. **Evidence** - What kind of support provided
4. **Emotional** - Emotional tone and intensity
5. **Uncertainty** - Coding confidence
6. **Moral Foundations** - Which moral concerns invoked

This provides a complete analytical framework for understanding not just WHAT citizens say, but HOW they frame issues morally, adding crucial depth to policy insights.