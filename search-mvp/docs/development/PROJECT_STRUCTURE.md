# Uruguay Interview Research - Project Structure

## Directory Layout

```
search-mvp/
├── api_server.py                    # Main FastAPI server with WebSocket support
├── interview_research_agent_improved.py  # Core research agent implementation
├── interview_research_tools.py      # Tool definitions for agent
├── mock_research_agent.py          # Mock agent for frontend testing
├── unified_logger.py               # Unified logging server
├── unified_backend_logger.py       # Backend logger client
├── view_unified_logs.py            # Log viewer utility
├── requirements.txt                # Python dependencies
├── Makefile                        # Build and run commands
├── docker-compose.yml              # Docker deployment config
├── Dockerfile                      # Container definition
├── nginx.conf                      # Nginx reverse proxy config
├── deploy.sh                       # Deployment script
├── config.yaml                     # Application configuration
├── .env                           # Environment variables (not in git)
├── .gitignore                     # Git ignore patterns
│
├── config/                        # Configuration modules
│   └── providers.py              # LLM provider configurations
│
├── src/                          # Source code modules
│   ├── cli/                      # CLI interfaces
│   │   └── enriched_cli.py       # Enhanced CLI with rich formatting
│   └── tools/                    # Tool implementations
│       └── (various tool modules)
│
├── web_demo/                     # Streamlit demo application
│   ├── app.py                    # Main Streamlit app
│   ├── corpus_loader_api.py      # Corpus loading utilities
│   ├── pages/                    # Streamlit pages
│   │   ├── 1_🔍_Interview_Browser.py
│   │   ├── 2_🎯_Theme_Explorer.py
│   │   ├── 3_💬_Research_Agent.py
│   │   └── 4_📊_Analytics.py
│   └── utils/                    # Utility modules
│       ├── data_loader.py
│       └── styling.py
│
├── uruguay-research-ui/          # React frontend application
│   ├── package.json             # Node dependencies
│   ├── src/                     # React source code
│   │   ├── App.tsx              # Main app component
│   │   ├── components/          # React components
│   │   │   ├── Chat/            # Chat interface components
│   │   │   ├── Layout/          # Layout components
│   │   │   └── Research/        # Research display components
│   │   ├── services/            # API and WebSocket services
│   │   │   ├── api.ts
│   │   │   ├── websocket.ts
│   │   │   └── unifiedLogger.ts
│   │   └── types/               # TypeScript type definitions
│   │       └── research.types.ts
│   └── public/                  # Static assets
│
├── tests/                       # Test files
│   ├── unit/                    # Unit tests
│   │   ├── test_event_contract.py
│   │   ├── test_websocket_events.py
│   │   └── debug_trace_issue.py
│   ├── integration/             # Integration tests
│   └── fixtures/                # Test fixtures and data
│       └── test_trace_display.html
│
├── scripts/                     # Utility scripts
│   ├── analysis/                # Data analysis scripts
│   └── utilities/               # Helper utilities
│       └── cleanup_project.py
│
├── docs/                        # Documentation
│   ├── PROVIDER_CONFIGURATION.md
│   ├── LOGGING_IMPROVEMENTS.md
│   ├── fix_trace_display.md
│   └── trace_fix_report.md
│
├── archived/                    # Archived code versions
│   ├── old_versions/           # Previous implementations
│   └── experiments/            # Experimental code
│
├── logs/                       # Application logs (gitignored)
├── unified_logs/               # Unified frontend/backend logs (gitignored)
├── results/                    # Research results (gitignored)
├── scratchpads/                # Agent scratchpad files (gitignored)
├── data/                       # Data directory (gitignored)
└── venv/                       # Python virtual environment (gitignored)
```

## Key Components

### Backend Services

1. **API Server** (`api_server.py`)
   - FastAPI application
   - WebSocket support for real-time updates
   - Research job management
   - Interview data endpoints

2. **Research Agent** (`interview_research_agent_improved.py`)
   - Autonomous research with tool use
   - Event emission for real-time updates
   - Multiple LLM provider support
   - Iterative research process

3. **Mock Agent** (`mock_research_agent.py`)
   - Simulates research process for testing
   - No LLM costs
   - Predictable event flow

### Frontend Applications

1. **React UI** (`uruguay-research-ui/`)
   - Modern chat interface
   - Real-time research visualization
   - WebSocket integration
   - Tool trace display

2. **Streamlit Demo** (`web_demo/`)
   - Multi-page application
   - Interview browser
   - Theme explorer
   - Analytics dashboard

### Development Tools

1. **Unified Logger**
   - Captures frontend and backend logs
   - Synchronized debugging
   - JSON Lines format

2. **Test Suite**
   - Event contract validation
   - WebSocket testing
   - Frontend/backend integration tests

## Configuration

- **Environment Variables**: `.env` file (see `.env.example`)
- **LLM Providers**: `config/providers.py`
- **Application Config**: `config.yaml`

## Running the Project

1. **Backend API**:
   ```bash
   make run-api
   ```

2. **React Frontend**:
   ```bash
   make run-ui
   ```

3. **Streamlit Demo**:
   ```bash
   make run-demo
   ```

4. **Full Stack**:
   ```bash
   make run-all
   ```

## Testing

```bash
# Run all tests
make test

# Run specific test
python tests/unit/test_event_contract.py
```

## Deployment

```bash
# Build and deploy with Docker
./deploy.sh
```