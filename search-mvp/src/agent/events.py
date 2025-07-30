"""Event handling for the research agent"""

import json
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional


class EventHandler:
    """Handles event emission for the research agent"""
    
    def __init__(self, event_store_path: Optional[str] = None):
        self.event_store_path = event_store_path or "event_store.py"
        self.session_id = None
    
    def set_session_id(self, session_id: str):
        """Set the session ID for event tracking"""
        self.session_id = session_id
    
    async def emit_event(self, event_type: str, data: Dict[str, Any], iteration: Optional[int] = None):
        """Emit an event to the event store"""
        if not self.session_id:
            return
            
        try:
            # Import event_store module dynamically
            import sys
            import os
            sys.path.insert(0, os.path.dirname(self.event_store_path))
            
            from event_store import event_store
            
            # Create event with metadata
            event = {
                "session_id": self.session_id,
                "type": event_type,
                "timestamp": datetime.now().isoformat(),
                "data": data
            }
            
            if iteration is not None:
                event["iteration"] = iteration
            
            # Publish event to store
            event_store.publish(self.session_id, event)
            
            # Force yield to allow SSE to process events immediately
            await asyncio.sleep(0)
            
        except Exception as e:
            # Log error but don't fail the research
            print(f"Warning: Could not emit event: {e}")
    
    def _extract_sources(self, text: str) -> list:
        """Extract citation sources from text"""
        import re
        # Look for patterns like [[064:23]] or [[071:summary]]
        pattern = r'\[\[(\d{3}):(\w+)\]\]'
        matches = re.findall(pattern, text)
        
        sources = []
        for interview_id, turn_id in matches:
            sources.append({
                "interview": interview_id,
                "turn": turn_id,
                "reference": f"{interview_id}:{turn_id}"
            })
        
        return sources