#!/usr/bin/env python3
"""
Dead simple API endpoint that streams CLI output directly
"""

import asyncio
import subprocess
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import sys
import os
from datetime import datetime

# Add parent directory to path to import corpus loader
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from archived.web_demo.corpus_loader import load_enriched_corpus

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load corpus once at startup
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

class ResearchRequest(BaseModel):
    question: str
    provider: Optional[str] = "moonshot"
    max_iterations: Optional[int] = 15

class InterviewSummary(BaseModel):
    id: str
    title: str
    date: str
    location: Optional[str] = None
    themes: List[str] = []
    turns: int = 0

@app.get("/")
async def root():
    return {"status": "API is running", "endpoints": ["/interviews", "/stream-research"]}

@app.options("/stream-research")
async def stream_research_options():
    return {"message": "OK"}

@app.post("/stream-research")
async def stream_research(request: ResearchRequest):
    """Stream the raw CLI output from running the research agent"""
    
    async def run_command():
        # Build the command
        cmd = [
            sys.executable,
            "run_agent.py",
            "--question", request.question,
            "--provider", request.provider,
            "--max-iterations", str(request.max_iterations)
        ]
        
        # Start the process
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        # Stream output line by line
        async for line in process.stdout:
            text = line.decode('utf-8', errors='replace')
            # Remove the newline at the end but preserve the line
            # Empty lines should be sent as empty strings
            content = text.rstrip('\n\r')
            # Escape backslashes for SSE format
            escaped = content.replace('\\', '\\\\')
            yield f"data: {escaped}\n\n"
        
        # Wait for process to complete
        await process.wait()
        
        # Send completion event
        yield f"data: [DONE]\n\n"
    
    return StreamingResponse(
        run_command(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "*"
        }
    )

@app.get("/interviews")
async def get_interviews():
    """Get list of all interviews"""
    if not corpus:
        raise HTTPException(status_code=500, detail="Corpus not loaded")
    
    # Handle nested structure
    interview_data = corpus.get('interviews', corpus)
    
    interviews = []
    for interview_id, interview in interview_data.items():
        # Extract themes from annotations
        themes = []
        if 'annotation' in interview:
            # Check for themes in different possible locations
            if 'key_themes' in interview['annotation']:
                # Direct key_themes array
                themes = [theme.get('theme', theme) if isinstance(theme, dict) else str(theme) 
                         for theme in interview['annotation']['key_themes'][:3]]
            elif 'summary' in interview['annotation'] and 'key_themes' in interview['annotation']['summary']:
                # Nested in summary
                themes = [theme.get('theme', theme) if isinstance(theme, dict) else str(theme) 
                         for theme in interview['annotation']['summary']['key_themes'][:3]]
        
        interviews.append(InterviewSummary(
            id=interview_id,
            title=f"Interview {interview_id}",
            date=interview.get('metadata', {}).get('date', '2025-05-28'),
            location=interview.get('metadata', {}).get('location'),
            themes=themes,
            turns=len(interview.get('turns', []))
        ))
    
    return sorted(interviews, key=lambda x: x.id)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "corpus_loaded": corpus is not None}

@app.get("/debug/interviews")
async def debug_interviews():
    """Debug endpoint to see available interview IDs"""
    if not corpus:
        return {"error": "Corpus not loaded"}
    
    result = {
        "corpus_type": type(corpus).__name__,
        "corpus_keys": list(corpus.keys()) if hasattr(corpus, 'keys') else "not a dict",
    }
    
    # Check what corpus['interviews'] actually is
    if 'interviews' in corpus:
        interviews = corpus['interviews']
        result["interviews_type"] = type(interviews).__name__
        
        if hasattr(interviews, 'keys'):
            interview_keys = list(interviews.keys())
            result["num_interviews"] = len(interview_keys)
            result["sample_interview_ids"] = interview_keys[:5]
            
            # Check if '062' is in there
            result["has_062"] = '062' in interview_keys
            
            # Get actual interview data
            if '062' in interviews:
                interview_062 = interviews['062']
                result["interview_062_type"] = type(interview_062).__name__
                if hasattr(interview_062, 'keys'):
                    result["interview_062_keys"] = list(interview_062.keys())
                    
                    # Check for annotation
                    if 'annotation' in interview_062:
                        annotation = interview_062['annotation']
                        result["annotation_type"] = type(annotation).__name__
                        if hasattr(annotation, 'keys'):
                            result["annotation_keys"] = list(annotation.keys())
                    
                    # Check turns structure
                    if 'turns' in interview_062:
                        turns = interview_062['turns']
                        result["num_turns"] = len(turns) if isinstance(turns, list) else "not a list"
                        if isinstance(turns, list) and len(turns) > 0:
                            # Show first few turns
                            sample_turns = []
                            for i, turn in enumerate(turns[:3]):
                                sample_turns.append({
                                    "index": i,
                                    "turn_id": turn.get('turn_id', 'no turn_id'),
                                    "keys": list(turn.keys()) if hasattr(turn, 'keys') else "not a dict"
                                })
                            result["sample_turns"] = sample_turns
    
    return result

@app.get("/interviews/{interview_id}/full")
async def get_full_interview(interview_id: str):
    """Get full interview data with all enrichment"""
    try:
        if not corpus:
            raise HTTPException(status_code=503, detail="Corpus not loaded")
        
        # Pad interview ID to 3 digits
        interview_id = interview_id.zfill(3)
        
        # Handle nested structure
        interview_data = corpus.get('interviews', corpus)
        
        if interview_id not in interview_data:
            raise HTTPException(status_code=404, detail=f"Interview {interview_id} not found")
        
        # Get the interview data and clean up newlines in turns
        interview = interview_data[interview_id].copy()
        
        # Clean newlines from turn text for better display
        if 'turns' in interview:
            cleaned_turns = []
            for turn in interview['turns']:
                cleaned_turn = turn.copy()
                if 'text' in cleaned_turn:
                    cleaned_turn['text'] = cleaned_turn['text'].replace('\n', ' ').strip()
                cleaned_turns.append(cleaned_turn)
            interview['turns'] = cleaned_turns
        
        # Return the cleaned interview data
        return {
            "id": interview_id,
            **interview
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching full interview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/interviews/{interview_id}/turns/{turn_id}")
async def get_interview_turn(interview_id: str, turn_id: str):
    """Get a specific interview turn or summary for tooltip display"""
    try:
        # Ensure corpus is loaded
        if not corpus:
            raise HTTPException(status_code=503, detail="Corpus not loaded")
        
        # Pad interview ID to 3 digits
        interview_id = interview_id.zfill(3)
        
        # Handle nested structure - interviews are under corpus['interviews']
        interview_data = corpus.get('interviews', corpus)
        
        # Check if interview exists
        if interview_id not in interview_data:
            raise HTTPException(status_code=404, detail=f"Interview {interview_id} not found")
        
        interview = interview_data[interview_id]
        
        # Handle summary request
        if turn_id == 'summary':
            # Try different paths to find the summary
            summary_text = "No summary available"
            
            # Check for summary in different locations
            if 'annotation' in interview:
                annotation = interview['annotation']
                if isinstance(annotation, dict):
                    if 'summary' in annotation:
                        if isinstance(annotation['summary'], str):
                            summary_text = annotation['summary']
                        elif isinstance(annotation['summary'], dict) and 'overview' in annotation['summary']:
                            summary_text = annotation['summary']['overview']
                    elif 'overview' in annotation:
                        summary_text = annotation['overview']
            elif 'summary' in interview:
                summary_text = interview['summary']
            
            return {
                "interview_id": interview_id,
                "type": "summary",
                "summary": summary_text,
                "metadata": interview.get('metadata', {})
            }
        
        # Handle turn range request (e.g., "1-5")
        if '-' in turn_id:
            start_turn, end_turn = turn_id.split('-')
            try:
                start = int(start_turn)
                end = int(end_turn)
                
                # Collect turns in range
                turns_in_range = []
                for turn in interview.get('turns', []):
                    turn_num = turn.get('turn_id', '').split(':')[-1]
                    try:
                        if start <= int(turn_num) <= end:
                            turns_in_range.append({
                                "turn": turn_num,
                                "speaker": turn.get('speaker', 'Unknown'),
                                "text": turn.get('text', '').replace('\n', ' ').strip()
                            })
                    except ValueError:
                        continue
                
                if turns_in_range:
                    # Format the turns
                    combined_text = "\n\n".join([
                        f"[Turn {t['turn']}] {t['speaker']}: {t['text']}"
                        for t in sorted(turns_in_range, key=lambda x: int(x['turn']))
                    ])
                    
                    return {
                        "interview_id": interview_id,
                        "turn_id": f"{start}-{end}",
                        "type": "turn_range",
                        "speaker": "Multiple speakers",
                        "text": combined_text,
                        "num_turns": len(turns_in_range)
                    }
                else:
                    raise HTTPException(status_code=404, detail=f"No turns found in range {start}-{end}")
                    
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid turn range: {turn_id}")
        
        # Handle single turn request
        else:
            turn_key = f"{interview_id}:{turn_id.zfill(2)}"
            
            # Find the turn in the interview
            for turn in interview.get('turns', []):
                if turn.get('turn_id') == turn_key:
                    return {
                        "interview_id": interview_id,
                        "turn_id": turn_key,
                        "type": "turn",
                        "speaker": turn.get('speaker', 'Unknown'),
                        "text": turn.get('text', '').replace('\n', ' ').strip(),
                        "word_count": turn.get('word_count', 0)
                    }
            
            raise HTTPException(status_code=404, detail=f"Turn {turn_key} not found")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching interview turn: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)