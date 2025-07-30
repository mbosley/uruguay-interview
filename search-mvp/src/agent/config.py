"""Configuration for the research agent"""

import os
from datetime import datetime
from typing import Optional


def get_session_id(prefix: str = "research") -> str:
    """Generate a unique session ID"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}"


def get_event_store_path() -> str:
    """Get the path to the event store"""
    return os.path.join(os.path.dirname(__file__), "..", "..", "event_store.py")


class AgentConfig:
    """Configuration for the research agent"""
    
    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        max_iterations: int = 30,
        research_mode: bool = False,
        debug: bool = False,
        width: int = 80,
        is_sub_agent: bool = False,
        depth: int = 0,
        parent_id: Optional[str] = None,
        max_depth: int = 2,
        enable_sub_agents: bool = False,  # Disabled by default
        session_id: Optional[str] = None
    ):
        self.provider = provider
        self.model = model
        self.max_iterations = max_iterations
        self.research_mode = research_mode
        self.debug = debug
        self.width = width
        self.is_sub_agent = is_sub_agent
        self.depth = depth
        self.parent_id = parent_id
        self.max_depth = max_depth
        self.enable_sub_agents = enable_sub_agents
        self.session_id = session_id or get_session_id()
        
    @classmethod
    def from_args(cls, args):
        """Create config from command line arguments"""
        return cls(
            provider=getattr(args, 'provider', None),
            model=getattr(args, 'model', None),
            max_iterations=getattr(args, 'max_iterations', 30),
            research_mode=getattr(args, 'research', False),
            debug=getattr(args, 'debug', False),
            width=getattr(args, 'width', 80),
            is_sub_agent=getattr(args, 'sub_agent', False),
            depth=getattr(args, 'depth', 0),
            parent_id=getattr(args, 'parent', None),
            max_depth=getattr(args, 'max_depth', 2),
            enable_sub_agents=getattr(args, 'enable_sub_agents', False),
            session_id=getattr(args, 'session_id', None)
        )