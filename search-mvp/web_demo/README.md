# Uruguay Interview Research Agent - Web Demo

A web-based interface for exploring citizen consultation interviews from Uruguay using AI-powered research agents.

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# 1. Clone the repository
git clone <your-repo>
cd search-mvp

# 2. Create .env file with your API keys
cp .env.example .env
# Edit .env and add your MOONSHOT_API_KEY and/or GROQ_API_KEY

# 3. Deploy with Docker
./deploy.sh

# 4. Access the demo
# Web UI: http://localhost:8501
# API: http://localhost:8000
```

### Option 2: Local Development

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set environment variables
export MOONSHOT_API_KEY="your_key"
export GROQ_API_KEY="your_key"

# 3. Start the API server
python web_demo/api_server.py

# 4. In another terminal, start Streamlit
streamlit run web_demo/app.py
```

## 🎯 Features

### Web Interface (Streamlit)
- **Interactive Research**: Ask questions about the interview corpus
- **Provider Selection**: Choose between Groq (fast) or Moonshot (cost-efficient)
- **Real-time Results**: See research progress and results instantly
- **Cost Tracking**: Monitor API usage and costs
- **Research History**: Review previous research sessions

### API Endpoints
- `GET /`: API documentation
- `GET /providers`: List available LLM providers
- `POST /research`: Submit a research question
- `GET /research/{job_id}`: Get research results
- `GET /corpus/stats`: Get corpus statistics

## 📊 Demo Limitations

For the public demo, we implement:
- **Rate Limiting**: 10 requests per hour per IP
- **Max Iterations**: Limited to 10 iterations per research
- **Timeout**: 5-minute maximum per research session
- **No Sub-agents**: Recursive agents disabled for demo

## 🔒 Security Considerations

1. **API Keys**: Never expose API keys in the frontend
2. **Rate Limiting**: Implement proper rate limiting
3. **Input Validation**: Sanitize all user inputs
4. **Resource Limits**: Set memory and CPU limits in Docker
5. **HTTPS**: Use HTTPS in production (via reverse proxy)

## 🏗️ Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Browser   │────▶│   Nginx     │────▶│  Streamlit  │
└─────────────┘     │  (Reverse   │     │    (UI)     │
                    │   Proxy)     │     └─────────────┘
                    │             │              │
                    │             │              ▼
                    │             │     ┌─────────────┐
                    │             │────▶│  FastAPI    │
                    └─────────────┘     │   (API)     │
                                       └─────────────┘
                                              │
                                              ▼
                                       ┌─────────────┐
                                       │Research Agent│
                                       └─────────────┘
```

## 🚀 Deployment Options

### 1. Heroku
```bash
# Create Heroku app
heroku create your-app-name

# Set environment variables
heroku config:set MOONSHOT_API_KEY=your_key
heroku config:set GROQ_API_KEY=your_key

# Deploy
git push heroku main
```

### 2. Google Cloud Run
```bash
# Build and push image
gcloud builds submit --tag gcr.io/PROJECT-ID/research-agent

# Deploy
gcloud run deploy --image gcr.io/PROJECT-ID/research-agent \
  --platform managed \
  --set-env-vars MOONSHOT_API_KEY=$MOONSHOT_API_KEY,GROQ_API_KEY=$GROQ_API_KEY
```

### 3. AWS ECS
Use the provided `docker-compose.yml` with ECS CLI or create ECS task definitions.

## 📈 Scaling Considerations

1. **Caching**: Add Redis for caching research results
2. **Queue**: Use Celery/RabbitMQ for async processing
3. **Database**: Store results in PostgreSQL instead of memory
4. **CDN**: Serve static assets via CDN
5. **Load Balancing**: Use multiple API instances

## 🛠️ Customization

### Modify UI Theme
Edit `web_demo/app.py` and update Streamlit config:
```python
st.set_page_config(
    page_title="Your Title",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)
```

### Add Authentication
```python
# In api_server.py
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

@app.post("/research")
async def submit_research(
    request: ResearchRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Verify token
    if not verify_token(credentials.credentials):
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Custom Branding
1. Add logo: Place in `web_demo/static/logo.png`
2. Update colors in `web_demo/style.css`
3. Modify welcome text in `app.py`

## 📝 Environment Variables

```env
# Required
MOONSHOT_API_KEY=sk-...
GROQ_API_KEY=gsk-...

# Optional
KIMI_PROVIDER=groq          # Default provider (moonshot/groq)
MAX_ITERATIONS=10           # Max research iterations
RATE_LIMIT_PER_HOUR=10     # API rate limit
ENABLE_SUB_AGENTS=false    # Enable recursive agents
LOG_LEVEL=INFO             # Logging level
```

## 🐛 Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs -f

# Rebuild containers
docker-compose build --no-cache
docker-compose up -d
```

### API key errors
```bash
# Verify environment variables
docker-compose exec api env | grep API_KEY
```

### Port conflicts
```bash
# Change ports in docker-compose.yml
ports:
  - "8001:8000"  # API
  - "8502:8501"  # Streamlit
```

## 📄 License

This demo is provided as-is for educational purposes. Ensure you comply with the data usage terms for the Uruguay interview corpus.