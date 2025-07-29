"""
Streaming client wrapper for Kimi/Moonshot with dynamic thinking box support
"""

import os
import sys
import json
import time
import asyncio
from typing import AsyncIterator, Iterator, Dict, Any, Tuple, Optional
from openai import OpenAI
from dataclasses import dataclass

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
web_demo_dir = os.path.dirname(current_dir)
parent_dir = os.path.dirname(web_demo_dir)
sys.path.insert(0, parent_dir)

from config.providers import get_provider_config

@dataclass
class StreamEvent:
    """Represents a streaming event from the LLM"""
    type: str  # 'reasoning', 'content', 'tool_call', 'status'
    content: Any
    metadata: Optional[Dict] = None

class KimiStreamingClient:
    """Streaming client for Kimi with thinking/reasoning support"""
    
    def __init__(self, provider_name: str = "moonshot"):
        self.config = get_provider_config(provider_name)
        self.client = OpenAI(
            base_url=self.config.base_url,
            api_key=os.getenv(self.config.api_key_env)
        )
        
    def stream_chat(
        self,
        messages: list,
        tools: list = None,
        temperature: float = 0.7,
        with_thinking: bool = True,
        system_prompt: str = None
    ) -> Iterator[StreamEvent]:
        """
        Stream chat completions with support for reasoning/thinking
        
        Yields StreamEvent objects with types:
        - 'reasoning': Intermediate reasoning/thinking
        - 'content': Main response content
        - 'tool_call': Tool invocation
        - 'status': Status updates
        """
        
        # Prepare messages
        full_messages = []
        
        # Add system prompt if provided
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        
        # If we want thinking, prepend instruction to show reasoning
        if with_thinking:
            thinking_prompt = """When answering questions, show your reasoning process by:
1. First, prefix your internal analysis with "THINKING:" 
2. Then provide your final answer after "ANSWER:"

This helps users understand your research process."""
            
            if full_messages and full_messages[0]["role"] == "system":
                full_messages[0]["content"] += "\n\n" + thinking_prompt
            else:
                full_messages.insert(0, {"role": "system", "content": thinking_prompt})
        
        # Add user messages
        full_messages.extend(messages)
        
        # Create streaming request
        try:
            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=full_messages,
                tools=tools,
                temperature=temperature,
                stream=True
            )
            
            # Parse the stream
            buffer = ""
            in_thinking = False
            
            for chunk in response:
                if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    buffer += content
                    
                    # Check for mode transitions
                    if "THINKING:" in buffer and not in_thinking:
                        # Extract thinking content
                        parts = buffer.split("THINKING:", 1)
                        if parts[0].strip():
                            # Yield any content before thinking
                            yield StreamEvent('content', parts[0].strip())
                        buffer = parts[1]
                        in_thinking = True
                        
                    elif "ANSWER:" in buffer and in_thinking:
                        # Transition from thinking to answer
                        parts = buffer.split("ANSWER:", 1)
                        # Yield the thinking content
                        yield StreamEvent('reasoning', parts[0].strip())
                        buffer = parts[1]
                        in_thinking = False
                    
                    # Stream current content
                    if in_thinking:
                        yield StreamEvent('reasoning', content)
                    else:
                        yield StreamEvent('content', content)
                
                # Handle tool calls
                elif hasattr(chunk.choices[0].delta, 'tool_calls') and chunk.choices[0].delta.tool_calls:
                    for tool_call in chunk.choices[0].delta.tool_calls:
                        yield StreamEvent('tool_call', tool_call)
                        
        except Exception as e:
            yield StreamEvent('status', f"Error: {str(e)}", {'error': True})
    
    async def stream_research_agent(
        self,
        agent,
        question: str,
        max_iterations: int = 8
    ) -> AsyncIterator[StreamEvent]:
        """
        Stream events from the research agent with real-time updates
        
        This wraps the InterviewResearchAgent to provide streaming updates
        """
        
        # Track research progress
        current_step = 0
        total_steps = max_iterations * 2  # Estimate: 2 phases per iteration
        
        yield StreamEvent('status', 'Initializing research...', {
            'progress': 0,
            'step': 'init'
        })
        
        # Custom callback to capture agent events
        def progress_callback(event_type: str, data: Any):
            nonlocal current_step
            current_step += 1
            
            if event_type == 'thinking':
                return StreamEvent('reasoning', data)
            elif event_type == 'tool_call':
                return StreamEvent('status', f"🔧 {data['tool']}: {data['args']}", {
                    'progress': current_step / total_steps,
                    'step': 'tool_call'
                })
            elif event_type == 'tool_result':
                return StreamEvent('reasoning', f"Tool result: {data[:200]}...")
            elif event_type == 'iteration':
                return StreamEvent('status', f"Step {data['current']}/{data['total']}: {data['phase']}", {
                    'progress': data['current'] / data['total'],
                    'step': 'iteration'
                })
            
        # Monkey-patch the agent to emit events
        original_log = agent.logger.thinking
        events_queue = asyncio.Queue()
        
        def patched_thinking(message):
            # Call original
            original_log(message)
            # Emit event
            asyncio.create_task(events_queue.put(
                StreamEvent('reasoning', message)
            ))
        
        agent.logger.thinking = patched_thinking
        
        try:
            # Start research in background
            research_task = asyncio.create_task(
                agent.autonomous_research(question, max_iterations=max_iterations)
            )
            
            # Stream events as they come
            while not research_task.done():
                try:
                    # Wait for events with timeout
                    event = await asyncio.wait_for(events_queue.get(), timeout=0.1)
                    yield event
                except asyncio.TimeoutError:
                    # No event, check if task is done
                    continue
            
            # Get final result
            result = await research_task
            
            # Stream the final response with thinking
            final_response = result.get('final_response', '')
            if final_response:
                # Stream it token by token
                for i in range(0, len(final_response), 5):  # Chunk by 5 chars
                    chunk = final_response[i:i+5]
                    yield StreamEvent('content', chunk)
                    await asyncio.sleep(0.01)  # Small delay for effect
            
            # Yield completion event
            yield StreamEvent('status', 'Research complete', {
                'progress': 1.0,
                'step': 'complete',
                'stats': result.get('stats', {})
            })
            
        finally:
            # Restore original logger
            agent.logger.thinking = original_log

class MockKimiClient:
    """Mock client for testing the UI without API calls"""
    
    def stream_chat(self, messages, **kwargs):
        """Mock streaming responses"""
        thinking = "Let me analyze the citizen interviews to understand healthcare concerns..."
        answer = "Based on my analysis of the Uruguay citizen interviews, the main healthcare concerns include:\n\n1. **Long wait times** - Citizens frequently mention waiting months for specialist appointments\n2. **Medicine availability** - Several interviewees reported difficulties obtaining prescribed medications\n3. **Rural access** - Limited healthcare facilities in rural areas force long travels"
        
        # Stream thinking
        for char in thinking:
            yield StreamEvent('reasoning', char)
            time.sleep(0.02)
        
        # Stream answer
        for word in answer.split():
            yield StreamEvent('content', word + ' ')
            time.sleep(0.03)