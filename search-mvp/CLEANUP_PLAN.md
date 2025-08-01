# Repository Cleanup Plan

## Current Issues
1. Multiple versions of similar files (stream_cli_output*.py)
2. Test files scattered in root directory
3. Many documentation files in root
4. Old demo/test HTML files
5. Large results and scratchpads directories

## Proposed Structure

```
search-mvp/
├── README.md                    # Main documentation
├── requirements.txt             # Dependencies
├── Makefile                    # Build commands
├── .gitignore                  # Git ignore rules
│
├── src/                        # Source code (keep as is)
│   ├── agent/
│   ├── cli/
│   ├── llm/
│   ├── parser/
│   ├── search/
│   └── tools/
│
├── backend/                    # Consolidate backend files
│   ├── stream_cli_output.py    # Main backend (currently used)
│   ├── run_agent.py           # Agent runner
│   └── archived/              # Old versions
│       ├── stream_cli_output_simple.py
│       ├── stream_cli_output_optimized.py
│       └── stream_cli_output_railway.py
│
├── frontend/                   # Frontend files
│   ├── cli-terminal.html      # Main interface
│   ├── interview-view.html    # Interview viewer
│   └── archived/              # Old demos
│       ├── demo.html
│       ├── terminal-demo.html
│       └── terminal-demo-simple.html
│
├── docs/                       # All documentation
│   ├── setup/                 # Setup guides
│   │   ├── LOCAL_BACKEND_GUIDE.md
│   │   ├── RAILWAY_DEPLOYMENT_STRATEGY.md
│   │   └── RAILWAY_VOLUME_GUIDE.md
│   ├── development/           # Development docs
│   │   ├── BACKEND_UPDATE_SPEC.md
│   │   └── PROJECT_STRUCTURE.md
│   └── archived/              # Old docs
│
├── tests/                      # All tests
│   ├── unit/                  # Existing unit tests
│   ├── integration/           # Integration tests
│   └── fixtures/              # Test fixtures
│
├── scripts/                    # Utility scripts (keep as is)
│
├── data/                       # Data directory (gitignored)
│
└── results/                    # Results directory (consider gitignoring)
```

## Files to Delete/Archive

### Delete (redundant/outdated):
- test_websocket.html
- test_websocket_connection.html
- test_ws_minimal.html
- test-interview-api.html
- test_*.py in root (move to tests/)
- mock_research_agent.py
- unified_logger.py
- unified_backend_logger.py

### Archive (may be useful later):
- Old stream_cli_output versions
- Demo HTML files
- Old documentation

### Keep in Root:
- Main entry points (stream_cli_output.py, run_agent.py)
- Config files (requirements.txt, Makefile, etc.)
- Main README.md

## Cleanup Commands

```bash
# 1. Create new directories
mkdir -p backend/archived
mkdir -p frontend/archived
mkdir -p docs/{setup,development,archived}

# 2. Move backend files
mv stream_cli_output_*.py backend/archived/
mv stream_cli_output.py run_agent.py backend/

# 3. Move frontend files
mv cli-terminal.html interview-view.html frontend/
mv demo.html terminal-demo*.html frontend/archived/

# 4. Move documentation
mv LOCAL_BACKEND_GUIDE.md RAILWAY_*.md docs/setup/
mv BACKEND_UPDATE_SPEC.md PROJECT_STRUCTURE.md docs/development/
mv *.md docs/archived/  # Other misc docs

# 5. Move tests
mv test_*.py tests/

# 6. Update .gitignore
echo "results/" >> .gitignore
echo "scratchpads/" >> .gitignore
echo "logs/" >> .gitignore
echo "unified_logs/" >> .gitignore
```

## Questions Before Proceeding

1. Should we keep the results/ directory or gitignore it?
2. Should we archive or delete the uruguay-research-ui React app?
3. Do you want to keep the web_demo/ Streamlit app?
4. Should we consolidate the multiple test files in root?

## Benefits
- Cleaner root directory
- Easier to find relevant files
- Clear separation of concerns
- Better for new contributors