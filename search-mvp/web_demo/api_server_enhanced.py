"""
Enhanced FastAPI server with WebSocket support for real-time research updates
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import asyncio
import uuid
import json
import os
import sys
import re
from datetime import datetime
from pathlib import Path

sys.path.append('..')

from interview_research_agent_improved import InterviewResearchAgent
from config.providers import get_provider_config, PROVIDERS
from corpus_loader_api import load_enriched_corpus

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
    provider: Optional[str] = "moonshot"
    max_iterations: Optional[int] = 8

class ResearchResponse(BaseModel):
    job_id: str
    status: str
    message: str

class InterviewSummary(BaseModel):
    id: str
    title: str
    date: str
    location: Optional[str]
    themes: List[str]
    turns: int

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, job_id: str):
        await websocket.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = []
        self.active_connections[job_id].append(websocket)

    def disconnect(self, websocket: WebSocket, job_id: str):
        if job_id in self.active_connections:
            self.active_connections[job_id].remove(websocket)
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]

    async def send_message(self, job_id: str, message: dict):
        if job_id in self.active_connections:
            message['timestamp'] = datetime.now().isoformat()
            disconnected = []
            for connection in self.active_connections[job_id]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.append(connection)
            
            # Clean up disconnected
            for conn in disconnected:
                self.disconnect(conn, job_id)

manager = ConnectionManager()

# In-memory job storage
jobs = {}

# Load corpus once
corpus = None
try:
    corpus = load_enriched_corpus()
except:
    print("Warning: Could not load corpus")

async def monitor_research_log(job_id: str, log_file: Path):
    """Monitor the agent log file and send updates via WebSocket"""
    last_size = 0
    current_iteration = 0
    current_trace = None
    
    while job_id in jobs and jobs[job_id]['status'] == 'running':
        try:
            if log_file.exists() and log_file.stat().st_size > last_size:
                with open(log_file, 'r', encoding='utf-8') as f:
                    f.seek(last_size)
                    new_content = f.read()
                    last_size = f.tell()
                
                # Parse log lines
                for line in new_content.strip().split('\n'):
                    if not line.strip():
                        continue
                    
                    # Extract content after timestamp and log level
                    parts = line.split('|', 2)
                    if len(parts) > 2:
                        content = parts[2].strip()
                    else:
                        content = line
                    
                    # Parse different types of log entries
                    if '🔄 Iteration' in content:
                        match = re.search(r'Iteration (\d+)/(\d+)', content)
                        if match:
                            current_iteration = int(match.group(1))
                            current_trace = {
                                'iteration': current_iteration,
                                'steps': [],
                                'timestamp': datetime.now().isoformat()
                            }
                            await manager.send_message(job_id, {
                                'type': 'trace',
                                'data': current_trace
                            })
                    
                    elif '💭' in content and current_trace:
                        # Thinking step
                        step = {
                            'type': 'thinking',
                            'content': content.replace('💭', '').strip(),
                            'status': 'complete'
                        }
                        current_trace['steps'].append(step)
                        await manager.send_message(job_id, {
                            'type': 'thinking',
                            'data': {'content': step['content']}
                        })
                    
                    elif '🔧' in content and current_trace:
                        # Tool call
                        tool_match = re.search(r'Using tool: (\w+)', content)
                        if tool_match:
                            tool_name = tool_match.group(1)
                            step = {
                                'type': 'tool',
                                'tool': tool_name,
                                'content': f"Calling {tool_name}",
                                'status': 'active'
                            }
                            current_trace['steps'].append(step)
                            await manager.send_message(job_id, {
                                'type': 'tool_call',
                                'data': {
                                    'tool': tool_name,
                                    'description': content
                                }
                            })
                    
                    elif '📊 Tool Result:' in content and current_trace and current_trace['steps']:
                        # Tool result
                        if current_trace['steps'][-1]['type'] == 'tool':
                            current_trace['steps'][-1]['status'] = 'complete'
                            current_trace['steps'][-1]['results'] = content.replace('📊 Tool Result:', '').strip()[:100] + '...'
                            
                            await manager.send_message(job_id, {
                                'type': 'trace',
                                'data': current_trace
                            })
            
            await asyncio.sleep(0.1)
            
        except Exception as e:
            print(f"Error monitoring log: {e}")
            await asyncio.sleep(0.5)

async def run_research_job(job_id: str, question: str, provider: str, max_iterations: int):
    """Run the research agent and update job status"""
    try:
        jobs[job_id] = {
            'status': 'running',
            'question': question,
            'started_at': datetime.now().isoformat()
        }
        
        # Create log file path
        log_file = Path(f"logs/research_{job_id}.log")
        log_file.parent.mkdir(exist_ok=True)
        
        # Start log monitoring
        monitor_task = asyncio.create_task(monitor_research_log(job_id, log_file))
        
        # Initialize agent with custom log file
        agent = InterviewResearchAgent(
            provider=provider,
            verbose=True,
            research_mode=True,
            log_file=str(log_file)
        )
        
        # Run research
        start_time = datetime.now()
        results = await agent.autonomous_research(question, max_iterations=max_iterations)
        end_time = datetime.now()
        
        # Calculate final stats
        stats = results.get('stats', {})
        stats['duration'] = (end_time - start_time).total_seconds()
        
        # Extract sources from the response
        sources = []
        if 'tool_calls' in results:
            for call in results['tool_calls']:
                if 'result' in call and 'Interview' in str(call['result']):
                    # Extract interview IDs
                    matches = re.findall(r'Interview (\d{3})', str(call['result']))
                    sources.extend([f"Interview {id}" for id in matches])
        sources = list(set(sources))[:5]  # Unique, max 5
        
        # Send final result
        await manager.send_message(job_id, {
            'type': 'result',
            'data': {
                'response': results.get('final_response', 'No response generated'),
                'sources': sources,
                'stats': stats
            }
        })
        
        # Update job status
        jobs[job_id] = {
            'status': 'completed',
            'question': question,
            'results': results,
            'completed_at': datetime.now().isoformat()
        }
        
        # Stop monitoring
        await monitor_task
        
    except Exception as e:
        error_msg = str(e)
        await manager.send_message(job_id, {
            'type': 'error',
            'data': {'error': error_msg}
        })
        
        jobs[job_id] = {
            'status': 'failed',
            'question': question,
            'error': error_msg,
            'failed_at': datetime.now().isoformat()
        }

@app.post("/research", response_model=ResearchResponse)
async def start_research(request: ResearchRequest, background_tasks: BackgroundTasks):
    """Start a new research job"""
    job_id = str(uuid.uuid4())
    
    # Validate provider
    if request.provider and request.provider not in PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {request.provider}")
    
    # Start job in background
    background_tasks.add_task(
        run_research_job,
        job_id,
        request.question,
        request.provider or "moonshot",
        request.max_iterations
    )
    
    return ResearchResponse(
        job_id=job_id,
        status="started",
        message=f"Research job {job_id} started"
    )

@app.get("/research/{job_id}")
async def get_job_status(job_id: str):
    """Get research job status"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return jobs[job_id]

@app.websocket("/research/{job_id}/stream")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for real-time research updates"""
    await manager.connect(websocket, job_id)
    try:
        while True:
            # Keep connection alive
            await asyncio.sleep(1)
            if job_id not in jobs:
                await websocket.close()
                break
            if jobs[job_id]['status'] in ['completed', 'failed']:
                await asyncio.sleep(1)
                await websocket.close()
                break
    except WebSocketDisconnect:
        manager.disconnect(websocket, job_id)

@app.get("/interviews", response_model=List[InterviewSummary])
async def get_interviews():
    """Get list of all interviews"""
    if not corpus:
        raise HTTPException(status_code=500, detail="Corpus not loaded")
    
    interviews = []
    for interview_id, interview_data in corpus.items():
        # Extract themes from annotations
        themes = []
        if 'annotation' in interview_data and 'summary' in interview_data['annotation']:
            if 'key_themes' in interview_data['annotation']['summary']:
                themes = [theme['theme'] for theme in interview_data['annotation']['summary']['key_themes'][:3]]
        
        interviews.append(InterviewSummary(
            id=interview_id,
            title=f"Interview {interview_id}",
            date=interview_data.get('metadata', {}).get('date', '2025-05-28'),
            location=interview_data.get('metadata', {}).get('location'),
            themes=themes,
            turns=len(interview_data.get('turns', []))
        ))
    
    return sorted(interviews, key=lambda x: x.id)

@app.get("/interviews/{interview_id}")
async def get_interview(interview_id: str):
    """Get specific interview content"""
    if not corpus:
        raise HTTPException(status_code=500, detail="Corpus not loaded")
    
    if interview_id not in corpus:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    return corpus[interview_id]

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "corpus_loaded": corpus is not None}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)