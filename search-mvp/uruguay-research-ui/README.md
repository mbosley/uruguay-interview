# Uruguay Interview Research UI

A modern React web application for the Uruguay Interview Research Agent, providing a professional interface for analyzing citizen consultation interviews with real-time AI reasoning visualization.

## Features

- 🧠 **Real-time Research Process**: Watch the AI agent's thinking and tool calls as it analyzes interviews
- 🔍 **Smart Question Interface**: Natural language queries with helpful suggestions
- 📊 **Live Trace Display**: Animated visualization of each research step
- 📄 **Streaming Results**: Results appear word-by-word as the AI generates them
- 🇺🇾 **Uruguay-themed Design**: Professional dark theme with Uruguay blue accents
- 📁 **Interview Browser**: Navigate through 37 citizen consultation interviews
- 📈 **Research Metrics**: Track duration, costs, and tool usage

## Prerequisites

- Node.js 18+ and npm
- Python 3.8+ (for the API server)
- The Uruguay interview corpus data

## Installation

1. Install dependencies:
```bash
npm install
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API endpoints
```

## Running the Application

### Development Mode

1. Start the API server (from the parent directory):
```bash
cd ../web_demo
python api_server_enhanced.py
```

2. Start the React development server:
```bash
npm start
```

The app will open at http://localhost:3000

### Production Build

```bash
npm run build
```

This creates an optimized production build in the `build` folder.

## Architecture

### Frontend Structure
```
src/
├── components/
│   ├── Layout/          # Header, Sidebar
│   ├── Research/        # QuestionInput, TraceDisplay, ResultsViewer
│   └── Common/          # Shared components
├── services/
│   ├── api.ts          # REST API client
│   └── websocket.ts    # WebSocket client for real-time updates
├── types/              # TypeScript type definitions
└── utils/              # Helper functions
```

### Key Technologies
- **React 19** with TypeScript
- **Tailwind CSS** for styling
- **Lucide React** for icons
- **WebSocket** for real-time updates
- **Axios** for HTTP requests

## Usage

1. **Ask a Question**: Enter a research question about the interviews
2. **Watch the Process**: See the AI's reasoning steps in real-time
3. **Review Results**: Read the comprehensive analysis with citations
4. **Export Findings**: Download results as PDF or Markdown

## Example Questions

- What are the main healthcare concerns mentioned by citizens?
- How do citizens describe security issues in their communities?
- What infrastructure problems are most frequently mentioned?
- Compare rural vs urban perspectives on public services
- What do people say about education quality?

## API Integration

The app connects to the FastAPI backend via:
- REST endpoints for starting research and retrieving results
- WebSocket for real-time trace updates

Configure endpoints in `.env`:
```
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
```

## Development

### Available Scripts

- `npm start` - Runs the app in development mode
- `npm test` - Launches the test runner
- `npm run build` - Builds the app for production
- `npm run eject` - Ejects from Create React App (one-way operation)

### Code Style
- ESLint configuration in `package.json`
- TypeScript strict mode enabled
- Tailwind CSS for consistent styling

### Testing
```bash
npm test
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Troubleshooting

### CORS Issues
Ensure the API server has CORS enabled for your frontend URL.

### WebSocket Connection Failed
Check that:
- The API server is running
- WebSocket URL in `.env` is correct
- No firewall is blocking WebSocket connections

## License

This project is part of the Uruguay Interview Research system.