"""
FastAPI server for the research agent
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
import uuid
import os
import sys
sys.path.append('..')

from interview_research_agent_improved import InterviewResearchAgent
from config.providers import get_provider_config, PROVIDERS

app = FastAPI(title="Uruguay Interview Research API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ResearchRequest(BaseModel):
    question: str
    provider: Optional[str] = None
    max_iterations: Optional[int] = 10

class ResearchResponse(BaseModel):
    job_id: str
    status: str
    message: str

class ResearchResult(BaseModel):
    job_id: str
    status: str
    question: str
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# In-memory job storage (use Redis in production)
jobs = {}

async def run_research_job(job_id: str, question: str, provider: str, max_iterations: int):
    """Background task to run research"""
    try:
        jobs[job_id]['status'] = 'running'
        
        agent = InterviewResearchAgent(
            provider=provider,
            verbose=False,
            research_mode=True
        )
        
        results = await agent.autonomous_research(question, max_iterations=max_iterations)
        
        jobs[job_id]['status'] = 'completed'
        jobs[job_id]['results'] = results
        
    except Exception as e:
        jobs[job_id]['status'] = 'failed'
        jobs[job_id]['error'] = str(e)

@app.get("/")
def root():
    return {
        "message": "Uruguay Interview Research API",
        "endpoints": {
            "/providers": "List available LLM providers",
            "/research": "Submit a research question",
            "/research/{job_id}": "Get research results",
            "/corpus/stats": "Get corpus statistics"
        }
    }

@app.get("/providers")
def get_providers():
    """List available providers and their configurations"""
    providers_info = {}
    for name, config in PROVIDERS.items():
        providers_info[name] = {
            "description": config.description,
            "speed": f"{config.tokens_per_second} tokens/sec",
            "cost_input": f"${config.cost_per_1k_input:.4f}/1k tokens",
            "cost_output": f"${config.cost_per_1k_output:.4f}/1k tokens",
            "available": bool(os.getenv(config.api_key_env))
        }
    
    current = get_provider_config()
    return {
        "providers": providers_info,
        "current": current.name
    }

@app.post("/research", response_model=ResearchResponse)
async def submit_research(request: ResearchRequest, background_tasks: BackgroundTasks):
    """Submit a research question for processing"""
    
    # Validate provider
    if request.provider and request.provider not in PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {request.provider}")
    
    provider = request.provider or get_provider_config().name
    
    # Check if provider is available
    provider_config = PROVIDERS[provider]
    if not os.getenv(provider_config.api_key_env):
        raise HTTPException(
            status_code=400, 
            detail=f"Provider {provider} not configured. Set {provider_config.api_key_env}"
        )
    
    # Create job
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        'status': 'pending',
        'question': request.question,
        'provider': provider,
        'results': None,
        'error': None
    }
    
    # Start background task
    background_tasks.add_task(
        run_research_job,
        job_id,
        request.question,
        provider,
        request.max_iterations
    )
    
    return ResearchResponse(
        job_id=job_id,
        status="pending",
        message="Research job submitted successfully"
    )

@app.get("/research/{job_id}", response_model=ResearchResult)
def get_research_results(job_id: str):
    """Get results of a research job"""
    
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    return ResearchResult(
        job_id=job_id,
        status=job['status'],
        question=job['question'],
        results=job.get('results'),
        error=job.get('error')
    )

@app.get("/corpus/stats")
async def get_corpus_stats():
    """Get basic corpus statistics"""
    # Run a simple corpus stats query
    agent = InterviewResearchAgent(
        provider=get_provider_config().name,
        verbose=False
    )
    
    # Just get corpus stats
    from src.cli.enriched_cli import EnrichedCLI
    cli = EnrichedCLI()
    stats = cli.stats()
    
    return stats

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)