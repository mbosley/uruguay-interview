# Database Schema Revision Analysis

## Current JSON Structure vs Database Schema

### Rich Data We're NOT Capturing

#### 1. **Comprehensive Participant Profiles**
**JSON provides:**
```json
"participant_profile": {
  "age_range": "50-64",
  "gender": "female", 
  "occupation_sector": "agriculture",
  "organizational_affiliation": "Aparcería Los amigos de Young",
  "self_described_political_stance": null,
  "profile_confidence": 0.8,
  "profile_notes": "Detailed context"
}
```

**Current schema:** Only basic `DemographicIndicator` table with limited fields.

#### 2. **Narrative Features Analysis**
**JSON provides:**
```json
"narrative_features": {
  "dominant_frame": "stagnation",
  "frame_narrative": "Community perceives stagnation...",
  "temporal_orientation": "present_focused", 
  "agency_attribution": {
    "government_responsibility": 0.8,
    "individual_responsibility": 0.4,
    "structural_factors": 0.9
  },
  "cultural_patterns_identified": ["community_resilience", "bureaucratic_frustration"]
}
```

**Current schema:** No representation at all.

#### 3. **Rich Turn-by-Turn Analysis**
**JSON provides 5-dimensional analysis per turn:**
```json
"turns": [{
  "turn_analysis": {
    "reasoning": "Detailed chain-of-thought...",
    "primary_function": "question",
    "secondary_functions": ["elicitation", "problem_identification"],
    "function_confidence": 0.9
  },
  "content_analysis": {
    "topics": ["public policy", "social priorities"],
    "geographic_scope": ["national"],
    "temporal_reference": "present"
  },
  "evidence_analysis": {
    "evidence_type": "personal_experience",
    "specificity": "very_specific"
  },
  "emotional_analysis": {
    "emotional_valence": "negative",
    "emotional_intensity": 0.7,
    "specific_emotions": ["frustration", "concern"]
  },
  "uncertainty_tracking": {
    "coding_confidence": 0.85,
    "alternative_interpretations": ["Other valid readings..."]
  }
}]
```

**Current schema:** Basic turn tables with minimal analysis depth.

#### 4. **Key Narratives**
**JSON provides:**
```json
"key_narratives": {
  "identity_narrative": "How participant positions themselves...",
  "problem_narrative": "Core story about what's wrong...", 
  "hope_narrative": "What gives them hope...",
  "memorable_quotes": ["striking quote 1", "key quote 2"],
  "rhetorical_strategies": ["metaphors used", "comparison patterns"]
}
```

**Current schema:** No representation.

#### 5. **Interview Dynamics**
**JSON provides:**
```json
"interview_dynamics": {
  "rapport": "excellent",
  "participant_engagement": "highly_engaged",
  "coherence": "highly_coherent",
  "interviewer_effects": "Notable influence..."
}
```

**Current schema:** Basic conversation dynamics, missing qualitative assessments.

#### 6. **Processing Intelligence**
**JSON provides:**
```json
"processing_metadata": {
  "total_api_calls": 4,
  "api_call_breakdown": [...],
  "turn_coverage": {
    "coverage_percentage": 100,
    "analyzed_turns": 15,
    "total_turns": 15
  }
}
```

**Current schema:** Basic processing logs, missing detailed analytics.

## Recommended Schema Revisions

### Strategy: Evolutionary Enhancement

1. **Maintain Backward Compatibility**
   - Keep existing tables functional
   - Add new tables for rich analytics
   - Use feature flags for migration

2. **Add Comprehensive Analytics Tables**
   - Capture full JSON richness
   - Enable sophisticated research queries
   - Support dashboard visualizations

3. **Optimize for Research Use Cases**
   - Cross-interview pattern analysis
   - Longitudinal narrative tracking
   - Cultural pattern identification
   - Quality assurance monitoring

### Priority 1: Core Analytics Tables

#### Enhanced Participant Profiles
```sql
CREATE TABLE participant_profiles (
    id SERIAL PRIMARY KEY,
    interview_id INTEGER REFERENCES interviews(id),
    age_range VARCHAR(20),
    gender VARCHAR(20),
    occupation_sector VARCHAR(50),
    organizational_affiliation TEXT,
    political_stance TEXT,
    profile_confidence FLOAT,
    profile_notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Narrative Features
```sql
CREATE TABLE narrative_features (
    id SERIAL PRIMARY KEY,
    interview_id INTEGER REFERENCES interviews(id),
    dominant_frame VARCHAR(20), -- decline, progress, stagnation, mixed
    frame_narrative TEXT,
    temporal_orientation VARCHAR(20),
    temporal_narrative TEXT,
    government_responsibility FLOAT,
    individual_responsibility FLOAT,
    structural_factors FLOAT,
    agency_narrative TEXT,
    solution_orientation VARCHAR(20),
    solution_narrative TEXT,
    cultural_patterns JSONB,
    narrative_confidence FLOAT
);
```

#### Key Narratives
```sql
CREATE TABLE key_narratives (
    id SERIAL PRIMARY KEY,
    interview_id INTEGER REFERENCES interviews(id),
    identity_narrative TEXT,
    problem_narrative TEXT,
    hope_narrative TEXT,
    memorable_quotes JSONB,
    rhetorical_strategies JSONB,
    narrative_confidence FLOAT
);
```

### Priority 2: Enhanced Turn Analysis

#### Turn Analysis Enhancement
```sql
CREATE TABLE turn_reasoning (
    id SERIAL PRIMARY KEY,
    turn_id INTEGER REFERENCES turns(id),
    analysis_reasoning TEXT,
    function_reasoning TEXT,
    content_reasoning TEXT,
    evidence_reasoning TEXT,
    emotional_reasoning TEXT
);

CREATE TABLE turn_uncertainty (
    id SERIAL PRIMARY KEY,
    turn_id INTEGER REFERENCES turns(id),
    coding_confidence FLOAT,
    ambiguous_aspects JSONB,
    edge_case_flag BOOLEAN,
    alternative_interpretations JSONB,
    resolution_strategy VARCHAR(50),
    annotator_notes TEXT
);
```

### Priority 3: Interview Quality Metrics

#### Quality Assessment
```sql
CREATE TABLE annotation_quality (
    id SERIAL PRIMARY KEY,
    interview_id INTEGER REFERENCES interviews(id),
    annotation_completeness FLOAT,
    turn_coverage_percentage FLOAT,
    analyzed_turns INTEGER,
    expected_turns INTEGER,
    processing_approach VARCHAR(50),
    all_turns_analyzed BOOLEAN,
    overall_quality_score FLOAT
);
```

### Priority 4: Processing Intelligence

#### Enhanced Processing Metadata
```sql
CREATE TABLE processing_analytics (
    id SERIAL PRIMARY KEY,
    interview_id INTEGER REFERENCES interviews(id),
    model_name VARCHAR(100),
    annotation_approach VARCHAR(50),
    total_api_calls INTEGER,
    api_call_breakdown JSONB,
    total_cost DECIMAL(10,6),
    processing_time_seconds FLOAT,
    turn_coverage JSONB,
    overall_confidence FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Implementation Plan

### Phase 1: Core Enhancement (Week 1)
- Add participant profiles table
- Add narrative features table
- Add key narratives table
- Update extraction pipeline

### Phase 2: Turn Analysis Enhancement (Week 2)
- Enhance turn tables with reasoning
- Add uncertainty tracking
- Add emotional analysis depth
- Update turn extraction logic

### Phase 3: Quality & Processing (Week 3)
- Add quality assessment tables
- Add processing analytics
- Create research query views
- Build dashboard data models

### Phase 4: Migration & Optimization (Week 4)
- Migrate existing data
- Optimize queries for research
- Create analytical views
- Performance testing

## Research Benefits

### Enabled Analyses
1. **Cross-Interview Pattern Analysis**
   - Cultural pattern tracking across regions
   - Narrative frame evolution over time
   - Agency attribution patterns

2. **Quality Assurance Analytics** 
   - Turn coverage analysis
   - Confidence score distributions
   - Processing cost optimization

3. **Sophisticated Research Queries**
   - "Find all participants with 'decline' narrative frame"
   - "Analyze agency attribution by occupation sector"
   - "Track memorable quotes by cultural patterns"

4. **Dashboard Enhancements**
   - Narrative feature distributions
   - Processing quality metrics
   - Cultural pattern heat maps

## Conclusion

The revised schema will capture the full analytical richness of our JSON annotations while maintaining research-grade data organization and query performance.