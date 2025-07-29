"""
Backend logger that sends logs to unified logging server
"""

import requests
import json
from datetime import datetime
from typing import Any, Dict

class UnifiedBackendLogger:
    def __init__(self, source: str = "backend"):
        self.source = source
        self.logger_url = "http://localhost:8001/log"
        self.enabled = True
        
    def _send_log(self, level: str, message: str, data: Dict[str, Any] = None):
        """Send log to unified logger"""
        if not self.enabled:
            return
            
        try:
            payload = {
                "source": self.source,
                "level": level,
                "message": message,
                "data": data or {}
            }
            requests.post(self.logger_url, json=payload, timeout=0.5)
        except:
            # Silently fail if logger is not available
            pass
    
    def info(self, message: str, **kwargs):
        self._send_log("info", message, kwargs)
        
    def error(self, message: str, **kwargs):
        self._send_log("error", message, kwargs)
        
    def debug(self, message: str, **kwargs):
        self._send_log("debug", message, kwargs)
        
    def success(self, message: str, **kwargs):
        self._send_log("success", message, kwargs)
        
    def event(self, event_type: str, event_data: Dict[str, Any]):
        """Log WebSocket events"""
        self._send_log("info", f"WebSocket Event: {event_type}", {
            "event_type": event_type,
            "event_data": event_data
        })

# Global logger instance
unified_logger = UnifiedBackendLogger()