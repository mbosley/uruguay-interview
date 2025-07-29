# Handoff Instructions for MVP Sprint

## Context
The hierarchical citation system PR has been merged! Now we're moving to build the MVP search tool that leverages this citation system.

## What Was Just Completed
- ✅ 4-pass annotation pipeline with citation tracking
- ✅ Semantic tagging system (security_concern, economic_worry, etc.)
- ✅ Hierarchical citations: Corpus → Interview → Turn
- ✅ Database models for citation metadata
- ✅ Tested on real Uruguay interview data

## MVP Sprint Goal
Build a lightweight, locally-hosted search tool that makes the Uruguay interviews searchable via natural language queries using the existing citation system.

## Key Files to Reference

### From the Merged Citation System:
- `src/pipeline/annotation/semantic_tagger.py` - How tags are extracted
- `src/pipeline/annotation/citation_tracker.py` - Citation management
- `src/database/models.py` - Database schema including citation tables
- `config/taxonomy.yaml` - Semantic tag definitions

### MVP Specifications Created:
- `docs/LOCAL_MVP_SPEC.md` - Simplified architecture
- `MVP_QUICKSTART.md` - 30-minute implementation guide
- `MVP_INITIAL_CODE.py` - Working FastAPI starter code

## Starting the MVP Sprint

1. **Create new worktree:**
   ```bash
   cd /Users/mitchellbosley/projects/uruguay-interview
   git worktree add worktrees/mvp-search-tool -b feature/mvp-search-tool
   cd worktrees/mvp-search-tool
   ```

2. **Set up basic structure:**
   ```bash
   mkdir -p src templates config
   cp MVP_INITIAL_CODE.py src/main.py
   cp config/taxonomy.yaml config/
   ```

3. **Install dependencies:**
   ```bash
   pip install fastapi sqlalchemy uvicorn psycopg2-binary
   ```

4. **Run the MVP:**
   ```bash
   export DATABASE_URL="postgresql://user:pass@localhost/uruguay_interviews"
   python src/main.py
   ```

## Week 1 Implementation Plan

### Day 1-2: Basic Search
- Tag-based search using existing semantic tags
- Text search fallback
- Connect to PostgreSQL database
- Test endpoint: `POST /search`

### Day 3: Query Enhancement  
- Spanish/English keyword mapping
- Uruguay-specific terms (pasta base, asentamiento, etc.)
- Demographic filtering

### Day 4: AI Tool Interface
- `/tool/search` endpoint for Claude/GPT
- Structured citation responses
- Natural language summaries

### Day 5: Simple Web UI
- Basic HTML with search form
- Display results with citations
- Export functionality

## Key Insight

**The semantic tags ARE our embeddings!** The citation system already tagged every turn with standardized labels like:
- `security_concern`, `economic_worry`, `health_anxiety`
- `hope_expression`, `frustration_statement`, `fear_articulation`
- `personal_experience`, `community_observation`, `statistical_claim`

These tags make the corpus immediately searchable without needing vector embeddings.

## Database Tables to Use

```sql
-- Main tables with data
interviews          -- Core interview data
conversation_turns  -- Individual turns within interviews
turn_citation_metadata -- Semantic tags for each turn
interview_insight_citations -- Interview-level insights

-- Key query pattern
SELECT t.*, tcm.semantic_tags 
FROM conversation_turns t
JOIN turn_citation_metadata tcm ON t.id = tcm.turn_id
WHERE tcm.semantic_tags::text LIKE '%security_concern%'
```

## What NOT to Build Yet

1. **No embeddings** - semantic tags are sufficient
2. **No cloud deployment** - local only
3. **No authentication** - research team use
4. **No complex UI** - simple HTML is fine

## Success Metrics

- Find relevant quotes in <5 seconds (vs 15 minutes manual)
- Surface 80% of relevant content for a query
- Work with both Spanish and English queries
- Provide full citation chains

## Questions to Consider

1. Should we cache common queries?
2. How to handle synonyms (work/employment/job)?
3. What relevance scoring makes sense?
4. How to format citations for researchers?

## Remember

This MVP leverages ALL the work from the citation system. Every turn is already:
- Analyzed for content and function
- Tagged with semantic labels
- Linked to interview-level insights
- Ready to be searched!

The MVP just needs to make this searchable. Keep it simple!

Good luck with the sprint! 🚀