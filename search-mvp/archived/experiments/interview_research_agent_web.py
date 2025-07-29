"""
Web-optimized Interview Research Agent with structured output and streaming support
"""

import json
import time
import os
from typing import Dict, Any, List, Optional, AsyncGenerator, Callable
from datetime import datetime
import asyncio
from dataclasses import dataclass, asdict
from enum import Enum

from openai import AsyncOpenAI
from interview_research_tools import INTERVIEW_RESEARCH_TOOLS
from config.providers import get_provider_config
import subprocess
import shlex


class EventType(Enum):
    """Types of events emitted by the agent"""
    ITERATION_START = "iteration_start"
    THINKING = "thinking"
    REFLECTION = "reflection"
    PLANNING = "planning"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    ANALYSIS = "analysis"
    PROGRESS = "progress"
    RESPONSE_START = "response_start"
    RESPONSE_CHUNK = "response_chunk"
    RESPONSE_END = "response_end"
    ERROR = "error"
    STATS = "stats"


@dataclass
class AgentEvent:
    """Structured event emitted by the agent"""
    type: EventType
    data: Dict[str, Any]
    iteration: Optional[int] = None
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self):
        return {
            "type": self.type.value,
            "data": self.data,
            "iteration": self.iteration,
            "timestamp": self.timestamp
        }


class InterviewResearchAgentWeb:
    """Web-optimized research agent with structured events and streaming"""
    
    def __init__(self, provider="moonshot", verbose=False, event_callback: Optional[Callable] = None):
        # Get provider configuration
        self.provider_config = get_provider_config(provider)
        
        # Set up async API client
        api_key = os.getenv(self.provider_config.api_key_env)
        if not api_key:
            raise ValueError(f"{self.provider_config.api_key_env} not found")
        
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=self.provider_config.base_url
        )
        
        self.model = self.provider_config.model_name
        self.tools = INTERVIEW_RESEARCH_TOOLS
        self.verbose = verbose
        self.event_callback = event_callback
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Statistics tracking
        self.stats = {
            'start_time': datetime.now(),
            'iterations': 0,
            'tool_calls': 0,
            'llm_calls': 0,
            'input_tokens': 0,
            'output_tokens': 0,
            'total_cost': 0.0,
            'thinking_steps': 0,
            'reflections': 0
        }
        
        # Add thinking prompts
        self.thinking_prompts = {
            'initial': "Before I begin, let me think about the best approach to answer this question...",
            'iteration': "Let me reflect on what I've learned so far and plan my next steps...",
            'tool_selection': "Considering what information I need next...",
            'analysis': "Let me analyze what I've discovered...",
            'synthesis': "Now I'll synthesize all the findings into a comprehensive response..."
        }
    
    async def emit_event(self, event: AgentEvent):
        """Emit an event to the callback if provided"""
        if self.event_callback:
            await self.event_callback(event.to_dict())
        
        if self.verbose:
            print(f"[{event.type.value}] {json.dumps(event.data, indent=2)}")
    
    async def think_before_action(self, context: str, iteration: int) -> str:
        """Generate thinking/reflection before taking action"""
        thinking_prompt = f"""
You are analyzing Uruguay citizen interviews about healthcare, education, and social priorities.

Current context: {context}

Based on the URUGUAY INTERVIEW DATA, reflect on:
1. What have I learned so far about citizen concerns?
2. What interview data am I still missing?
3. What should be my next action to explore the interviews?

Focus ONLY on the Uruguay interview research. Provide a brief thought process (2-3 sentences).
"""
        
        # Emit thinking start
        await self.emit_event(AgentEvent(
            type=EventType.THINKING,
            data={"status": "starting", "context": context[:100] + "..."},
            iteration=iteration
        ))
        
        # Simple thinking without tools
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are analyzing citizen consultation interviews from Uruguay about healthcare, education, and social priorities. Be concise and focused on the interview research."},
                {"role": "user", "content": thinking_prompt}
            ],
            max_tokens=150,
            temperature=0.3
        )
        
        thinking = response.choices[0].message.content
        self.stats['thinking_steps'] += 1
        
        # Update token stats
        if response.usage:
            self.stats['input_tokens'] += response.usage.prompt_tokens
            self.stats['output_tokens'] += response.usage.completion_tokens
            self.stats['llm_calls'] += 1
        
        # Emit thinking result
        await self.emit_event(AgentEvent(
            type=EventType.THINKING,
            data={"content": thinking},
            iteration=iteration
        ))
        
        return thinking
    
    async def execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        """Execute a tool by running its command"""
        tool_config = self.tools.get(tool_name)
        if not tool_config or 'command' not in tool_config:
            raise ValueError(f"Tool {tool_name} not found or has no command")
        
        # Format command with arguments
        command = tool_config['command']
        for key, value in tool_args.items():
            # Escape special characters for shell
            escaped_value = shlex.quote(str(value))
            command = command.replace(f"{{{key}}}", escaped_value)
        
        # Add session ID for scratchpad tools
        if 'session_id' in command:
            command = command.replace('{session_id}', self.session_id)
        
        try:
            # Run command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return f"Error: {result.stderr}"
            
            return result.stdout
        except subprocess.TimeoutExpired:
            return "Error: Tool execution timed out"
        except Exception as e:
            return f"Error executing tool: {str(e)}"
    
    async def autonomous_research(self, research_question: str, max_iterations: int = 8) -> Dict[str, Any]:
        """Main research method with structured events and streaming"""
        
        # Emit start event
        await self.emit_event(AgentEvent(
            type=EventType.PROGRESS,
            data={
                "message": "Starting research",
                "question": research_question,
                "max_iterations": max_iterations
            }
        ))
        
        # Initialize conversation
        messages = [
            {
                "role": "system",
                "content": """You are an expert qualitative researcher analyzing citizen consultation interviews from Uruguay.

Your task is to explore the interview corpus to answer research questions comprehensively.

IMPORTANT: Think step-by-step before each action. Always explain your reasoning.

Available tools:
- get_corpus_stats: Get overview statistics
- list_interview_themes: Browse all themes in the corpus
- search_themes: Find interviews by theme keywords
- search_interviews: Full-text search with semantic capabilities
- get_interview_summary: Get AI-generated summary of specific interview
- get_interview_turns: Read actual interview transcript

Be thorough and systematic in your exploration."""
            },
            {
                "role": "user",
                "content": research_question
            }
        ]
        
        tool_call_log = []
        final_response = None
        iteration = 0
        
        # Initial thinking
        await self.think_before_action(f"Research question: {research_question}", 0)
        
        while iteration < max_iterations:
            try:
                iteration += 1
                self.stats['iterations'] = iteration
                
                # Emit iteration start
                await self.emit_event(AgentEvent(
                    type=EventType.ITERATION_START,
                    data={
                        "current": iteration,
                        "max": max_iterations
                    },
                    iteration=iteration
                ))
                
                # Make API call with tools
                # Extract tool functions from the INTERVIEW_RESEARCH_TOOLS format
                tool_functions = []
                for tool_name, tool_config in self.tools.items():
                    if 'schema' in tool_config and 'function' in tool_config['schema']:
                        tool_functions.append(tool_config['schema'])
                
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=tool_functions,
                    tool_choice="auto",
                    temperature=0.1
                )
                
                self.stats['llm_calls'] += 1
                
                # Update token usage
                if response.usage:
                    self.stats['input_tokens'] += response.usage.prompt_tokens
                    self.stats['output_tokens'] += response.usage.completion_tokens
                    
                    # Calculate cost based on provider
                    if self.provider_config.cost_per_1k_input and self.provider_config.cost_per_1k_output:
                        iteration_cost = (
                            (response.usage.prompt_tokens / 1000) * self.provider_config.cost_per_1k_input +
                            (response.usage.completion_tokens / 1000) * self.provider_config.cost_per_1k_output
                        )
                        self.stats['total_cost'] += iteration_cost
                
                message = response.choices[0].message
                
                # Check if agent wants to use tools
                if message.tool_calls:
                    # Add assistant's message to conversation
                    messages.append(message.model_dump())
                    
                    for tool_call in message.tool_calls:
                        tool_name = tool_call.function.name
                        
                        try:
                            tool_args = json.loads(tool_call.function.arguments)
                        except:
                            tool_args = {}
                        
                        # Think before using the tool
                        if iteration > 1:  # Skip for first iteration as we already thought
                            tool_thinking = await self.think_before_action(
                                f"About to use tool: {tool_name}",
                                iteration
                            )
                        
                        # Emit tool call event
                        await self.emit_event(AgentEvent(
                            type=EventType.TOOL_CALL,
                            data={
                                "tool": tool_name,
                                "args": tool_args,
                                "id": tool_call.id
                            },
                            iteration=iteration
                        ))
                        
                        # Execute tool
                        result = await self.execute_tool(tool_name, tool_args)
                        self.stats['tool_calls'] += 1
                        
                        # Create preview of result
                        result_str = json.dumps(result) if isinstance(result, (dict, list)) else str(result)
                        preview = result_str[:200] + "..." if len(result_str) > 200 else result_str
                        
                        # Extract useful metadata
                        metadata = {
                            "size": len(result_str),
                            "preview": preview
                        }
                        
                        # Add specific metadata based on tool
                        if tool_name == "search_interviews" and isinstance(result, list):
                            interviews_found = list(set([m.get('interview_id', '') for m in result if isinstance(m, dict)]))
                            metadata["interviews_found"] = interviews_found
                            metadata["matches_count"] = len(result)
                        elif tool_name == "get_interview_summary" and isinstance(result, dict):
                            metadata["interview_id"] = tool_args.get('interview_id', '')
                            metadata["themes"] = result.get('annotation', {}).get('summary', {}).get('key_themes', [])
                        
                        # Emit tool result event
                        await self.emit_event(AgentEvent(
                            type=EventType.TOOL_RESULT,
                            data={
                                "tool": tool_name,
                                "metadata": metadata
                            },
                            iteration=iteration
                        ))
                        
                        # Log tool call
                        tool_call_log.append({
                            'iteration': iteration,
                            'tool': tool_name,
                            'args': tool_args,
                            'result_preview': preview,
                            'metadata': metadata
                        })
                        
                        # Add tool result to conversation
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result_str
                        })
                    
                else:
                    # No tools used - agent is providing final response
                    final_response = message.content
                    break
                    
            except Exception as e:
                await self.emit_event(AgentEvent(
                    type=EventType.ERROR,
                    data={"error": str(e)},
                    iteration=iteration
                ))
                break
        
        # Generate final response if we hit max iterations
        if not final_response:
            await self.emit_event(AgentEvent(
                type=EventType.ANALYSIS,
                data={"message": "Generating comprehensive summary from research..."}
            ))
            
            final_response = await self._generate_final_response(
                research_question, 
                tool_call_log, 
                messages
            )
        
        # Stream the final response
        await self._stream_response(final_response)
        
        # Calculate final statistics
        duration = (datetime.now() - self.stats['start_time']).total_seconds()
        self.stats['duration'] = duration
        
        # Emit stats event
        await self.emit_event(AgentEvent(
            type=EventType.STATS,
            data=self.stats
        ))
        
        # Return structured result
        return {
            'final_response': final_response,
            'tool_calls': tool_call_log,
            'stats': self.stats,
            'session_id': self.session_id
        }
    
    async def _generate_final_response(self, question: str, tool_calls: List[Dict], messages: List[Dict]) -> str:
        """Generate final response with streaming support"""
        
        summary_prompt = f"""
Based on your research exploration, provide a comprehensive answer to: {question}

Your research involved {len(tool_calls)} tool calls across multiple interviews.

Structure your response with:
1. Executive Summary (2-3 sentences)
2. Key Findings (bullet points with specific interview references)
3. Supporting Evidence (quotes and examples)
4. Patterns and Themes
5. Conclusions

Be specific and cite interview IDs (e.g., "Interview 023") when referencing findings.
"""
        
        messages.append({"role": "user", "content": summary_prompt})
        
        # Generate with streaming
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
            stream=True
        )
        
        full_response = ""
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                full_response += chunk.choices[0].delta.content
        
        return full_response
    
    async def _stream_response(self, response: str):
        """Stream the response in chunks"""
        await self.emit_event(AgentEvent(
            type=EventType.RESPONSE_START,
            data={"total_length": len(response)}
        ))
        
        # Stream in reasonable chunks (simulate typing)
        chunk_size = 20  # characters per chunk
        for i in range(0, len(response), chunk_size):
            chunk = response[i:i + chunk_size]
            await self.emit_event(AgentEvent(
                type=EventType.RESPONSE_CHUNK,
                data={"text": chunk}
            ))
            await asyncio.sleep(0.02)  # Small delay for smooth streaming
        
        # Extract sources from response
        import re
        interview_matches = re.findall(r'Interview (\d{3})', response)
        sources = list(set([f"Interview {id}" for id in interview_matches]))[:10]
        
        await self.emit_event(AgentEvent(
            type=EventType.RESPONSE_END,
            data={
                "sources": sources,
                "word_count": len(response.split())
            }
        ))


# Example usage
async def example_callback(event: Dict):
    """Example callback that prints events"""
    print(f"[{event['type']}] {event['data']}")


async def main():
    """Example usage"""
    agent = InterviewResearchAgentWeb(
        provider="moonshot",
        verbose=True,
        event_callback=example_callback
    )
    
    result = await agent.autonomous_research(
        "What are the main healthcare concerns mentioned by citizens?",
        max_iterations=3
    )
    
    print("\n=== Final Result ===")
    print(f"Response length: {len(result['final_response'])} chars")
    print(f"Tool calls: {result['stats']['tool_calls']}")
    print(f"Total cost: ${result['stats']['total_cost']:.4f}")


if __name__ == "__main__":
    asyncio.run(main())