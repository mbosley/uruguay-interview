"""
Enhanced FastAPI server with WebSocket support for real-time research updates
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
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
from dotenv import load_dotenv
from json import JSONEncoder
from concurrent.futures import ThreadPoolExecutor
import threading

# Load environment variables
load_dotenv()

# Custom JSON encoder to handle datetime objects
class DateTimeEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

from interview_research_agent_improved import InterviewResearchAgent
from mock_research_agent import MockResearchAgent
from config.providers import get_provider_config, PROVIDERS
from web_demo.corpus_loader_api import load_enriched_corpus
from unified_backend_logger import unified_logger
from event_store import event_store

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
    use_mock: Optional[bool] = False  # For testing frontend
    test_mode: Optional[bool] = False  # Quick test with fewer iterations

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

# WebSocket connection manager with event buffering
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.event_buffers: Dict[str, List[dict]] = {}
        self.buffer_metadata: Dict[str, dict] = {}
        self.max_buffer_size = 1000

    async def connect(self, websocket: WebSocket, job_id: str):
        # WebSocket already accepted in the endpoint
        
        # Send any buffered events to the new client
        if job_id in self.event_buffers and self.event_buffers[job_id]:
            print(f"Replaying {len(self.event_buffers[job_id])} buffered events for job {job_id}")
            for event in self.event_buffers[job_id]:
                try:
                    json_str = json.dumps(event, cls=DateTimeEncoder)
                    await websocket.send_text(json_str)
                    await asyncio.sleep(0.01)  # Small delay between events for smoother replay
                except:
                    break
        
        # Mark that a client has connected
        if job_id in self.buffer_metadata:
            self.buffer_metadata[job_id]['client_connected'] = True
        
        # Add to active connections
        if job_id not in self.active_connections:
            self.active_connections[job_id] = []
        self.active_connections[job_id].append(websocket)

    def disconnect(self, websocket: WebSocket, job_id: str):
        if job_id in self.active_connections:
            self.active_connections[job_id].remove(websocket)
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]

    async def send_message(self, job_id: str, message: dict):
        message['timestamp'] = datetime.now().isoformat()
        
        # Initialize buffer if needed
        if job_id not in self.event_buffers:
            self.event_buffers[job_id] = []
            self.buffer_metadata[job_id] = {
                'created_at': datetime.now(),
                'client_connected': False
            }
        
        # Buffer the event if no client connected yet or buffer is still active
        if not self.buffer_metadata[job_id]['client_connected'] and len(self.event_buffers[job_id]) < self.max_buffer_size:
            print(f"[{datetime.now()}] Buffering event for job {job_id}: {message['type']}")
            self.event_buffers[job_id].append(message)
        
        # Send to connected clients
        if job_id in self.active_connections:
            print(f"[{datetime.now()}] Sending event to {len(self.active_connections[job_id])} clients: {message['type']}")
            disconnected = []
            # Serialize the message using our custom encoder
            json_str = json.dumps(message, cls=DateTimeEncoder)
            for connection in self.active_connections[job_id]:
                try:
                    await connection.send_text(json_str)
                except:
                    disconnected.append(connection)
            
            # Clean up disconnected
            for conn in disconnected:
                self.disconnect(conn, job_id)
        else:
            print(f"[{datetime.now()}] No active connections for job {job_id}")
    
    def cleanup_buffer(self, job_id: str):
        """Clean up buffers for completed jobs"""
        self.event_buffers.pop(job_id, None)
        self.buffer_metadata.pop(job_id, None)

manager = ConnectionManager()

# In-memory job storage
jobs = {}

# Load corpus once
corpus = None
print("Loading corpus...")
try:
    corpus = load_enriched_corpus()
    if corpus:
        print(f"Corpus loaded successfully with {len(corpus)} interviews")
    else:
        print("Warning: Corpus is None")
except Exception as e:
    print(f"Error loading corpus: {e}")
    import traceback
    traceback.print_exc()


async def run_research_job(job_id: str, question: str, provider: str, max_iterations: int, use_mock: bool = False, test_mode: bool = False):
    """Run the research agent and update job status"""
    print(f"[{datetime.now()}] Starting research job {job_id} with question: {question}")
    print(f"[{datetime.now()}] Test mode: {test_mode}, Max iterations: {max_iterations}")
    print(f"[{datetime.now()}] Current event loop: {asyncio.get_running_loop()}")
    print(f"[{datetime.now()}] Thread: {threading.current_thread().name}")
    try:
        jobs[job_id] = {
            'status': 'running',
            'question': question,
            'started_at': datetime.now().isoformat()
        }
        
        # Define callback to publish events to event store
        async def event_callback(event: Dict):
            # Log the event
            unified_logger.event(event.get('type', 'unknown'), event)
            # Publish to event store (non-blocking)
            event_store.publish(f"job:{job_id}", event)
            print(f"[{datetime.now()}] Published event {event.get('type')} to job:{job_id}")
        
        # Initialize agent (mock or real based on flag)
        if use_mock:
            print(f"Using MOCK agent for job {job_id}")
            agent = MockResearchAgent(event_callback=event_callback)
        else:
            agent = InterviewResearchAgent(
                provider=provider,
                verbose=True,
                research_mode=False,  # Don't need extra logging for web
                event_callback=event_callback
            )
        
        # Run research
        start_time = datetime.now()
        results = await agent.autonomous_research(question, max_iterations=max_iterations)
        end_time = datetime.now()
        
        # Extract sources from the response
        sources = []
        if 'tool_calls' in results:
            for call in results['tool_calls']:
                if 'result' in call and 'Interview' in str(call['result']):
                    # Extract interview IDs
                    matches = re.findall(r'Interview (\d{3})', str(call['result']))
                    sources.extend([f"Interview {id}" for id in matches])
        
        # Also check the final response for interview mentions
        if 'final_response' in results:
            response_matches = re.findall(r'Interview (\d{3})', results['final_response'])
            sources.extend([f"Interview {id}" for id in response_matches])
        
        sources = list(set(sources))[:5]  # Unique, max 5
        
        # For backwards compatibility, also send a "result" event
        event_store.publish(f"job:{job_id}", {
            'type': 'result',
            'data': {
                'response': results.get('final_response', 'No response generated'),
                'sources': sources,
                'stats': results.get('stats', {})
            },
            'timestamp': datetime.now().isoformat()
        })
        
        # Update job status
        jobs[job_id] = {
            'status': 'completed',
            'question': question,
            'results': results,
            'completed_at': datetime.now().isoformat()
        }
        
        # Note: Event store keeps events until explicitly cleared
        # This allows late-connecting clients to get all events
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error in research job {job_id}: {error_msg}")
        import traceback
        traceback.print_exc()
        
        event_store.publish(f"job:{job_id}", {
            'type': 'error',
            'data': {'error': error_msg},
            'timestamp': datetime.now().isoformat()
        })
        
        jobs[job_id] = {
            'status': 'failed',
            'question': question,
            'error': error_msg,
            'failed_at': datetime.now().isoformat()
        }

@app.post("/research", response_model=ResearchResponse)
async def start_research(request: ResearchRequest):
    """Start a new research job"""
    job_id = str(uuid.uuid4())
    print(f"==> [{datetime.now()}] POST /research - Request received")
    print(f"Request: question='{request.question}', provider='{request.provider}'")
    
    # Validate provider
    if request.provider and request.provider not in PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {request.provider}")
    
    # Initialize job status immediately
    jobs[job_id] = {
        'status': 'pending',
        'question': request.question,
        'created_at': datetime.now().isoformat()
    }
    
    print(f"==> [{datetime.now()}] About to create async task for job {job_id}")
    
    # Adjust iterations for test mode
    max_iterations = 2 if request.test_mode else (request.max_iterations or 8)
    
    # Create task with explicit name and log any errors
    task = asyncio.create_task(
        run_research_job(
            job_id,
            request.question,
            request.provider or "moonshot",
            max_iterations,
            request.use_mock,
            request.test_mode
        ),
        name=f"research-{job_id}"
    )
    
    # Add error logging
    def log_task_exception(task):
        try:
            task.result()
        except Exception as e:
            print(f"Task {task.get_name()} failed with exception: {e}")
    
    task.add_done_callback(log_task_exception)
    
    # Force a yield to allow other tasks to run
    await asyncio.sleep(0)
    
    print(f"==> [{datetime.now()}] Task created. Returning response for {job_id}")
    
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
    print(f"[{datetime.now()}] WebSocket connection attempt for job {job_id}")
    
    # Accept the WebSocket connection immediately
    await websocket.accept()
    print(f"[{datetime.now()}] WebSocket accepted for job {job_id}")
    
    if job_id not in jobs:
        print(f"Job {job_id} not found in jobs: {list(jobs.keys())}")
        await websocket.close(code=1008, reason="Job not found")
        return
    
    # Subscribe to events from event store
    event_channel = f"job:{job_id}"
    queue = await event_store.subscribe(event_channel)
    print(f"[{datetime.now()}] Subscribed to event store channel: {event_channel}")
    
    try:
        # Stream events from the queue
        while True:
            try:
                # Wait for events with timeout
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                
                # Send event to WebSocket
                json_str = json.dumps(event, cls=DateTimeEncoder)
                await websocket.send_text(json_str)
                print(f"[{datetime.now()}] Sent event {event.get('type')} to WebSocket")
                
                # Check if this is a terminal event
                if event.get('type') in ['response_end', 'error', 'result']:
                    print(f"[{datetime.now()}] Terminal event received, closing WebSocket")
                    await asyncio.sleep(0.5)  # Give client time to process
                    break
                    
            except asyncio.TimeoutError:
                # Check if job is still running
                if job_id in jobs and jobs[job_id]['status'] in ['completed', 'failed']:
                    print(f"[{datetime.now()}] Job completed but no more events, closing")
                    break
                # Otherwise continue waiting
                
    except WebSocketDisconnect:
        print(f"[{datetime.now()}] Client disconnected")
    except Exception as e:
        print(f"[{datetime.now()}] WebSocket error: {e}")
        await websocket.send_json({
            'type': 'error',
            'data': {'error': str(e)},
            'timestamp': datetime.now().isoformat()
        })
    finally:
        # Cleanup
        event_store.unsubscribe(event_channel, queue)
        await websocket.close()
        print(f"[{datetime.now()}] WebSocket closed for job {job_id}")

@app.websocket("/test/echo")
async def test_websocket_echo(websocket: WebSocket):
    """Simple echo WebSocket for testing"""
    await websocket.accept()
    print(f"[{datetime.now()}] Test WebSocket connected")
    
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        print(f"[{datetime.now()}] Test WebSocket disconnected")

@app.get("/research/{job_id}/events")
async def research_events_sse(job_id: str):
    """Server-sent events endpoint for research updates"""
    from fastapi.responses import StreamingResponse
    
    print(f"[{datetime.now()}] SSE connection for job {job_id}")
    
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    async def event_generator():
        # Subscribe to events from event store
        event_channel = f"job:{job_id}"
        queue = await event_store.subscribe(event_channel)
        print(f"[{datetime.now()}] SSE subscribed to channel: {event_channel}")
        
        try:
            while True:
                try:
                    # Wait for events with timeout
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    
                    # Format as SSE
                    json_str = json.dumps(event, cls=DateTimeEncoder)
                    yield f"data: {json_str}\n\n"
                    print(f"[{datetime.now()}] SSE sent event: {event.get('type')}")
                    
                    # Check if this is a terminal event
                    if event.get('type') in ['response_end', 'error', 'result']:
                        print(f"[{datetime.now()}] SSE terminal event, closing")
                        break
                        
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield ": keepalive\n\n"
                    
                    # Check if job is complete
                    if job_id in jobs and jobs[job_id]['status'] in ['completed', 'failed']:
                        print(f"[{datetime.now()}] SSE job completed, closing")
                        break
                        
        except Exception as e:
            print(f"[{datetime.now()}] SSE error: {e}")
            error_event = {
                'type': 'error',
                'data': {'error': str(e)},
                'timestamp': datetime.now().isoformat()
            }
            yield f"data: {json.dumps(error_event)}\n\n"
        finally:
            # Cleanup
            event_store.unsubscribe(event_channel, queue)
            print(f"[{datetime.now()}] SSE connection closed for job {job_id}")
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )

@app.get("/interviews", response_model=List[InterviewSummary])
async def get_interviews():
    """Get list of all interviews"""
    if not corpus:
        raise HTTPException(status_code=500, detail="Corpus not loaded")
    
    interviews = []
    for interview_id, interview_data in corpus.items():
        # Extract themes from annotations
        themes = []
        if 'annotation' in interview_data:
            # Check for themes in different possible locations
            if 'key_themes' in interview_data['annotation']:
                # Direct key_themes array
                themes = [theme.get('theme', theme) if isinstance(theme, dict) else str(theme) 
                         for theme in interview_data['annotation']['key_themes'][:3]]
            elif 'summary' in interview_data['annotation'] and 'key_themes' in interview_data['annotation']['summary']:
                # Nested in summary
                themes = [theme.get('theme', theme) if isinstance(theme, dict) else str(theme) 
                         for theme in interview_data['annotation']['summary']['key_themes'][:3]]
        
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
    
    # Ensure proper JSON serialization
    from fastapi.responses import JSONResponse
    return JSONResponse(content=corpus[interview_id], media_type="application/json")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "corpus_loaded": corpus is not None}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)