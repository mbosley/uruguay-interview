# Uruguay Interview Research Demo

A minimal, single-page demo showcasing AI-powered research through citizen consultation interviews.

## Features

- **Real-time Research Trace**: Watch the AI explore the interview corpus step-by-step
- **Interactive Citations**: Click interview references to view source material
- **Zero Dependencies**: Pure HTML/CSS/JavaScript - no build process required
- **Server-Sent Events**: Lightweight alternative to WebSockets for streaming

## Quick Start

1. **Start the API server**:
   ```bash
   cd search-mvp
   make run-api
   # or
   python api_server.py
   ```

2. **Open the demo**:
   - Open `demo.html` in your browser
   - Or serve it locally: `python -m http.server 8080`

## How It Works

The demo showcases the core research flow:

1. **Question Input**: User asks about citizen perspectives
2. **Research Execution**: AI agent explores the corpus using tools:
   - `get_corpus_stats()` - Understand the data
   - `list_interview_themes()` - Discover topics
   - `search_interviews()` - Find specific content
   - `get_interview_turn()` - Retrieve exact quotes
3. **Live Trace**: Each tool call is displayed as it happens
4. **Final Report**: Synthesized findings with clickable citations

## Architecture

```
demo.html  ←→  API Server  ←→  Research Agent
   SSE            FastAPI         LLM + Tools
```

## Customization

- **Styling**: Modify CSS variables at the top of `demo.html`
- **API URL**: Change `API_URL` in the script section
- **Max Iterations**: Adjust in the `startResearch()` function

## Deployment Options

### Static Hosting (Vercel, Netlify, GitHub Pages)
1. Change `API_URL` to your deployed backend
2. Upload `demo.html` as index.html

### Backend Hosting (Railway, Render, Fly.io)
```bash
docker build -t uruguay-research .
docker run -p 8000:8000 uruguay-research
```

## Demo Script

1. **Healthcare Access**: "What do citizens say about healthcare?"
   - Shows concerns about doctor shortages, rural access
   - Cites specific interviews with evidence

2. **Education Crisis**: "What challenges face education?"
   - Reveals systemic issues, teacher burnout
   - Links to interview segments

3. **Rural Perspectives**: "How do rural communities view government services?"
   - Contrasts urban/rural experiences
   - Highlights infrastructure gaps