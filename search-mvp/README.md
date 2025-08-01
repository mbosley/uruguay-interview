# Uruguay Interview Research Agent

An AI-powered research assistant for analyzing qualitative interview data from Uruguay's citizen consultation project.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- API keys for Moonshot or Groq

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Add your API keys to .env

# Run the backend
python backend/stream_cli_output.py
```

### Frontend Access
1. **Local access**: Open `frontend/cli-terminal.html` in your browser
2. **Remote access**: 
   - Install ngrok: `brew install ngrok`
   - Expose backend: `ngrok http 8001`
   - Update `API_URL` in frontend files with ngrok URL

## 📁 Project Structure

```
search-mvp/
├── backend/              # Backend API servers
│   ├── stream_cli_output.py    # Main SSE backend
│   └── run_agent.py           # Research agent runner
├── frontend/             # Web interfaces
│   ├── cli-terminal.html      # Main research interface
│   └── interview-view.html    # Interview viewer
├── src/                  # Core source code
│   ├── agent/           # Research agent implementation
│   ├── cli/             # CLI tools for corpus interaction
│   └── tools/           # Rendering and utility tools
├── data/                # Interview corpus (gitignored)
├── docs/                # Documentation
│   ├── setup/          # Setup and deployment guides
│   └── development/    # Development documentation
└── tests/              # Test suite
```

## 🔍 Key Features

- **Interactive Research**: Ask questions about the interview corpus and get AI-powered analysis
- **Citation Support**: Click on citations like [[062:15]] to view source material
- **Real-time Streaming**: See research progress as it happens
- **Multiple LLM Providers**: Support for Moonshot and Groq

## 📚 Documentation

- [Local Backend Setup](docs/setup/LOCAL_BACKEND_GUIDE.md)
- [Railway Deployment](docs/setup/RAILWAY_DEPLOYMENT_STRATEGY.md)
- [Development Guide](docs/development/BACKEND_UPDATE_SPEC.md)

## 🛠 Development

```bash
# Run tests
python -m pytest tests/

# Check corpus data
python src/cli/enriched_cli.py list

# Search interviews
python src/cli/enriched_cli.py search "healthcare"
```

## 📄 License

This project is part of academic research on citizen consultation in Uruguay.