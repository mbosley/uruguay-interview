#!/usr/bin/env python3
"""
Simple scratchpad tools for the research agent to track findings
"""

import os
from pathlib import Path
from datetime import datetime

class ScratchpadTools:
    def __init__(self, session_id=None):
        # Create scratchpad directory
        self.scratchpad_dir = Path(__file__).parent.parent.parent / "scratchpads"
        self.scratchpad_dir.mkdir(exist_ok=True)
        
        # Create session-specific scratchpad file
        if session_id:
            self.scratchpad_file = self.scratchpad_dir / f"session_{session_id}.md"
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.scratchpad_file = self.scratchpad_dir / f"session_{timestamp}.md"
    
    def append_to_scratchpad(self, content: str, entry_type: str = "NOTE"):
        """Append content to the scratchpad with timestamp and type"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Add entry with type and timestamp
        entry = f"\n\n[{entry_type}] {timestamp}\n{content}"
        
        # Append to file
        with open(self.scratchpad_file, 'a', encoding='utf-8') as f:
            f.write(entry)
        
        return f"Added {entry_type}: {len(content)} characters to scratchpad"
    
    def read_scratchpad(self):
        """Read the current scratchpad contents"""
        if not self.scratchpad_file.exists():
            return "Scratchpad is empty"
        
        with open(self.scratchpad_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return content if content else "Scratchpad is empty"
    
    def clear_scratchpad(self):
        """Clear the scratchpad (start fresh)"""
        if self.scratchpad_file.exists():
            self.scratchpad_file.unlink()
        return "Scratchpad cleared"

# CLI wrapper functions for the tools
def append_note(note: str, session_id: str = None):
    """Append a note to the research scratchpad"""
    tools = ScratchpadTools(session_id)
    return tools.append_to_scratchpad(note)

def read_notes(session_id: str = None):
    """Read all notes from the research scratchpad"""
    tools = ScratchpadTools(session_id)
    return tools.read_scratchpad()

def clear_notes(session_id: str = None):
    """Clear the research scratchpad"""
    tools = ScratchpadTools(session_id)
    return tools.clear_scratchpad()