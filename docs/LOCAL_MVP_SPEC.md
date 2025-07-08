# Local MVP: Citation-Aware Search Tool (1-2 Week Build)

## Overview

A lightweight, locally-hosted research tool that lets AI assistants (like Claude) search the Uruguay interviews using the existing citation system. No cloud services, minimal dependencies, immediate value.

## Core Principle

**"Make the existing citation system searchable via natural language"**

## What We Already Have (Ready to Use)

1. **Complete Citation Database**
   - 37 interviews fully annotated with 4-pass pipeline
   - Turn-level semantic tags and citations
   - Interview-level insights with citation chains
   - PostgreSQL database with all relationships

2. **Semantic Tags** (Our "Poor Man's Embeddings")
   ```python
   # Already extracted and stored:
   - security_concern, economic_worry, health_anxiety
   - hope_expression, frustration_statement, fear_articulation
   - personal_experience, community_observation
   - policy_proposal, individual_action
   ```

## MVP Architecture (All Local)

```
┌─────────────────────────────────────────┐
│         Simple Web Interface            │
│    (FastAPI + Basic HTML/HTMX)         │
└────────────────────┬────────────────────┘
                     │
┌────────────────────┴────────────────────┐
│          Search Engine                   │
│   (Tag matching + Text search)          │
└────────────────────┬────────────────────┘
                     │
┌────────────────────┴────────────────────┐
│      Existing PostgreSQL DB             │
│  (Citations, tags, full text)          │
└─────────────────────────────────────────┘
```

## Implementation Plan (5-7 Days)

### Day 1-2: Basic Search API

```python
# src/mvp/search_api.py
from fastapi import FastAPI
from sqlalchemy import or_, and_
import json

app = FastAPI()

@app.post("/search")
async def search(query: str, filters: dict = None):
    """
    Simple but effective search without embeddings.
    """
    # 1. Extract likely tags from query
    query_lower = query.lower()
    likely_tags = []
    
    TAG_KEYWORDS = {
        'security': ['security', 'crime', 'safety', 'violence', 'robbery'],
        'employment': ['work', 'job', 'employment', 'unemployment'],
        'health': ['health', 'medical', 'doctor', 'hospital'],
        # ... etc
    }
    
    for tag, keywords in TAG_KEYWORDS.items():
        if any(kw in query_lower for kw in keywords):
            likely_tags.append(f"{tag}_concern")
    
    # 2. Search by tags + text
    results = db.query(Turn).filter(
        or_(
            Turn.semantic_tags.overlap(likely_tags),
            Turn.text.ilike(f"%{query}%")
        )
    ).limit(50).all()
    
    # 3. Return with citations
    return format_results_with_citations(results)

@app.post("/summarize")
async def summarize_theme(topic: str, max_results: int = 20):
    """
    Get a summary of what people say about a topic.
    """
    # Use existing citation chains
    relevant_insights = db.query(InterviewInsight).filter(
        InterviewInsight.theme.ilike(f"%{topic}%")
    ).all()
    
    # Aggregate and return
    return {
        "topic": topic,
        "summary": generate_summary(relevant_insights),
        "supporting_quotes": get_supporting_quotes(relevant_insights),
        "prevalence": f"{len(relevant_insights)}/{total_interviews}"
    }
```

### Day 2-3: Query Enhancement

```python
# src/mvp/query_enhancer.py
class SimpleQueryEnhancer:
    """
    Expand queries using domain knowledge, no LLM needed.
    """
    
    SYNONYMS = {
        'seguridad': ['security', 'crime', 'safety', 'police', 'violence'],
        'trabajo': ['work', 'employment', 'job', 'unemployment', 'salary'],
        'jóvenes': ['youth', 'young people', 'teenagers', 'young adults'],
        # Uruguay-specific terms
        'pasta base': ['drugs', 'addiction', 'substance abuse'],
        'asentamiento': ['informal settlement', 'slum', 'poor neighborhood']
    }
    
    def enhance_query(self, query: str) -> dict:
        """
        Return enhanced search parameters.
        """
        tokens = query.lower().split()
        
        # Expand with synonyms
        expanded_terms = []
        for token in tokens:
            expanded_terms.append(token)
            if token in self.SYNONYMS:
                expanded_terms.extend(self.SYNONYMS[token])
        
        # Detect filters
        filters = self.extract_filters(query)
        
        return {
            'original': query,
            'expanded_terms': expanded_terms,
            'filters': filters,
            'search_strategy': self.determine_strategy(query)
        }
```

### Day 3-4: Local Embeddings (Optional but Powerful)

```python
# src/mvp/local_embeddings.py
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

class LocalEmbeddingSearch:
    """
    Use small, fast model that runs on CPU.
    """
    
    def __init__(self):
        # 22M parameter model, runs fast on CPU
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.index = None
        self.turn_ids = []
        
    def build_index(self):
        """One-time index building (takes ~10 minutes for 37 interviews)."""
        turns = db.query(Turn).all()
        
        # Generate embeddings in batches
        texts = [t.text for t in turns]
        embeddings = self.model.encode(texts, batch_size=32, show_progress_bar=True)
        
        # Build FAISS index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings.astype('float32'))
        
        # Save mapping
        self.turn_ids = [t.id for t in turns]
        
        # Persist to disk
        faiss.write_index(self.index, "mvp_embeddings.index")
        np.save("mvp_turn_ids.npy", self.turn_ids)
    
    def search(self, query: str, k: int = 20):
        """Semantic search using local embeddings."""
        query_vector = self.model.encode([query])
        distances, indices = self.index.search(query_vector.astype('float32'), k)
        
        return [self.turn_ids[i] for i in indices[0]]
```

### Day 4-5: Simple UI

```html
<!-- templates/search.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Uruguay Interview Search</title>
    <script src="https://unpkg.com/htmx.org@1.9.0"></script>
    <style>
        body { font-family: Arial; max-width: 1200px; margin: 0 auto; padding: 20px; }
        .result { border: 1px solid #ddd; padding: 15px; margin: 10px 0; }
        .citation { background: #f0f0f0; padding: 10px; margin: 5px 0; }
        .metadata { color: #666; font-size: 0.9em; }
    </style>
</head>
<body>
    <h1>Uruguay Interview Search (MVP)</h1>
    
    <form hx-post="/api/search" hx-target="#results">
        <input type="text" name="query" placeholder="What do people say about security?" 
               style="width: 70%; padding: 10px;">
        <button type="submit">Search</button>
    </form>
    
    <div style="margin-top: 20px;">
        <label>Filters:</label>
        <select name="department">
            <option value="">All Departments</option>
            <option value="Montevideo">Montevideo</option>
            <option value="Canelones">Canelones</option>
            <option value="Salto">Salto</option>
        </select>
        
        <select name="age_range">
            <option value="">All Ages</option>
            <option value="18-29">18-29</option>
            <option value="30-49">30-49</option>
            <option value="50+">50+</option>
        </select>
    </div>
    
    <div id="results" style="margin-top: 30px;">
        <!-- Results appear here -->
    </div>
</body>
</html>
```

### Day 5-7: Tool Interface for AI Assistants

```python
# src/mvp/ai_tool_interface.py
@app.post("/tool/search")
async def tool_search(
    query: str,
    filters: dict = None,
    return_format: str = "citations"  # or "natural"
):
    """
    Simplified interface for AI assistants like Claude.
    
    Example:
    {
        "query": "youth unemployment concerns",
        "filters": {"age_range": "18-29"},
        "return_format": "citations"
    }
    """
    # Get results
    results = await search(query, filters)
    
    if return_format == "citations":
        # Return structured data for AI to process
        return {
            "query": query,
            "result_count": len(results),
            "citations": [
                {
                    "turn_id": r.turn_id,
                    "interview_id": r.interview_id,
                    "text": r.text,
                    "speaker_age": r.age_range,
                    "location": r.department,
                    "tags": r.semantic_tags,
                    "relevance": calculate_relevance(query, r)
                }
                for r in results[:20]
            ]
        }
    else:
        # Return natural language summary
        return {
            "summary": generate_natural_summary(query, results),
            "supporting_evidence": len(results),
            "key_themes": extract_themes(results)
        }

@app.get("/tool/contradictions/{interview_id}")
async def find_contradictions(interview_id: str):
    """
    Simple contradiction detection using tags and sentiment.
    """
    turns = db.query(Turn).filter_by(interview_id=interview_id).all()
    
    contradictions = []
    for i, turn1 in enumerate(turns):
        for turn2 in turns[i+1:]:
            # Same topic, different sentiment?
            if (set(turn1.semantic_tags) & set(turn2.semantic_tags) and
                turn1.sentiment * turn2.sentiment < 0):  # Opposite signs
                
                contradictions.append({
                    "turn1": {"id": turn1.id, "text": turn1.text},
                    "turn2": {"id": turn2.id, "text": turn2.text},
                    "topic": list(set(turn1.semantic_tags) & set(turn2.semantic_tags)),
                    "confidence": 0.7  # Simple heuristic
                })
    
    return contradictions
```

## Deployment (Local Only)

```bash
# requirements.txt
fastapi==0.104.1
sqlalchemy==2.0.23
uvicorn==0.24.0
sentence-transformers==2.2.2  # Optional
faiss-cpu==1.7.4  # Optional
```

```bash
# Run locally
pip install -r requirements.txt
python build_search_index.py  # One time
uvicorn src.mvp.search_api:app --reload

# Access at http://localhost:8000
```

## What This MVP Provides

### For Researchers:
1. **Find quotes fast**: "What do elderly people say about healthcare?"
2. **Compare demographics**: "How do rural vs urban discuss employment?"
3. **Track themes**: "Show me all mentions of youth emigration"
4. **Export citations**: Copy-paste ready for papers

### For AI Assistants:
1. **Structured search**: Get JSON with full citation chains
2. **Natural summaries**: Pre-formatted research insights  
3. **Contradiction detection**: Find ambivalence/complexity
4. **Demographic analysis**: Filter by age, location, etc.

## MVP Limitations (Accepted for Speed)

1. **No cloud scale**: Handles 37 interviews well, would need optimization for 1000+
2. **Basic search**: Tag matching + text search (optional embeddings)
3. **Simple UI**: Functional but not beautiful
4. **Local only**: No collaboration features
5. **English/Spanish**: Basic keyword translation, not full multilingual

## Evolution Path

```
Week 1-2: This MVP
Week 3-4: Add local embeddings + better UI
Month 2: Cloud deployment + user accounts
Month 3: Full embedding system + advanced features
```

## Success Metrics

1. **Speed**: Find relevant quote in <5 seconds (vs 15 minutes manual)
2. **Coverage**: Surface 80% of relevant content for a query
3. **Usability**: Researchers can use without training
4. **Integration**: AI assistants can query programmatically

## Key Insight

**We don't need embeddings to start!** The existing semantic tags + smart text search + citation chains give us 70% of the value with 10% of the complexity.

The structured annotations from the 4-pass pipeline are already a form of "human embeddings" - they capture semantic meaning in a searchable way.

## Next Steps

1. Implement basic search API (Day 1-2)
2. Test with real research questions
3. Add local embeddings if needed (Day 3-4)
4. Deploy for research team use
5. Iterate based on feedback

This MVP can be built by one developer in 5-7 days and immediately provides value to researchers, setting the foundation for the full system later.