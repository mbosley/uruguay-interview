#!/usr/bin/env python3
"""
View unified logs from frontend and backend
"""

import json
import sys
from datetime import datetime
from pathlib import Path

def view_logs(session_file=None):
    """View logs from a session file"""
    
    if not session_file:
        # Find most recent log file
        log_files = sorted(Path("unified_logs").glob("session_*.jsonl"))
        if not log_files:
            print("No log files found")
            return
        session_file = log_files[-1]
    
    print(f"📁 Viewing logs from: {session_file}")
    print("=" * 80)
    
    with open(session_file, 'r') as f:
        for line in f:
            try:
                log = json.loads(line)
                
                # Format timestamp
                ts = datetime.fromisoformat(log['timestamp']).strftime("%H:%M:%S.%f")[:-3]
                
                # Source emoji
                source_emoji = "🌐" if log['source'] == "frontend" else "🐍"
                
                # Level emoji
                level_emoji = {
                    "error": "❌",
                    "warn": "⚠️",
                    "info": "ℹ️",
                    "debug": "🔍",
                    "success": "✅"
                }.get(log['level'], "📝")
                
                # Print main log line
                print(f"{ts} {source_emoji} [{log['source']:8}] {level_emoji} {log['message']}")
                
                # Print data if present
                if log.get('data'):
                    # Special handling for WebSocket events
                    if log['message'].startswith('WebSocket Event:'):
                        event_data = log['data'].get('event_data', {})
                        event_type = log['data'].get('event_type', 'unknown')
                        
                        if event_type in ['thinking', 'tool_call', 'tool_result']:
                            iteration = event_data.get('iteration', 'N/A')
                            print(f"{'':19} Iteration: {iteration}")
                            
                        if 'data' in event_data:
                            # Pretty print event data
                            data_str = json.dumps(event_data['data'], indent=2)
                            for line in data_str.split('\n'):
                                print(f"{'':19} {line}")
                    else:
                        # Regular data
                        data_str = json.dumps(log['data'], indent=2)
                        if len(data_str) < 200:
                            for line in data_str.split('\n'):
                                print(f"{'':19} {line}")
                
            except json.JSONDecodeError:
                print(f"Invalid log line: {line}")

if __name__ == "__main__":
    session_file = sys.argv[1] if len(sys.argv) > 1 else None
    view_logs(session_file)