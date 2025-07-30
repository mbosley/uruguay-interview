"""Core research agent implementation"""

import json
import time
import asyncio
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from openai import AsyncOpenAI

# Import from parent directory
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from interview_research_tools import INTERVIEW_RESEARCH_TOOLS
from config.providers import get_provider_config
from .logger import AgentLogger
from .events import EventHandler
from .tools import ToolExecutor
from .report_generator import ReportGenerator
from .prompts import SYSTEM_PROMPT
from .config import AgentConfig


class InterviewResearchAgent:
    """Agent for conducting research on interview data"""
    
    def __init__(self, config: AgentConfig):
        """Initialize the agent with configuration"""
        self.config = config
        self.session_id = config.session_id
        self.is_sub_agent = config.is_sub_agent
        self.depth = config.depth
        self.parent_id = config.parent_id
        self.max_depth = config.max_depth
        self.research_mode = config.research_mode
        self.debug = config.debug
        
        # Set up provider
        self.provider_config = get_provider_config(config.provider)
        self.model = config.model or self.provider_config.model_name
        
        # Initialize components
        self.logger = AgentLogger(research_mode=self.research_mode, debug=self.debug, max_width=config.width)
        self.event_handler = EventHandler()
        self.event_handler.set_session_id(self.session_id)
        self.tool_executor = ToolExecutor(self.session_id, self.logger)
        self.report_generator = ReportGenerator(self.logger, max_width=config.width)
        
        # Set up OpenAI client
        api_key = os.getenv(self.provider_config.api_key_env)
        if not api_key:
            raise ValueError(f"{self.provider_config.api_key_env} not found in environment")
        
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=self.provider_config.base_url
        )
        
        # Initialize tools
        self.tools = INTERVIEW_RESEARCH_TOOLS.copy()
        
        # Remove spawn_sub_agent if sub-agents are disabled
        if not config.enable_sub_agents and "spawn_sub_agent" in self.tools:
            del self.tools["spawn_sub_agent"]
        
        # Statistics tracking
        self.stats = {
            'start_time': datetime.now(),
            'iterations': 0,
            'tool_calls': 0,
            'input_tokens': 0,
            'output_tokens': 0,
            'total_cost': 0.0,
            'sub_agents_spawned': 0
        }
    
    async def emit_event(self, event_type: str, data: Dict[str, Any], iteration: Optional[int] = None):
        """Emit an event"""
        await self.event_handler.emit_event(event_type, data, iteration)
    
    def _generate_preview(self, tool_name: str, result: str) -> str:
        """Generate preview for tool result"""
        return self.tool_executor.generate_preview(tool_name, result)
    
    async def research(self, research_question: str, max_iterations: int = 30) -> Dict[str, Any]:
        """Main research loop"""
        # Log startup
        if not self.is_sub_agent:
            self.logger.info("\n" + "═"*self.logger.max_width)
            self.logger.info(f"🚀 RESEARCH AGENT INITIALIZED")
            self.logger.info(f"📍 Provider: {self.provider_config.name} - {self.provider_config.description}")
            self.logger.info(f"⚡ Speed: {self.provider_config.tokens_per_second} tokens/second")
            # Wrap long questions
            question_wrapped = self.logger._wrap_text(f"🎯 Question: {research_question}")
            self.logger.info(question_wrapped)
            self.logger.info(f"🔄 Max iterations: {max_iterations}")
            self.logger.info("═"*self.logger.max_width)
        
        # Emit session start event
        await self.emit_event("session_start", {
            "research_question": research_question,
            "max_iterations": max_iterations,
            "provider": self.provider_config.name,
            "model": self.model,
            "session_id": self.session_id
        })
        
        # Initialize conversation with system prompt
        system_message = {
            "role": "system", 
            "content": SYSTEM_PROMPT.replace(
                "'QUICK: 1-2 searches, 2-3 key interview excerpts maximum' if max_iterations <= 5",
                "'QUICK: 1-2 searches, 2-3 key interview excerpts maximum'" if max_iterations <= 5 else "'THOROUGH: Multiple searches, 4-6 interviews, key quotes'"
            ).replace(
                "'QUICK: Skip iteration - go straight to synthesis' if max_iterations <= 5",
                "'QUICK: Skip iteration - go straight to synthesis'" if max_iterations <= 5 else "'Review your scratchpad with `scratchpad_read()`'"
            ).replace(
                "'Monitor your remaining iterations carefully' if max_iterations <= 10",
                "'Monitor your remaining iterations carefully'" if max_iterations <= 10 else "'Identify gaps or new directions'"
            )
        }
        
        user_message = {
            "role": "user",
            "content": f"Research question: {research_question}\n\nPlease explore this systematically using the methodology provided. You have {max_iterations} iterations available."
        }
        
        messages = [system_message, user_message]
        
        # Emit research start event
        await self.emit_event("research_start", {
            "question": research_question,
            "max_iterations": max_iterations
        })
        
        iteration = 0
        tool_call_log = []
        final_response = "Research incomplete - reached maximum iterations or encountered error"
        
        while iteration < max_iterations:
            try:
                # Show iteration header
                self.logger.iteration_header(iteration + 1, max_iterations)
                
                # Prepare API call - always allow tools during research phase
                api_params = {
                    "model": self.model,
                    "messages": messages,
                    "tools": [schema["schema"] for schema in self.tools.values()],
                    "tool_choice": "auto"  # Always allow tools during research
                }
                
                # Handle different parameters for different models
                if self.model.startswith("o3") or self.model.startswith("o4"):
                    api_params["max_completion_tokens"] = 4096
                    # o-series models only support default temperature
                else:
                    api_params["max_tokens"] = 4096
                    api_params["temperature"] = 0.7
                
                # Debug: Log API call details
                if self.debug:
                    self.logger.debug(f"API Call: iteration={iteration}, model={self.model}, provider={self.provider_config.name}")
                    self.logger.debug(f"API Key: {self.client.api_key[:10]}...{self.client.api_key[-4:]}")
                    self.logger.debug(f"Messages: {len(messages)} messages, last role: {messages[-1]['role'] if messages else 'none'}")
                
                response = await self.client.chat.completions.create(**api_params)
                message = response.choices[0].message
                
                # Track token usage
                if hasattr(response, 'usage') and response.usage:
                    self.stats['input_tokens'] += response.usage.prompt_tokens
                    self.stats['output_tokens'] += response.usage.completion_tokens
                    
                    # Calculate cost
                    input_cost = (response.usage.prompt_tokens / 1000) * self.provider_config.cost_per_1k_input
                    output_cost = (response.usage.completion_tokens / 1000) * self.provider_config.cost_per_1k_output
                    iteration_cost = input_cost + output_cost
                    self.stats['total_cost'] += iteration_cost
                    
                    # Log cost in research mode
                    if self.research_mode and not self.is_sub_agent:
                        self.logger.info(f"💰 Iteration cost: ${iteration_cost:.6f} ({response.usage.total_tokens} tokens)")
                
                # Check if agent wants to use tools
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    # Show agent's thinking if provided
                    if message.content:
                        self.logger.thinking(message.content)
                    
                    # Add assistant message to conversation
                    messages.append({
                        "role": "assistant",
                        "content": message.content or "",  # Ensure content is never None
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            }
                            for tc in message.tool_calls
                        ]
                    })
                    
                    # Execute tools
                    await self._execute_tool_calls(
                        message.tool_calls,
                        messages,
                        tool_call_log,
                        iteration + 1
                    )
                    
                    iteration += 1
                    self.stats['iterations'] = iteration
                    
                    # Add context about remaining iterations
                    remaining_iterations = max_iterations - iteration
                    if remaining_iterations > 0:
                        messages.append({
                            "role": "system",
                            "content": f"You are now in iteration {iteration + 1} of {max_iterations}. You have {remaining_iterations} more iteration(s) available for research."
                        })
                    
                    # Add small delay for Groq to avoid rate limiting
                    if self.provider_config.name == "groq" and not self.is_sub_agent:
                        await asyncio.sleep(0.5)
                    
                else:
                    # No tools used in this iteration
                    if message.content:
                        self.logger.thinking(message.content)
                    
                    # Add assistant message to conversation
                    messages.append({
                        "role": "assistant",
                        "content": message.content or ""
                    })
                    
                    # Increment iteration counter even if no tools were used
                    iteration += 1
                    self.stats['iterations'] = iteration
                    
                    # Continue to next iteration unless we've reached the limit
                    if iteration < max_iterations:
                        messages.append({
                            "role": "system",
                            "content": f"You chose not to use tools in iteration {iteration}. You are now in iteration {iteration + 1} of {max_iterations}. You have {max_iterations - iteration} more iteration(s) available for research. Please continue your research using the available tools."
                        })
                    else:
                        # Reached max iterations
                        break
                    
            except Exception as e:
                error_msg = str(e)
                self.logger.error(f"Error in iteration {iteration + 1}: {error_msg}")
                
                # Check if it's a retryable error (rate limiting, server overload)
                is_retryable = any(phrase in error_msg.lower() for phrase in [
                    "over capacity", "rate limit", "server error", "503", "502", "500"
                ])
                
                if is_retryable and iteration < max_iterations - 1:  # Leave room for at least one retry
                    import time
                    retry_delay = min(2 ** (iteration % 3), 30)  # Exponential backoff, max 30s
                    self.logger.info(f"⏳ Retryable error detected. Waiting {retry_delay}s before retry...")
                    time.sleep(retry_delay)
                    continue  # Retry this iteration
                else:
                    # Non-retryable error or too many iterations used - break
                    self.logger.error(f"❌ Stopping research due to: {error_msg}")
                    break
        
        # Yield to ensure last tool result is sent
        await asyncio.sleep(0)
        
        # Emit research phase complete event
        await self.emit_event("research_complete", {
            "iterations": iteration,
            "tool_calls": len(tool_call_log)
        })
        
        # Store final messages for summary
        final_messages = messages.copy()
        
        # Generate summary/report as a separate step after all research
        self.logger.info("\n" + "═"*self.logger.max_width)
        self.logger.info(f"✅ RESEARCH PHASE COMPLETE")
        self.logger.info(f"📊 {iteration} iterations, {len(tool_call_log)} tool calls")
        self.logger.info("═"*self.logger.max_width)
        self.logger.info("\n📝 REPORT GENERATION PHASE")
        self.logger.info("━"*self.logger.max_width)
        
        final_response = await self._generate_summary(
            research_question,
            tool_call_log,
            iteration,
            final_response,
            final_messages
        )
        
        # Log statistics
        if not self.is_sub_agent:
            self._log_statistics()
        
        # Return results
        return self._prepare_results(
            final_response,
            tool_call_log,
            iteration,
            final_messages
        )
    
    async def _execute_tool_calls(
        self,
        tool_calls,
        final_messages: List[Dict[str, Any]],
        tool_call_log: List[Dict[str, Any]],
        iteration: int
    ):
        """Execute tool calls and handle results"""
        # Separate spawn_sub_agent calls from other tools
        spawn_calls = []
        other_calls = []
        
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            if tool_name == "spawn_sub_agent":
                spawn_calls.append(tool_call)
            else:
                other_calls.append(tool_call)
        
        # Execute non-spawn tools sequentially first
        for tool_call in other_calls:
            # Ensure we always add a tool response, even on error
            result = None
            tool_name = None
            tool_args = {}
            
            try:
                tool_name = tool_call.function.name
                tool_args_str = tool_call.function.arguments
                
                # Parse arguments
                try:
                    tool_args = json.loads(tool_args_str) if tool_args_str else {}
                except json.JSONDecodeError:
                    tool_args = {}
                
                self.logger.tool_call(tool_name, tool_args)
                
                # Emit tool_call event
                await self.emit_event("tool_call", {
                    "tool": tool_name,
                    "args": tool_args,
                    "id": tool_call.id
                }, iteration)
                
                # Execute tool
                if tool_name in [schema["schema"]["function"]["name"] for schema in self.tools.values()]:
                    # Find the right tool
                    tool_config = None
                    for tool_key, tool_def in self.tools.items():
                        if tool_def["schema"]["function"]["name"] == tool_name:
                            tool_config = tool_def
                            break
                    
                    if tool_config:
                        # Check if this is a sub-agent spawn
                        if tool_name == "spawn_sub_agent":
                            raw_result, rendered_result = await self.tool_executor.execute_spawn_sub_agent(
                                tool_config["command"],
                                tool_args,
                                parent_depth=0,  # TODO: Get from config
                                max_depth=2
                            )
                        else:
                            raw_result, rendered_result = await self.tool_executor.execute_cli_tool(
                                tool_name,
                                tool_config["command"],
                                tool_args
                            )
                    else:
                        raw_result = rendered_result = f"Error: Tool configuration not found for '{tool_name}'"
                else:
                    raw_result = rendered_result = f"Error: Unknown tool '{tool_name}'"
                
                # Extract preview using raw result for JSON parsing
                try:
                    preview = self._extract_preview(tool_name, raw_result)
                except Exception as e:
                    self.logger.debug(f"Preview extraction failed: {e}")
                    preview = "Preview unavailable"
                
                # Log the rendered result
                self.logger.tool_result(len(rendered_result), preview, tool_name, rendered_result)
                
                # Generate preview for event metadata
                try:
                    event_preview = self._generate_preview(tool_name, raw_result)
                except Exception as e:
                    self.logger.debug(f"Event preview generation failed: {e}")
                    event_preview = preview  # Use the extract_preview result
                
                # Emit tool_result event with raw result
                await self.emit_event("tool_result", {
                    "tool": tool_name,
                    "result": raw_result,
                    "metadata": {
                        "size": len(raw_result),
                        "preview": event_preview
                    }
                }, iteration)
                
                # Add raw result to conversation for agent processing
                final_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": raw_result
                })
                
                # Log tool call
                tool_call_log.append({
                    "tool": tool_name,
                    "args": tool_args,
                    "result": raw_result,
                    "result_length": len(raw_result),
                    "timestamp": datetime.now().isoformat()
                })
                
                self.stats['tool_calls'] += 1
                
            except Exception as e:
                # If anything goes wrong, ensure we still add a tool response
                import traceback
                error_msg = f"Error executing tool {tool_name}: {str(e)}"
                self.logger.error(error_msg)
                if self.debug:
                    self.logger.debug(f"Full traceback: {traceback.format_exc()}")
                
                # Add error response to conversation
                final_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps({"error": error_msg})
                })
                
                # Log the failed tool call
                tool_call_log.append({
                    "tool": tool_name,
                    "args": tool_args if 'tool_args' in locals() else {},
                    "result": error_msg,
                    "result_length": len(error_msg),
                    "timestamp": datetime.now().isoformat()
                })
        
        # Execute spawn_sub_agent calls in parallel
        if spawn_calls:
            await self._execute_spawn_calls(
                spawn_calls,
                final_messages,
                tool_call_log,
                iteration
            )
    
    async def _execute_spawn_calls(
        self,
        spawn_calls,
        final_messages: List[Dict[str, Any]],
        tool_call_log: List[Dict[str, Any]],
        iteration: int
    ):
        """Execute spawn_sub_agent calls in parallel"""
        self.logger.info(f"🚀 Executing {len(spawn_calls)} sub-agents in parallel...")
        
        # Show what each sub-agent will research
        for i, tool_call in enumerate(spawn_calls, 1):
            try:
                args = json.loads(tool_call.function.arguments)
                question = args.get('question', 'Unknown')
                self.logger.info(f"{i}. {question[:100]}...")
            except:
                pass
        
        start_time = time.time()
        
        # Prepare tasks for parallel execution
        spawn_tasks = []
        task_metadata = []
        
        for tool_call in spawn_calls:
            try:
                tool_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
            except json.JSONDecodeError:
                tool_args = {}
            
            self.logger.tool_call("spawn_sub_agent", tool_args)
            
            # Emit tool_call event
            await self.emit_event("tool_call", {
                "tool": "spawn_sub_agent",
                "args": tool_args,
                "id": tool_call.id
            }, iteration)
            
            # Find tool config
            tool_config = None
            for tool_key, tool_def in self.tools.items():
                if tool_def["schema"]["function"]["name"] == "spawn_sub_agent":
                    tool_config = tool_def
                    break
            
            if tool_config:
                # Create async task
                task = self.tool_executor.execute_spawn_sub_agent(
                    tool_config["command"],
                    tool_args,
                    self.depth,
                    self.max_depth
                )
                spawn_tasks.append(task)
                task_metadata.append((tool_call, tool_args))
        
        # Execute all spawn tasks in parallel
        results = await asyncio.gather(*spawn_tasks, return_exceptions=True)
        
        # Process results
        for (tool_call, tool_args), result in zip(task_metadata, results):
            if isinstance(result, Exception):
                error_result = json.dumps({"error": str(result)})
                self.logger.error(f"Sub-agent failed: {str(result)}")
                
                final_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": error_result
                })
                
                tool_call_log.append({
                    "tool": "spawn_sub_agent",
                    "args": tool_args,
                    "result": error_result,
                    "result_length": len(error_result),
                    "timestamp": datetime.now().isoformat()
                })
            else:
                # Process successful result
                preview = self._process_sub_agent_result(result)
                
                self.logger.tool_result(len(result), preview, "spawn_sub_agent", result)
                
                # Emit tool_result event
                await self.emit_event("tool_result", {
                    "tool": "spawn_sub_agent",
                    "result": result,
                    "metadata": {
                        "size": len(result),
                        "preview": preview
                    }
                }, iteration)
                
                # Add tool result to conversation
                final_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
                
                # Log tool call
                tool_call_log.append({
                    "tool": "spawn_sub_agent",
                    "args": tool_args,
                    "result": result,
                    "result_length": len(result),
                    "timestamp": datetime.now().isoformat()
                })
                
                self.stats['sub_agents_spawned'] += 1
        
        elapsed = time.time() - start_time
        self.logger.info(f"✅ All sub-agents completed in {elapsed:.1f}s (parallel execution)")
    
    def _extract_preview(self, tool_name: str, result: str) -> Optional[str]:
        """Extract preview for certain tools"""
        preview = None
        
        # Check if the result is already rendered (contains formatting markers)
        if any(marker in str(result) for marker in ["═" * 20, "━" * 20, "─" * 20, "INTERVIEW THEMES", "CORPUS STATISTICS", "SEARCH RESULTS"]):
            # Already rendered - extract a simple preview
            lines = result.strip().split('\n')
            relevant_lines = []
            for line in lines:
                line = line.strip()
                if line and not any(char * 10 in line for char in "═━─"):  # Skip separator lines
                    if "Found" in line or "themes" in line.lower() or "Total" in line:
                        relevant_lines.append(line)
                        if len(relevant_lines) >= 2:
                            break
            preview = " | ".join(relevant_lines) if relevant_lines else None
            return preview
        
        if tool_name in ["search_interviews", "search_themes", "list_interview_themes", "get_interview_turn"]:
            # Try to extract meaningful content from JSON results
            try:
                parsed = json.loads(result)
                
                if tool_name == "search_interviews" and "results" in parsed:
                    preview = self._extract_search_preview(parsed["results"])
                
                elif tool_name == "list_interview_themes":
                    preview = self._extract_themes_preview(parsed)
                
                elif tool_name == "search_themes":
                    if "matching_themes" in parsed:
                        themes = list(parsed["matching_themes"].keys())[:3]
                        preview = f"Found themes: {', '.join(themes)}"
                
                elif tool_name == "get_interview_turn":
                    preview = self._extract_interview_preview(parsed)
                
            except (json.JSONDecodeError, KeyError) as e:
                # Fallback for non-JSON results
                if tool_name == "search_interviews":
                    preview = self._extract_search_preview_raw(result)
                else:
                    # Original fallback
                    lines = result.strip().split('\n')
                    for line in lines:
                        if line.strip():
                            preview = line.strip()
                            break
        
        return preview
    
    def _extract_search_preview(self, results: List[Dict[str, Any]]) -> str:
        """Extract preview from search results"""
        # Count different types of matches
        theme_matches = sum(1 for r in results if r.get("type") == "theme_match")
        tag_matches = sum(1 for r in results if r.get("type") == "tag_match")
        text_matches = sum(1 for r in results if r.get("type") == "turn_text_match")
        
        # Get unique interviews
        interviews = set()
        for r in results:
            if r.get("type") == "theme_match":
                interviews.update(r.get("interviews", []))
            elif r.get("interview_id"):
                interviews.add(r["interview_id"])
        
        # Build informative summary
        parts = []
        if theme_matches: 
            parts.append(f"{theme_matches} themes")
        if tag_matches: 
            parts.append(f"{tag_matches} tags")
        if text_matches: 
            parts.append(f"{text_matches} text matches")
        
        summary = f"Found: {', '.join(parts)}"
        if interviews:
            summary += f" across {len(interviews)} interviews"
        
        # Add sample themes if available
        theme_names = []
        for r in results[:3]:  # First 3 results
            if r.get("type") == "theme_match":
                theme_names.append(r.get("theme", ""))
        if theme_names:
            summary += f" | Themes: {', '.join(theme_names[:2])}"
        
        return summary
    
    def _extract_themes_preview(self, parsed: Dict[str, Any]) -> str:
        """Extract preview from themes listing"""
        if "meta_themes" in parsed:
            # Summary mode - extract themes from meta_themes hierarchy
            all_themes = []
            for meta_theme, meta_data in parsed["meta_themes"].items():
                if meta_theme != "uncategorized" and "themes" in meta_data:
                    all_themes.extend(list(meta_data["themes"].keys()))
            # Show top themes, excluding any from uncategorized
            preview = f"Top themes: {', '.join(all_themes[:5])}" if all_themes else "No themes found"
        elif "themes" in parsed:
            # Regular mode
            themes = list(parsed["themes"].keys())[:4]
            preview = f"Themes: {', '.join(themes)}"
        else:
            preview = "Theme data structure not recognized"
        
        return preview
    
    def _extract_interview_preview(self, parsed: Dict[str, Any]) -> str:
        """Extract preview from interview data"""
        if parsed.get("type") == "interview_summary":
            # Interview summary
            interview_id = parsed.get("interview_id", "")
            meta = parsed.get("metadata", {})
            themes = parsed.get("key_themes", [])[:3]
            
            parts = [f"Interview {interview_id} summary"]
            if meta.get("location"):
                parts.append(f"{meta['location']}")
            if themes:
                # Extract theme names from theme objects
                theme_names = [t.get("theme", "") if isinstance(t, dict) else str(t) for t in themes]
                parts.append(f"themes: {', '.join(theme_names)}")
            preview = " | ".join(parts)
        
        elif parsed.get("turns"):
            # Turn or turn range
            turns = parsed.get("turns", [])
            turn_count = len(turns)
            if turn_count == 1:
                # Single turn - show speaker and preview
                turn = turns[0]
                speaker = turn.get("speaker", "")
                text = turn.get("text", "")[:100] + "..."
                preview = f"{speaker}: {text}"
            else:
                # Multiple turns - show count and speakers
                speakers = list(set(t.get("speaker", "") for t in turns))
                preview = f"{turn_count} turns | Speakers: {', '.join(speakers[:3])}"
        else:
            preview = None
        
        return preview
    
    def _extract_search_preview_raw(self, result: str) -> str:
        """Extract preview from raw search results"""
        lines = result.strip().split('\n')
        text_matches = sum(1 for line in lines if line.startswith("MATCH:"))
        theme_matches = sum(1 for line in lines if line.startswith("THEME MATCH:"))
        tag_matches = sum(1 for line in lines if line.startswith("TAG MATCH:"))
        
        # Count unique interviews
        interviews = set()
        for line in lines:
            if "Interview " in line and ":" in line:
                # Extract interview ID from lines like "Interview 065:"
                parts = line.split("Interview ")
                if len(parts) > 1:
                    interview_id = parts[1].split(":")[0].strip()
                    if interview_id.isdigit():
                        interviews.add(interview_id)
        
        parts = []
        if theme_matches: parts.append(f"{theme_matches} themes")
        if tag_matches: parts.append(f"{tag_matches} tags")
        if text_matches: parts.append(f"{text_matches} text matches")
        
        if parts:
            preview = f"Found: {', '.join(parts)}"
            if interviews:
                preview += f" across {len(interviews)} interviews"
        else:
            # Try to find any result summary line
            for line in lines:
                if line.strip() and "Found" in line:
                    preview = line.strip()
                    break
            else:
                preview = None
        
        return preview
    
    def _process_sub_agent_result(self, result: str) -> str:
        """Process sub-agent result and generate preview"""
        try:
            parsed_result = json.loads(result)
            
            if 'final_response' in parsed_result:
                summary = parsed_result.get('final_response', '')[:200] + '...'
                tool_calls = parsed_result.get('tool_calls_count', 0)
                iterations = parsed_result.get('iterations', 0)
                action_summary = parsed_result.get('action_summary', 'conducted research')
                
                preview = f"✓ {iterations} iterations, {tool_calls} tool calls"
                self.logger.info(f"🔍 Sub-agent {action_summary}")
                self.logger.info(f"📊 Key finding: {summary[:150]}...")
                
                # Show tool usage breakdown if available
                if 'tool_summary' in parsed_result:
                    tools_used = ', '.join([f"{t}({c})" for t, c in parsed_result['tool_summary'].items()])
                    self.logger.info(f"🔧 Tools used: {tools_used}")
                
                # Aggregate sub-agent costs
                if 'stats' in parsed_result and 'total_cost' in parsed_result['stats']:
                    sub_cost = parsed_result['stats']['total_cost']
                    self.stats['total_cost'] += sub_cost
                    if sub_cost > 0:
                        self.logger.info(f"💰 Sub-agent cost: ${sub_cost:.6f}")
            else:
                preview = "Sub-agent completed"
        except json.JSONDecodeError:
            preview = "Sub-agent completed (non-JSON response)"
        
        return preview
    
    async def _generate_summary(
        self,
        research_question: str,
        tool_call_log: List[Dict[str, Any]],
        iteration: int,
        final_response: str,
        final_messages: List[Dict[str, Any]]
    ) -> str:
        """Generate research summary"""
        # Read scratchpad content
        try:
            from src.tools.scratchpad_tools import read_notes
            scratchpad_content = read_notes(self.session_id)
        except Exception as e:
            self.logger.error(f"Error reading scratchpad: {e}")
            scratchpad_content = ""
        
        # Generate summary only if we have meaningful research data
        min_tool_calls = 3  # Lowered threshold to ensure UN-style reports are generated
        has_sufficient_data = len(tool_call_log) >= min_tool_calls
        
        if tool_call_log and has_sufficient_data:
            self.logger.info(f"📊 Synthesizing findings from {len(tool_call_log)} research actions...")
            
            # Emit summary generation event
            await self.emit_event("summary_generation_start", {
                "tool_calls": len(tool_call_log),
                "iterations": iteration
            })
            await asyncio.sleep(0)
            
            # Retry logic for summary generation
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    summary_prompt = self.report_generator.build_summary_prompt(
                        research_question,
                        tool_call_log,
                        scratchpad_content,
                        iteration
                    )
                    
                    # Debug: Show full context being sent to summarizing agent
                    if self.debug:
                        self.logger.debug("\n" + "="*self.logger.max_width)
                        self.logger.debug("🔍 FULL CONTEXT FOR SUMMARIZING AGENT")
                        self.logger.debug("="*self.logger.max_width)
                        
                        # Show research journey details
                        self.logger.debug("\n📋 RESEARCH SUMMARY:")
                        self.logger.debug(f"- Research question: {research_question}")
                        self.logger.debug(f"- Iterations completed: {iteration}")
                        self.logger.debug(f"- Tool calls made: {len(tool_call_log)}")
                        self.logger.debug(f"- Scratchpad notes length: {len(scratchpad_content)} characters")
                        
                        # Show scratchpad content
                        self.logger.debug("\n📝 SCRATCHPAD CONTENT:")
                        self.logger.debug("-"*self.logger.max_width)
                        print(scratchpad_content)
                        self.logger.debug("-"*self.logger.max_width)
                        
                        # Show tool calls
                        self.logger.debug("\n🔧 TOOL CALLS LOG:")
                        self.logger.debug("-"*self.logger.max_width)
                        for i, tc in enumerate(tool_call_log, 1):
                            print(f"\n{i}. {tc['tool']}({json.dumps(tc['args'], ensure_ascii=False)})")
                            print(f"   Result length: {tc.get('result_length', 0)} chars")
                            # Show actual result content
                            result = tc.get('result', '')
                            if len(result) > 500:  # Truncate very long results
                                print(f"   Result (first 500 chars): {result[:500]}...")
                            else:
                                print(f"   Result: {result}")
                        self.logger.debug("-"*self.logger.max_width)
                        
                        # Show the full conversation history
                        self.logger.debug("\n📜 FULL CONVERSATION HISTORY (including all tool results):")
                        self.logger.debug("-"*self.logger.max_width)
                        total_chars = 0
                        for i, msg in enumerate(final_messages):
                            role = msg.get("role", "unknown")
                            content = msg.get("content", "") or ""  # Handle None values
                            
                            # Also check for tool_calls in assistant messages
                            if role == "assistant" and msg.get("tool_calls"):
                                # This is an assistant message with tool calls
                                content_preview = content[:200] + "..." if content and len(content) > 200 else (content or "")
                                tool_count = len(msg.get("tool_calls", []))
                                print(f"\n[{i}] ASSISTANT: {content_preview} [+{tool_count} tool calls]")
                                total_chars += len(content) if content else 0
                                continue
                            
                            total_chars += len(content)
                            
                            if role == "system":
                                print(f"\n[{i}] SYSTEM: {content[:200]}..." if len(content) > 200 else f"\n[{i}] SYSTEM: {content}")
                            elif role == "user":
                                print(f"\n[{i}] USER: {content[:200]}..." if len(content) > 200 else f"\n[{i}] USER: {content}")
                            elif role == "assistant":
                                print(f"\n[{i}] ASSISTANT: {content[:200]}..." if len(content) > 200 else f"\n[{i}] ASSISTANT: {content}")
                            elif role == "tool":
                                tool_id = msg.get("tool_call_id", "unknown")
                                print(f"\n[{i}] TOOL RESULT (id: {tool_id[:8]}...): {content[:300]}..." if len(content) > 300 else f"\n[{i}] TOOL RESULT: {content}")
                        
                        self.logger.debug("-"*self.logger.max_width)
                        
                        # Show the summary prompt that will be added
                        self.logger.debug("\n📄 ADDITIONAL SUMMARY PROMPT:")
                        self.logger.debug("-"*self.logger.max_width)
                        print(summary_prompt)
                        self.logger.debug("-"*self.logger.max_width)
                        self.logger.debug(f"\n📊 Total context size: {total_chars + len(summary_prompt)} characters")
                        self.logger.debug("="*self.logger.max_width + "\n")
                    
                    # Build messages for summary generation - include full conversation history
                    summary_messages = final_messages.copy()
                    
                    # Add the summary generation prompt
                    summary_messages.append({
                        "role": "user",
                        "content": summary_prompt
                    })
                    
                    response = await self.client.chat.completions.create(
                        model=self.model,
                        messages=summary_messages,
                        max_tokens=8192,  # Increased for full reports
                        temperature=0.3,
                        stream=True  # Enable streaming
                    )
                    
                    # Stream the response directly to terminal
                    final_response = ""
                    self.logger.info("\n📝 RESEARCH REPORT:")
                    self.logger.info("━" * self.logger.max_width)
                    print()  # Blank line for cleaner output
                    
                    # Simple approach: buffer words and wrap at word boundaries
                    current_line_length = 0
                    word_buffer = ""
                    
                    async for chunk in response:
                        if chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            
                            for char in content:
                                if char == '\n':
                                    # Flush word buffer and reset line
                                    if word_buffer:
                                        sys.stdout.write(word_buffer)
                                        word_buffer = ""
                                    sys.stdout.write('\n')
                                    sys.stdout.flush()
                                    current_line_length = 0
                                elif char == ' ':
                                    # End of word - check if it fits
                                    word_length = len(word_buffer) + 1  # +1 for space
                                    if current_line_length + word_length > self.logger.max_width:
                                        # Word would overflow - wrap first
                                        sys.stdout.write('\n')
                                        sys.stdout.flush()
                                        current_line_length = 0
                                    # Output word + space
                                    sys.stdout.write(word_buffer + char)
                                    sys.stdout.flush()
                                    current_line_length += word_length
                                    word_buffer = ""
                                else:
                                    # Building up a word
                                    word_buffer += char
                            
                            final_response += content
                    
                    # Flush any remaining word
                    if word_buffer:
                        if current_line_length + len(word_buffer) > self.logger.max_width:
                            sys.stdout.write('\n')
                        sys.stdout.write(word_buffer)
                        sys.stdout.flush()
                    
                    # Add spacing after streaming completes
                    print("\n")
                    self.logger.info("━" * self.logger.max_width)
                    
                    # Emit summary generation end event
                    await self.emit_event("summary_generation_end", {
                        "response": final_response,
                        "sources": self.report_generator.extract_sources(final_response)
                    })
                    
                    await asyncio.sleep(0)
                    break  # Success, exit retry loop
                    
                except Exception as e:
                    error_msg = str(e)
                    self.logger.error(f"Error generating summary: {error_msg}")
                    
                    # Check if it's a retryable error
                    is_retryable = any(phrase in error_msg.lower() for phrase in [
                        "over capacity", "rate limit", "server error", "503", "502", "500"
                    ])
                    
                    retry_count += 1
                    
                    if is_retryable and retry_count < max_retries:
                        retry_delay = min(2 ** retry_count, 30)  # Exponential backoff: 2s, 4s, 8s, max 30s
                        self.logger.info(f"⏳ Retryable error in summary generation. Waiting {retry_delay}s before retry {retry_count}/{max_retries}...")
                        await asyncio.sleep(retry_delay)
                        continue  # Retry
                    else:
                        # Non-retryable error or max retries reached
                        final_response = f"Error generating summary after {retry_count} attempts: {error_msg}"
                        
                        # Emit error event
                        await self.emit_event("summary_generation_end", {
                            "error": error_msg
                        })
                        
                        await asyncio.sleep(0)
                        break
        
        elif tool_call_log and not has_sufficient_data:
            self.logger.error(f"Insufficient research data: only {len(tool_call_log)} tool calls (minimum {min_tool_calls} required)")
            final_response = f"Research incomplete: Only {len(tool_call_log)} tool calls completed (minimum {min_tool_calls} required for meaningful analysis). Please retry or check API availability."
        
        # Report generation phase
        if tool_call_log:
            # Emit report generation events
            await self.emit_event("report_generation_start", {
                "method": "summary"
            })
            
            await asyncio.sleep(0)
            
            await self.emit_event("report_generation_end", {
                "response": final_response,
                "sources": self.report_generator.extract_sources(final_response)
            })
            
            # Store final report
            self.final_report = final_response
        
        # Emit session end event
        await self.emit_event("session_end", {
            "final_response": final_response,
            "total_iterations": iteration,
            "total_tool_calls": len(tool_call_log)
        })
        
        return final_response
    
    def _log_statistics(self):
        """Log research statistics"""
        duration = datetime.now() - self.stats['start_time']
        self.logger.info(f"\n━" * self.logger.max_width)
        self.logger.info(f"📊 RESEARCH STATISTICS")
        self.logger.info("━" * self.logger.max_width)
        self.logger.info(f"⏱️  Duration: {duration.seconds}s")
        self.logger.info(f"🔄 Iterations completed: {self.stats['iterations']}")
        self.logger.info(f"🔧 Tool calls made: {self.stats['tool_calls']}")
        
        if self.stats['input_tokens'] > 0:
            total_tokens = self.stats['input_tokens'] + self.stats['output_tokens']
            token_info = f"📝 Tokens processed: {total_tokens:,} (input: {self.stats['input_tokens']:,}, output: {self.stats['output_tokens']:,})"
            self.logger.info(self.logger._wrap_text(token_info))
            
        if hasattr(self.provider_config, 'cost_per_1k_input'):
            if self.stats['total_cost'] > 0:
                self.logger.info(f"💰 Total cost: ${self.stats['total_cost']:.4f} ({self.provider_config.name})")
            else:
                self.logger.info(f"💰 Total cost: Free ({self.provider_config.name})")
        
        if self.stats['sub_agents_spawned'] > 0:
            self.logger.info(f"👥 Sub-agents spawned: {self.stats['sub_agents_spawned']}")
            
        self.logger.info(f"🆔 Session ID: {self.session_id}")
        self.logger.info("━" * self.logger.max_width + "\n")
    
    def _prepare_results(
        self,
        final_response: str,
        tool_call_log: List[Dict[str, Any]],
        iterations: int,
        final_messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Prepare results dictionary"""
        # Make stats serializable
        serializable_stats = self.stats.copy()
        if isinstance(serializable_stats['start_time'], datetime):
            serializable_stats['start_time'] = serializable_stats['start_time'].isoformat()
        
        # Include scratchpad if in research mode
        scratchpad_content = None
        if self.research_mode:
            try:
                from src.tools.scratchpad_tools import read_notes
                scratchpad_content = read_notes(self.session_id)
            except Exception:
                pass
        
        # Return results
        return {
            "final_response": final_response,
            "final_report": getattr(self, 'final_report', final_response),
            "tool_calls": tool_call_log,
            "iterations": iterations,
            "session_id": self.session_id,
            "stats": serializable_stats,
            "scratchpad": scratchpad_content,
            "full_conversation": final_messages
        }
    
    async def spawn_sub_agent(self, question: str, context: str, max_iterations: int = 10):
        """Spawn a sub-agent for delegated research"""
        self.logger.info(f"🚀 Delegating to sub-agent (depth {self.depth + 1}):")
        self.logger.info(f"📝 Question: {question[:150]}...")
        self.logger.info(f"🎯 Context: {context[:100]}..." if context else "🎯 No context provided")
        self.logger.info(f"⚙️  Max iterations: {max_iterations}")
        
        # Use tool executor to spawn sub-agent
        result = await self.tool_executor.execute_spawn_sub_agent(
            self.tools["spawn_sub_agent"]["command"],
            {
                "question": question,
                "context": context,
                "max_iterations": max_iterations
            },
            self.depth,
            self.max_depth
        )
        
        return result