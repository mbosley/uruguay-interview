# Uruguay Interview Research System

A comprehensive system for analyzing citizen consultation interviews from Uruguay using AI-powered research agents, with both web and command-line interfaces.

## 🚀 Quick Start

### Using the Web Interface (Recommended)

```bash
# 1. Start the API server
make run-api

# 2. Start the React UI (in another terminal)
make run-ui

# 3. Open http://localhost:3000 in your browser
```

### Using the Command Line

```bash
# Run a specific research question
make agent QUESTION="What do citizens say about healthcare access?"

# Interactive research session
make run-agent
```

### Using the Streamlit Demo

```bash
# Start the multi-page Streamlit app
make run-demo
```

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Installation](#installation)
- [Usage Guide](#usage-guide)
- [API Documentation](#api-documentation)
- [Configuration](#configuration)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)

## Overview

This system analyzes 37 citizen consultation interviews from Uruguay (May 28-29, 2025) to understand citizen perspectives on national and local priorities. It provides:

- **AI-powered research agent** for autonomous exploration of interview data
- **Real-time web interface** with live research visualization
- **Command-line tools** for batch processing and scripting
- **Multi-provider LLM support** (Moonshot, Groq)
- **WebSocket streaming** for real-time updates

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   React UI      │────▶│   FastAPI        │────▶│ Research Agent  │
│  (WebSocket)    │     │   Server         │     │  (LLM + Tools)  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │                           │
                               ▼                           ▼
                        ┌──────────────────┐     ┌─────────────────┐
                        │  Interview       │     │   Scratchpad    │
                        │  Corpus          │     │   Storage       │
                        └──────────────────┘     └─────────────────┘
```

## Installation

### Prerequisites

- Python 3.11+
- Node.js 16+
- npm or yarn

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd search-mvp

# Install Python dependencies
make setup

# Install frontend dependencies
cd uruguay-research-ui
npm install
cd ..
```

### Environment Configuration

Create a `.env` file:

```bash
# LLM Provider API Keys (at least one required)
MOONSHOT_API_KEY=your-moonshot-key
GROQ_API_KEY=your-groq-key

# Optional: Specify default provider
KIMI_PROVIDER=moonshot  # or "groq"
```

## Usage Guide

### Web Interface

The React UI provides a ChatGPT-style interface with real-time research visualization:

1. **Start the backend**: `make run-api`
2. **Start the frontend**: `make run-ui`
3. **Open**: http://localhost:3000

Features:
- Live tool trace showing the AI's reasoning process
- Real-time streaming of research steps
- Export results as PDF
- Interview browser sidebar

### Command Line Interface

#### Basic Research

```bash
# Healthcare research
make healthcare

# Education research  
make education

# Custom question
make agent QUESTION="What challenges do rural communities face?"
```

#### Advanced Options

```bash
# Specify provider and iterations
make agent PROVIDER=groq MAX_ITER=20 QUESTION="your question"

# Debug mode with detailed logging
make debug-agent QUESTION="your question"
```

### Streamlit Demo

A multi-page application for exploring the data:

```bash
make run-demo
```

Pages:
- 🔍 **Interview Browser**: Browse and read interviews
- 🎯 **Theme Explorer**: Explore themes and topics
- 💬 **Research Agent**: Interactive research interface
- 📊 **Analytics**: Statistical analysis dashboard

## API Documentation

### REST Endpoints

#### Start Research
```http
POST /research
Content-Type: application/json

{
  "question": "What do citizens say about healthcare?",
  "provider": "moonshot",
  "max_iterations": 10,
  "use_mock": false
}
```

#### Get Job Status
```http
GET /research/{job_id}
```

#### List Interviews
```http
GET /interviews
```

### WebSocket Events

Connect to: `ws://localhost:8000/research/{job_id}/stream`

Event types:
- `iteration_start`: New research iteration beginning
- `thinking`: Agent's reasoning process
- `tool_call`: Tool being invoked
- `tool_result`: Tool execution result
- `response_end`: Final research summary

## Configuration

### LLM Providers

Configure in `config/providers.py` or via environment:

| Provider | Speed | Model | Best For |
|----------|-------|-------|----------|
| Moonshot | ~30 tok/s | kimi-k2-0711-preview | Standard research |
| Groq | ~185 tok/s | moonshotai/kimi-k2-instruct | Fast iterations |

### Research Tools

Available tools in `interview_research_tools.py`:
- `get_corpus_stats`: Overview of interview data
- `search_interviews`: Text/semantic search
- `list_interview_themes`: Browse themes
- `get_interview_turn`: Retrieve specific quotes
- `search_themes`: Find theme patterns

## Development

### Project Structure

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for detailed layout.

### Running Tests

```bash
# All tests
make test

# Specific test
python tests/unit/test_event_contract.py

# Frontend tests
cd uruguay-research-ui && npm test
```

### Debugging

```bash
# Enable debug logging
export DEBUG=true
make run-api

# View unified logs
python unified_logger.py  # In one terminal
python view_unified_logs.py  # In another
```

## Testing

### Mock Agent

Test frontend without LLM costs:

```bash
# API with mock agent
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"question": "test", "use_mock": true}'
```

### Event Contract Testing

Verify frontend/backend compatibility:

```bash
python tests/unit/test_event_contract.py
```

## Deployment

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or use the deployment script
./deploy.sh
```

### Production Configuration

1. Update `nginx.conf` for your domain
2. Set production environment variables
3. Enable HTTPS in nginx
4. Configure CORS origins in `api_server.py`

## Additional Documentation

- [Provider Configuration](docs/PROVIDER_CONFIGURATION.md) - Detailed LLM provider setup
- [Project Structure](PROJECT_STRUCTURE.md) - Complete directory layout
- [Trace Display Fix](docs/trace_fix_report.md) - WebSocket trace implementation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

[Add your license here]

---

**Built for researchers** to explore citizen perspectives through natural language queries and receive comprehensive, evidence-based answers.