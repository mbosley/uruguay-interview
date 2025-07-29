#!/usr/bin/env python3
"""
Unified logging server that collects logs from both frontend and backend
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import json
import uvicorn
from pathlib import Path

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create logs directory
Path("unified_logs").mkdir(exist_ok=True)

# Session log file
session_file = f"unified_logs/session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"

@app.post("/log")
async def log_event(request: Request):
    """Receive log events from frontend or backend"""
    try:
        data = await request.json()
        
        # Add timestamp and source
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "source": data.get("source", "unknown"),
            "level": data.get("level", "info"),
            "message": data.get("message", ""),
            "data": data.get("data", {})
        }
        
        # Write to file
        with open(session_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        # Also print to console with formatting
        source_emoji = "🌐" if log_entry["source"] == "frontend" else "🐍"
        level_emoji = {
            "error": "❌",
            "warn": "⚠️",
            "info": "ℹ️",
            "debug": "🔍",
            "success": "✅"
        }.get(log_entry["level"], "📝")
        
        print(f"{source_emoji} [{log_entry['source']:8}] {level_emoji} {log_entry['message']}")
        if log_entry["data"]:
            print(f"   Data: {json.dumps(log_entry['data'], indent=2)}")
        
        return {"status": "logged"}
    
    except Exception as e:
        print(f"Logging error: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/logs")
async def get_logs(limit: int = 100):
    """Retrieve recent logs"""
    logs = []
    try:
        with open(session_file, "r") as f:
            lines = f.readlines()
            for line in lines[-limit:]:
                logs.append(json.loads(line))
    except:
        pass
    return {"logs": logs}

if __name__ == "__main__":
    print(f"📊 Unified Logger Started")
    print(f"📁 Logging to: {session_file}")
    print(f"🌐 Frontend: Add logging code to send to http://localhost:8001/log")
    print(f"🐍 Backend: Modify agent to send logs to http://localhost:8001/log")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8001)