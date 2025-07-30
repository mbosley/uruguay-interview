"""
In-memory event store for decoupling event production from WebSocket delivery
"""
import asyncio
from typing import Dict, List, Callable, Any
from collections import defaultdict
from datetime import datetime
import json
from dataclasses import dataclass, asdict
from queue import Queue
import threading


@dataclass
class Event:
    """Event data structure"""
    type: str
    data: Dict[str, Any]
    timestamp: str
    iteration: int = None
    
    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}


class EventStore:
    """Thread-safe in-memory event store"""
    
    def __init__(self):
        self._events: Dict[str, List[Event]] = defaultdict(list)
        self._subscribers: Dict[str, List[asyncio.Queue]] = defaultdict(list)
        self._lock = threading.Lock()
        
    def publish(self, channel: str, event: Dict[str, Any]):
        """Publish an event to a channel (thread-safe)"""
        # Create Event object
        if isinstance(event, dict):
            event_obj = Event(
                type=event.get('type', 'unknown'),
                data=event.get('data', {}),
                timestamp=event.get('timestamp', datetime.now().isoformat()),
                iteration=event.get('iteration')
            )
        else:
            event_obj = event
            
        with self._lock:
            # Store event
            self._events[channel].append(event_obj)
            queue_count = len(self._subscribers[channel])
            if queue_count > 0:
                print(f"[{datetime.now()}] 📮 Event '{event_obj.type}' queued for {queue_count} subscriber(s) on {channel}")
            
            # Notify all subscribers
            dead_queues = []
            for queue in self._subscribers[channel]:
                try:
                    # Put event in queue without blocking
                    queue.put_nowait(event_obj.to_dict())
                except asyncio.QueueFull:
                    # Queue is full, skip this event
                    print(f"Warning: Queue full for channel {channel}")
                except RuntimeError:
                    # Queue's event loop is closed
                    dead_queues.append(queue)
                    
            # Clean up dead queues
            for queue in dead_queues:
                self._subscribers[channel].remove(queue)
    
    async def subscribe(self, channel: str, queue: asyncio.Queue = None):
        """Subscribe to a channel and get an async queue of events"""
        if queue is None:
            queue = asyncio.Queue(maxsize=100)
            
        with self._lock:
            # Send all historical events first
            for event in self._events[channel]:
                await queue.put(event.to_dict())
                
            # Register for future events
            self._subscribers[channel].append(queue)
            
        return queue
    
    def unsubscribe(self, channel: str, queue: asyncio.Queue):
        """Unsubscribe a queue from a channel"""
        with self._lock:
            if queue in self._subscribers[channel]:
                self._subscribers[channel].remove(queue)
    
    def get_events(self, channel: str, start_index: int = 0) -> List[Dict]:
        """Get all events for a channel starting from index"""
        with self._lock:
            events = self._events[channel][start_index:]
            return [e.to_dict() for e in events]
    
    def clear_channel(self, channel: str):
        """Clear all events for a channel"""
        with self._lock:
            self._events[channel].clear()
            # Note: subscribers remain active
    
    def get_channel_info(self) -> Dict[str, Dict]:
        """Get information about all channels"""
        with self._lock:
            return {
                channel: {
                    'event_count': len(events),
                    'subscriber_count': len(self._subscribers[channel]),
                    'last_event': events[-1].to_dict() if events else None
                }
                for channel, events in self._events.items()
            }


# Global event store instance
event_store = EventStore()