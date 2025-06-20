# Analysis of HTML Generator: Inferences vs. Strict Data

## Features Added Beyond Strict JSON Data

### 1. **Hardcoded Key Turns** ❌ INFERENCE
```python
self.key_turns = {1, 2, 3, 18, 19, 31, 35, 36, 44, 47}
```
- I manually selected these as "key moments" based on reading the interview
- This is NOT in the JSON annotation data
- Should be derived from annotation confidence scores or turn significance

### 2. **Speaker Classification** ✅ REASONABLE INFERENCE
```python
is_interviewer = any(name in speaker.upper() for name in ['GERMÁN', 'GABRIELA', 'BUSCH', 'MEDINA', 'GM', 'GB'])
```
- The JSON doesn't explicitly mark interviewer vs participant
- This is a reasonable inference based on known interviewer names
- Could be made more robust by checking interview metadata

### 3. **Display Speaker Normalization** ❌ ARBITRARY
```python
if speaker == 'María Herlinda Ferret':
    display_speaker = 'PARTICIPANT'
```
- Changed actual names to generic labels
- This loses information from the original data
- Should preserve actual speaker names

### 4. **Text Emphasis** ❌ HARDCODED
```python
if "falta de dinero" in text:
    text = text.replace("Todo eso es a raíz de la falta de dinero", 
                      '<span class="emphasis">Todo eso es a raíz de la falta de dinero</span>')
```
- Hardcoded specific phrases to emphasize
- Should derive from annotation data (e.g., memorable_quotes, high emotional intensity)

### 5. **Transcript Merging Logic** ✅ NECESSARY
- Merging consecutive turns from same speaker
- This addresses transcript format issues, not adding interpretation

### 6. **Default Fallbacks** ✅ GOOD PRACTICE
```python
priorities or ["Elderly Care Capacity", "Youth Drug Prevention", ...]
```
- Provides fallbacks when data is missing
- Clearly identifiable as defaults

### 7. **Visual Design Choices** ✅ PRESENTATION ONLY
- CSS styling, colors, layout
- Expand/collapse functionality
- These are UI decisions, not data interpretation

## Data Strictly from JSON

### ✅ Preserved from Annotations:
1. All 5 turn-level analysis dimensions
2. Confidence scores
3. Reasoning text
4. Topics, emotions, evidence types
5. Interview metadata
6. Priority rankings
7. Narrative features
8. Analytical synthesis

## Recommendations for Generic Version

To make this work for all interviews without manual intervention:

1. **Replace hardcoded key turns with dynamic selection:**
```python
# Select turns with high significance or confidence
key_turns = set()
for turn in turns:
    significance = turn.get('turn_significance', '')
    confidence = turn.get('turn_analysis', {}).get('function_confidence', 0)
    if confidence > 0.9 or 'key' in significance.lower():
        key_turns.add(turn['turn_id'])
```

2. **Use annotation data for emphasis:**
```python
# Use memorable_quotes from key_narratives
memorable_quotes = annotation_data.get('key_narratives', {}).get('memorable_quotes', [])
for quote in memorable_quotes:
    if quote in text:
        text = text.replace(quote, f'<span class="emphasis">{quote}</span>')
```

3. **Preserve actual speaker names:**
```python
display_speaker = speaker  # Keep original names
```

4. **Dynamic speaker classification:**
```python
# Use interview metadata to identify interviewers
interviewer_ids = metadata.get('interviewer_ids', [])
is_interviewer = any(interviewer in speaker for interviewer in interviewer_ids)
```

## Conclusion

The HTML generator adds several inferences and arbitrary choices:
- Hardcoded key turns (should be data-driven)
- Hardcoded emphasis phrases (should use memorable_quotes)
- Generic speaker labels (loses information)

For a production version that works across all interviews, these should be replaced with data-driven logic using the annotation JSON structure.