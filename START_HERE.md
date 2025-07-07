# 🚀 Citation System Implementation - Start Here

Welcome! You're implementing a hierarchical citation system for the Uruguay Interview Analysis project. This system will enable complete traceability from high-level insights down to specific conversation turns.

## Your Mission

Build a citation system that tracks how AI-generated insights are derived from interview data across three levels:
1. **Turn Level**: Tag and extract citable elements from conversation turns
2. **Interview Level**: Link insights to supporting turns 
3. **Corpus Level**: Connect patterns to supporting interviews

## Essential Documents

Read these in order:

1. **`ARCHITECTURE.md`** - Understand the system design
2. **`IMPLEMENTATION_GUIDE.md`** - Detailed step-by-step instructions  
3. **`TASK_CHECKLIST.md`** - Track your progress

## Quick Context

The Uruguay project analyzes 5000+ citizen interviews using AI. Currently, the system generates insights but doesn't track which specific parts of conversations support those insights. Your implementation will add this critical capability.

## Development Setup

1. You're in a git worktree at: `worktrees/citation-system`
2. Branch: `feature/hierarchical-citations`
3. Parent directory has the main codebase

## First Steps

1. **Understand Current System**:
   ```bash
   # From parent directory
   cd ../..
   grep -r "turn_id" src/pipeline/annotation/
   cat src/pipeline/annotation/multipass_annotator.py | grep -A 20 "TURN_ANALYSIS_SCHEMA"
   ```

2. **Check Database Schema**:
   ```bash
   cat src/database/models.py | grep -A 10 "class Turn"
   ```

3. **Start Phase 1**:
   - Open `TASK_CHECKLIST.md`
   - Begin with Day 1 tasks
   - Create `semantic_tagger.py` as specified

## Key Technical Details

- **Language**: Python 3.9+
- **AI Provider**: OpenAI GPT-4 (configurable)
- **Database**: SQLite with SQLAlchemy
- **Testing**: pytest
- **UI**: Streamlit for Citation Explorer

## Architecture Highlights

```
Turn → "I worry about crime" + [security_concern] tag
    ↑
Interview Insight → "Security is top priority" + cites turns [3,7,12]
    ↑
Corpus Pattern → "73% prioritize security" + cites 26 interviews
```

## Implementation Philosophy

1. **Incremental**: Each phase builds on the previous
2. **Testable**: Write tests as you go
3. **Validatable**: Citations must be verifiable
4. **User-Friendly**: Clear visualization of citation chains

## Need Help?

- Check existing patterns: `grep -r "annotation" src/pipeline/`
- Database examples: `src/database/models.py`
- Annotation flow: `src/pipeline/annotation/multipass_annotator.py`

## Success Criteria

✅ Every insight can be traced to source text
✅ 95%+ citation coverage
✅ Performance impact <20%
✅ Validation catches bad citations
✅ UI makes citations explorable

---

**Ready? Start with Phase 1 in the TASK_CHECKLIST.md!** 🎯