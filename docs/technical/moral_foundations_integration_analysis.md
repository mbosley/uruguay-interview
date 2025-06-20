# Moral Foundations Theory Integration Analysis

## Overview
Adding Moral Foundations Theory (MFT) annotation would provide insight into the moral reasoning patterns citizens use when discussing priorities and problems.

## The 6 Moral Foundations
1. **Care/Harm** - Compassion for vulnerable, preventing suffering
2. **Fairness/Cheating** - Proportionality, justice, reciprocity
3. **Loyalty/Betrayal** - Group cohesion, patriotism, self-sacrifice
4. **Authority/Subversion** - Respect for tradition, hierarchy, leadership
5. **Sanctity/Degradation** - Purity, contamination, sacred values
6. **Liberty/Oppression** - Freedom from domination, autonomy

## Implementation Complexity: MODERATE-HIGH

### 1. Annotation Schema Changes (MODERATE)

```xml
<!-- Add to annotation-prompt-en.xml -->
<turn_level_analysis>
  <!-- Existing 5 dimensions... -->
  
  <moral_foundations_analysis>
    <instruction>
      Identify which moral foundations are activated in this turn.
      Consider both explicit moral language and implicit moral reasoning.
    </instruction>
    
    <foundations_present type="list">
      <care_harm>
        <present type="boolean"/>
        <intensity type="float" min="0" max="1"/>
        <manifestation type="text">How this foundation appears</manifestation>
      </care_harm>
      <!-- Repeat for all 6 foundations -->
    </foundations_present>
    
    <dominant_foundation type="string">
      Primary moral foundation if clear
    </dominant_foundation>
    
    <moral_framing type="text">
      How moral concerns shape the argument
    </moral_framing>
  </moral_foundations_analysis>
</turn_level_analysis>
```

### 2. Database Schema Changes (EASY)

```sql
-- New table for turn-level moral foundations
CREATE TABLE turn_moral_foundations (
    id INTEGER PRIMARY KEY,
    turn_id INTEGER NOT NULL,
    interview_id INTEGER NOT NULL,  -- Direct link!
    
    -- Foundation presence and intensity
    care_harm_present BOOLEAN DEFAULT FALSE,
    care_harm_intensity FLOAT,
    care_harm_manifestation TEXT,
    
    fairness_cheating_present BOOLEAN DEFAULT FALSE,
    fairness_cheating_intensity FLOAT,
    fairness_cheating_manifestation TEXT,
    
    loyalty_betrayal_present BOOLEAN DEFAULT FALSE,
    loyalty_betrayal_intensity FLOAT,
    loyalty_betrayal_manifestation TEXT,
    
    authority_subversion_present BOOLEAN DEFAULT FALSE,
    authority_subversion_intensity FLOAT,
    authority_subversion_manifestation TEXT,
    
    sanctity_degradation_present BOOLEAN DEFAULT FALSE,
    sanctity_degradation_intensity FLOAT,
    sanctity_degradation_manifestation TEXT,
    
    liberty_oppression_present BOOLEAN DEFAULT FALSE,
    liberty_oppression_intensity FLOAT,
    liberty_oppression_manifestation TEXT,
    
    dominant_foundation VARCHAR(50),
    moral_framing TEXT,
    
    FOREIGN KEY (turn_id) REFERENCES turns(id),
    FOREIGN KEY (interview_id) REFERENCES interviews(id)
);

-- Interview-level aggregation
CREATE TABLE interview_moral_foundations_summary (
    id INTEGER PRIMARY KEY,
    interview_id INTEGER NOT NULL,
    
    -- Aggregate scores (sum of intensities / number of turns)
    care_harm_score FLOAT,
    fairness_cheating_score FLOAT,
    loyalty_betrayal_score FLOAT,
    authority_subversion_score FLOAT,
    sanctity_degradation_score FLOAT,
    liberty_oppression_score FLOAT,
    
    -- Counts
    care_harm_mentions INTEGER,
    fairness_cheating_mentions INTEGER,
    loyalty_betrayal_mentions INTEGER,
    authority_subversion_mentions INTEGER,
    sanctity_degradation_mentions INTEGER,
    liberty_oppression_mentions INTEGER,
    
    -- Analysis
    primary_foundation VARCHAR(50),
    secondary_foundation VARCHAR(50),
    moral_profile_narrative TEXT,
    
    FOREIGN KEY (interview_id) REFERENCES interviews(id)
);
```

### 3. Annotation Engine Updates (MODERATE)

```python
# In src/pipeline/annotation/annotation_engine.py

def analyze_moral_foundations(self, text: str, context: dict) -> dict:
    """Analyze moral foundations in turn text."""
    
    # Keywords/patterns for each foundation
    FOUNDATION_INDICATORS = {
        'care_harm': [
            'suffering', 'vulnerable', 'protect', 'care', 'hurt',
            'children', 'elderly', 'sick', 'help', 'compassion'
        ],
        'fairness_cheating': [
            'fair', 'equal', 'justice', 'deserve', 'rights',
            'corrupt', 'cheat', 'proportional', 'merit'
        ],
        'loyalty_betrayal': [
            'community', 'together', 'unite', 'patriot', 'betray',
            'solidarity', 'team', 'family', 'nation'
        ],
        'authority_subversion': [
            'respect', 'tradition', 'leader', 'law', 'order',
            'chaos', 'rebel', 'hierarchy', 'obey'
        ],
        'sanctity_degradation': [
            'pure', 'clean', 'sacred', 'contaminate', 'disgust',
            'moral', 'degraded', 'corrupt', 'holy'
        ],
        'liberty_oppression': [
            'freedom', 'liberty', 'oppress', 'control', 'autonomy',
            'independent', 'dominate', 'choice', 'constrain'
        ]
    }
    
    # Enhanced prompt for Gemini
    prompt = f"""
    Analyze the moral foundations present in this turn:
    
    Text: {text}
    Context: {context}
    
    For each moral foundation, identify:
    1. Is it present? (boolean)
    2. How strongly? (0-1 intensity)
    3. How does it manifest?
    
    Foundations to analyze:
    - Care/Harm: Concern for suffering, vulnerability
    - Fairness/Cheating: Justice, proportionality, rights
    - Loyalty/Betrayal: Group cohesion, solidarity
    - Authority/Subversion: Respect for hierarchy, tradition
    - Sanctity/Degradation: Purity, contamination concerns
    - Liberty/Oppression: Freedom from domination
    
    Be sensitive to cultural context - moral language may be indirect.
    """
    
    return self._query_llm(prompt)
```

### 4. Processing Pipeline Updates (MODERATE)

```python
# Add to batch processing
def process_moral_foundations_batch(self, turns_data: list) -> dict:
    """Process moral foundations for all turns."""
    
    # Parallel processing for efficiency
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for turn in turns_data:
            future = executor.submit(
                self.analyze_moral_foundations,
                turn['text'],
                turn['context']
            )
            futures.append((turn['turn_id'], future))
    
    # Aggregate results
    results = {}
    for turn_id, future in futures:
        results[turn_id] = future.result()
    
    return results

def aggregate_moral_foundations(self, turn_results: dict) -> dict:
    """Aggregate moral foundations at interview level."""
    
    foundation_scores = defaultdict(lambda: {'sum': 0, 'count': 0})
    
    for turn_id, mf_data in turn_results.items():
        for foundation in FOUNDATIONS:
            if mf_data[f'{foundation}_present']:
                intensity = mf_data[f'{foundation}_intensity']
                foundation_scores[foundation]['sum'] += intensity
                foundation_scores[foundation]['count'] += 1
    
    # Calculate average intensities
    summary = {}
    for foundation, scores in foundation_scores.items():
        if scores['count'] > 0:
            summary[f'{foundation}_score'] = scores['sum'] / len(turn_results)
            summary[f'{foundation}_mentions'] = scores['count']
        else:
            summary[f'{foundation}_score'] = 0
            summary[f'{foundation}_mentions'] = 0
    
    # Identify primary/secondary
    ranked = sorted(
        [(f, summary[f'{f}_score']) for f in FOUNDATIONS],
        key=lambda x: x[1],
        reverse=True
    )
    
    summary['primary_foundation'] = ranked[0][0] if ranked[0][1] > 0 else None
    summary['secondary_foundation'] = ranked[1][0] if ranked[1][1] > 0 else None
    
    return summary
```

### 5. HTML Visualization Updates (EASY)

```python
# Add to turn annotation display
def _build_moral_foundation_annotation(self, mf_data: dict) -> str:
    """Build moral foundations visualization."""
    
    active_foundations = []
    for foundation in ['care_harm', 'fairness_cheating', 'loyalty_betrayal', 
                      'authority_subversion', 'sanctity_degradation', 'liberty_oppression']:
        if mf_data.get(f'{foundation}_present'):
            intensity = mf_data.get(f'{foundation}_intensity', 0)
            name = foundation.replace('_', '/').title()
            active_foundations.append((name, intensity))
    
    if not active_foundations:
        return ''
    
    # Sort by intensity
    active_foundations.sort(key=lambda x: x[1], reverse=True)
    
    html = '''
    <div class="annotation-dimension moral-foundations">
        <div class="dimension-label">
            <span class="dimension-icon">⚖️</span>
            MORAL FOUNDATIONS
        </div>
        <div class="dimension-content">
    '''
    
    for foundation, intensity in active_foundations:
        html += f'''
            <div class="foundation-item">
                <span class="foundation-name">{foundation}</span>
                <div class="intensity-bar">
                    <div class="intensity-fill" style="width: {intensity*100}%"></div>
                </div>
            </div>
        '''
    
    html += '''
        </div>
    </div>
    '''
    
    return html

# Add interview-level moral profile visualization
def generate_moral_profile_chart(self, summary: dict) -> str:
    """Generate radar chart or bar chart for moral profile."""
    # Could use Chart.js or simple CSS bars
    pass
```

## Challenges & Considerations

### 1. **Annotation Complexity**
- Already have 5 dimensions per turn
- Adding 6th increases cognitive load
- Need clear guidelines for coders

### 2. **Cultural Sensitivity**
- Moral foundations may manifest differently in Uruguayan context
- Need to adapt indicators for local expressions
- Authority might relate to state/bureaucracy differently

### 3. **Multiple Foundations**
- Single turn often activates multiple foundations
- Need to handle overlap (e.g., protecting children = Care + Loyalty)
- Intensity scoring is subjective

### 4. **Computational Cost**
- 6 more sub-analyses per turn
- For 790 turns across 36 interviews = 4,740 additional API calls
- Roughly $50-100 additional cost

### 5. **Validation Challenges**
- MFT coding typically requires training
- Inter-rater reliability important
- May need pilot testing

## Implementation Phases

### Phase 1: Pilot (1-2 interviews)
1. Update annotation prompt
2. Test with single interview
3. Validate results with manual review
4. Refine indicators

### Phase 2: Database & Pipeline
1. Add database tables
2. Update annotation engine
3. Add aggregation logic
4. Test batch processing

### Phase 3: Full Dataset
1. Process all 36 interviews
2. Add to HTML visualization
3. Create aggregate analyses
4. Generate insights report

### Phase 4: Analysis
1. Which foundations dominate discussions?
2. Do different demographics emphasize different foundations?
3. How do moral frames relate to priorities?
4. Urban vs rural moral emphasis?

## Example Output

```json
{
  "turn_id": 42,
  "moral_foundations": {
    "care_harm_present": true,
    "care_harm_intensity": 0.8,
    "care_harm_manifestation": "Deep concern for elderly lacking care",
    
    "fairness_cheating_present": true,
    "fairness_cheating_intensity": 0.6,
    "fairness_cheating_manifestation": "Government should provide equal services",
    
    "authority_subversion_present": true,
    "authority_subversion_intensity": 0.3,
    "authority_subversion_manifestation": "Criticism of bureaucratic failures",
    
    "dominant_foundation": "care_harm",
    "moral_framing": "Frames elderly care as moral imperative based on vulnerability"
  }
}
```

## Recommendation

**Difficulty: MODERATE-HIGH** but absolutely doable.

The main challenges are:
1. Annotation quality (needs clear guidelines)
2. Computational cost (significant but manageable)
3. Cultural adaptation (important for validity)

The payoff would be significant - understanding the moral reasoning patterns would provide deep insight into how citizens frame political priorities and could reveal important cultural differences in moral emphasis.

I'd recommend starting with a pilot on 2-3 interviews to validate the approach before scaling up.