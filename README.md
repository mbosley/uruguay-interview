# Hierarchical Citation System Feature Branch

This branch implements a comprehensive citation tracking system for the Uruguay Interview Analysis project.

## Overview

The citation system creates a traceable chain of evidence from corpus-level insights down to individual conversation turns:

```
Corpus Insights (cross-interview patterns)
    ↓ cites
Interview Insights (priorities, narratives)
    ↓ cites
Individual Turns (specific utterances)
```

## Quick Start

1. Review the comprehensive implementation guide:
   ```bash
   cat IMPLEMENTATION_GUIDE.md
   ```

2. Check the task list:
   ```bash
   cat TASK_CHECKLIST.md
   ```

3. Start with Phase 1 implementation

## Key Components

- **Turn-level enhancements**: Semantic tags, key phrases, quotable segments
- **Interview citations**: Every insight cites supporting turns
- **Corpus citations**: Patterns cite supporting interviews
- **Validation system**: Ensures citation quality
- **Explorer UI**: Interactive citation visualization

## Implementation Status

- [ ] Phase 1: Turn-Level Citation Enhancement
- [ ] Phase 2: Interview-Level Citation Implementation  
- [ ] Phase 3: Corpus-Level Citation Implementation
- [ ] Phase 4: Citation Validation and UI
- [ ] Phase 5: Integration and Testing

## Testing

Run tests specific to citation system:
```bash
pytest tests/test_citation_system.py -v
```

## Documentation

- `IMPLEMENTATION_GUIDE.md` - Detailed step-by-step implementation
- `TASK_CHECKLIST.md` - Checklist for tracking progress
- `ARCHITECTURE.md` - System design and data flow