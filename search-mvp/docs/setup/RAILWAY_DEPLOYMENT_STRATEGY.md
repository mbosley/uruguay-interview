# Railway Deployment Strategy for Uruguay Interview Research Backend

## Overview
Deploy the `stream_cli_output_simple.py` backend with full corpus data to Railway, enabling the web demo to access the research agent remotely.

## Key Challenges & Solutions

### 1. Data Storage Strategy
The enriched corpus consists of ~70 JSON files (~10-50MB total). Options:

**Option A: Include in Git Repository (Recommended for Demo)**
- Temporarily add data files to git for deployment
- Simple, works immediately
- Suitable for demo purposes

**Option B: Use Railway Volumes (Production Approach)**
- Create persistent volume for data
- Upload data separately
- Better for production, more complex

### 2. Step-by-Step Deployment Plan

#### Phase 1: Prepare Repository
```bash
# 1. Create deployment branch
git checkout -b railway-deployment

# 2. Temporarily include data in git
mv .gitignore .gitignore.bak
echo "# Temporary for Railway deployment" > .gitignore
echo "__pycache__/" >> .gitignore
echo "*.pyc" >> .gitignore
echo ".env" >> .gitignore
echo ".venv/" >> .gitignore
echo "venv/" >> .gitignore

# 3. Add the enriched data
git add data/processed/enriched/
git commit -m "Include enriched corpus data for Railway deployment"

# 4. Ensure all dependencies are captured
git add -A
git commit -m "Prepare for Railway deployment"
```

#### Phase 2: Railway Configuration

1. **Create `railway.json`:**
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn stream_cli_output_simple:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

2. **Update `Procfile`:**
```
web: uvicorn stream_cli_output_simple:app --host 0.0.0.0 --port $PORT
```

3. **Create `runtime.txt`:**
```
python-3.11.x
```

#### Phase 3: Environment Variables
Set in Railway dashboard:
- `MOONSHOT_API_KEY`: Your Moonshot API key
- `GROQ_API_KEY`: Your Groq API key (if using)
- `PORT`: (Railway sets automatically)

#### Phase 4: Deploy to Railway

```bash
# 1. Push to GitHub
git push origin railway-deployment

# 2. In Railway:
# - Create new project
# - Deploy from GitHub repo (railway-deployment branch)
# - Add environment variables
# - Deploy
```

#### Phase 5: Update Frontend

Update `cli-terminal.html`:
```javascript
const API_URL = 'https://your-app.up.railway.app'; // Replace with your Railway URL
```

### 3. Testing Strategy

1. **Health Check:**
```bash
curl https://your-app.up.railway.app/health
```

2. **Test Query:**
```bash
curl -X POST https://your-app.up.railway.app/stream-research \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the main concerns?", "provider": "moonshot", "max_iterations": 5}'
```

### 4. Optimization for Production

#### Memory Optimization
Add to `stream_cli_output_simple.py`:
```python
# Preload data at startup to avoid subprocess memory issues
import sys
sys.path.insert(0, '.')
from src.cli.enriched_cli import EnrichedUruguayCLI

# Initialize once at module level
cli = EnrichedUruguayCLI()
```

#### Alternative: Direct API Implementation
Instead of subprocess, directly call the research functions:
```python
# In stream_cli_output_simple.py
async def stream_research_direct(request: ResearchRequest):
    """Direct implementation without subprocess"""
    from src.agent.research_agent import InterviewResearchAgent
    from src.agent.config import AgentConfig
    
    config = AgentConfig(
        provider=request.provider,
        max_iterations=request.max_iterations,
        research_mode=False,
        debug=False,
        width=80
    )
    
    agent = InterviewResearchAgent(config)
    # Stream results directly...
```

### 5. Troubleshooting Guide

#### Common Issues:
1. **502 Bad Gateway**: Check logs, ensure PORT is used correctly
2. **Memory Issues**: Railway has memory limits, optimize data loading
3. **Timeout Issues**: Add health checks, implement connection pooling
4. **CORS Issues**: Ensure headers are set correctly

#### Debug Commands:
```bash
# View logs
railway logs

# Check deployment status
railway status

# Run locally with Railway environment
railway run python stream_cli_output_simple.py
```

### 6. Post-Deployment Cleanup

After successful demo:
```bash
# Switch back to main branch
git checkout main

# Restore original .gitignore
mv .gitignore.bak .gitignore

# Remove deployment branch (optional)
git branch -D railway-deployment
```

### 7. Alternative: Docker Deployment

If Railway deployment is problematic, create a Dockerfile:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "stream_cli_output_simple:app", "--host", "0.0.0.0", "--port", "8001"]
```

## Quick Start Commands

```bash
# 1. Prepare for deployment
git checkout -b railway-deployment
mv .gitignore .gitignore.bak
echo "__pycache__/\n*.pyc\n.env\n.venv/\nvenv/" > .gitignore
git add data/processed/enriched/
git commit -m "Include corpus data for Railway deployment"

# 2. Push to GitHub
git push origin railway-deployment

# 3. Deploy on Railway
# - Connect GitHub repo
# - Select railway-deployment branch
# - Add environment variables
# - Deploy

# 4. Update frontend with Railway URL
# Edit cli-terminal.html to use your Railway URL

# 5. Test deployment
curl https://your-app.up.railway.app/health
```

## Security Note
Including data in git is only recommended for demos. For production:
- Use Railway Volumes or external storage
- Implement proper authentication
- Use environment-specific data loading