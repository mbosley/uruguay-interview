"""Tool execution and preview generation for the research agent"""

import json
import subprocess
import asyncio
import os
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from src.tools.interview_renderer import InterviewRenderer
from src.tools.corpus_renderer import CorpusRenderer


class ToolExecutor:
    """Handles tool execution and result processing"""
    
    def __init__(self, session_id: str, logger=None):
        self.session_id = session_id
        self.logger = logger
        self.interview_renderer = InterviewRenderer(max_width=logger.max_width if logger else 80)
        self.corpus_renderer = CorpusRenderer(max_width=logger.max_width if logger else 80)
    
    async def execute_cli_tool(self, tool_name: str, command_template: str, arguments: Dict[str, Any]) -> Tuple[str, str]:
        """Execute a CLI tool with the given arguments
        
        Returns:
            Tuple[str, str]: (raw_result, rendered_result)
        """
        try:
            if self.logger:
                self.logger.debug(f"[ToolExecutor] Starting {tool_name} with args: {arguments}")
                self.logger.debug(f"[ToolExecutor] Command template: {command_template}")
            
            # Replace placeholders in command
            command = command_template
            for key, value in arguments.items():
                placeholder = f"{{{key}}}"
                if placeholder in command:
                    # Handle different value types
                    if isinstance(value, str):
                        # Properly escape for shell
                        if tool_name in ["scratchpad_append", "scratchpad_read"] and key == "note":
                            # For scratchpad, use base64 encoding
                            import base64
                            value_b64 = base64.b64encode(value.encode()).decode()
                            command = command.replace(placeholder, value_b64)
                        else:
                            command = command.replace(placeholder, f'"{value}"')
                    else:
                        command = command.replace(placeholder, str(value))
            
            # For scratchpad tools, use base64 to safely pass arguments  
            if tool_name in ["scratchpad_append", "scratchpad_read"]:
                if "note" in arguments:
                    # Use base64 to safely encode the note content
                    import base64
                    note_b64 = base64.b64encode(arguments["note"].encode()).decode()
                    session_id = arguments.get("session_id", self.session_id)
                    full_command = f'python -c "import base64; from src.tools.scratchpad_tools import append_note; print(append_note(base64.b64decode(\'{note_b64}\').decode(), \'{session_id}\'))"'
                else:
                    # For scratchpad_read, always use agent's session_id
                    session_id = arguments.get("session_id", self.session_id)
                    full_command = f'python -c "from src.tools.scratchpad_tools import read_notes; print(read_notes(\'{session_id}\'))"'
            else:
                full_command = command
            
            if self.logger:
                self.logger.debug(f"[ToolExecutor] Final command: {full_command}")
            
            # Execute command
            try:
                result = subprocess.run(
                    full_command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30  # 30 second timeout
                )
                
                if self.logger:
                    self.logger.debug(f"[ToolExecutor] Return code: {result.returncode}")
                    if result.stderr:
                        self.logger.debug(f"[ToolExecutor] Stderr: {result.stderr}")
                    self.logger.debug(f"[ToolExecutor] Stdout length: {len(result.stdout)}")
                
                if result.returncode != 0:
                    error_msg = f"Error: {result.stderr}"
                    return error_msg, error_msg
                
                output = result.stdout.strip()
                
                # Apply rendering for different tool types
                rendered = output  # Default to raw output
                if tool_name in ["get_interview_turn"]:
                    rendered = self.interview_renderer.render(output)
                elif tool_name in ["get_corpus_stats", "explore_meta_theme", "search_interviews", "search_themes"]:
                    rendered = self.corpus_renderer.render(output)
                
                return output, rendered
                
            except subprocess.TimeoutExpired:
                error_msg = "Error: Command timed out after 30 seconds"
                return error_msg, error_msg
                
        except Exception as e:
            error_msg = f"Error executing tool: {str(e)}"
            return error_msg, error_msg
    
    async def execute_spawn_sub_agent(
        self, 
        command_template: str, 
        arguments: Dict[str, Any],
        parent_depth: int = 0,
        max_depth: int = 2
    ) -> Tuple[str, str]:
        """Execute a sub-agent spawn command
        
        Returns:
            Tuple[str, str]: (raw_result, rendered_result)
        """
        # Check depth limit
        if parent_depth >= max_depth:
            error_result = json.dumps({
                "error": "Maximum delegation depth reached",
                "suggestion": "Consider broadening your current investigation instead of delegating further"
            })
            return error_result, error_result
        
        # Prepare command with depth parameters
        command = command_template
        command = command.replace("{depth}", str(parent_depth + 1))
        command = command.replace("{parent_id}", self.session_id)
        command = command.replace("{max_depth}", str(max_depth))
        
        # Replace other arguments
        for key, value in arguments.items():
            placeholder = f"{{{key}}}"
            if placeholder in command:
                if isinstance(value, str):
                    # Escape quotes in the string
                    escaped_value = value.replace('"', '\\"')
                    command = command.replace(placeholder, f'"{escaped_value}"')
                else:
                    command = command.replace(placeholder, str(value))
        
        # Set sub-agent specific environment variables
        env = os.environ.copy()
        env['SUB_AGENT_PARENT'] = self.session_id
        env['SUB_AGENT_DEPTH'] = str(parent_depth + 1)
        
        # Execute with longer timeout for sub-agents
        timeout = arguments.get('max_iterations', 10) * 30  # 30s per iteration
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env
            )
            
            if result.returncode != 0:
                error_result = json.dumps({
                    "error": f"Sub-agent failed: {result.stderr}",
                    "stdout": result.stdout
                })
                return error_result, error_result
            
            # Try to parse as JSON first
            try:
                output = result.stdout.strip()
                return output, output  # No special rendering for sub-agent results
            except:
                # If not JSON, return as string result
                json_result = json.dumps({
                    "response": result.stdout.strip(),
                    "status": "completed"
                })
                return json_result, json_result
                
        except subprocess.TimeoutExpired:
            timeout_result = json.dumps({
                "error": f"Sub-agent timed out after {timeout} seconds",
                "partial_output": "Sub-agent may still be running. Consider reducing max_iterations or simplifying the research question."
            })
            return timeout_result, timeout_result
        except Exception as e:
            error_msg = f"Failed to execute command: {str(e)}"
            return error_msg, error_msg
    
    def generate_preview(self, tool_name: str, result: str) -> str:
        """Generate informative preview based on tool type"""
        try:
            # Check if result is an error message
            if result.startswith("Error:"):
                return result[:100] + "..." if len(result) > 100 else result
            
            if tool_name == "get_corpus_stats":
                data = json.loads(result)
                return f"{data.get('total_interviews', 0)} interviews, {data.get('total_turns', 0)} turns"
            
            elif tool_name == "search_interviews":
                data = json.loads(result)
                results = data.get('results', [])
                return f"Found {len(results)} results"
            
            elif tool_name == "get_interview_turn":
                data = json.loads(result)
                if data.get('type') == 'interview_summary':
                    return f"Interview {data.get('interview_id', '')} summary"
                elif data.get('turns'):
                    return f"{len(data.get('turns', []))} turns retrieved"
            
            elif tool_name == "explore_meta_theme":
                data = json.loads(result)
                if data.get("error"):
                    return data.get("error")
                # Handle meta-theme exploration
                if 'meta_themes' in data and data.get('meta_theme_filter'):
                    meta_themes = data['meta_themes']
                    if meta_themes:
                        meta_key, meta_data = list(meta_themes.items())[0]
                        theme_count = len(meta_data.get('themes', {}))
                        return f"Found {theme_count} themes in {meta_data.get('name', meta_key)}"
                else:
                    return f"Found {data.get('total_themes', 0)} themes"
            
            elif tool_name == "search_themes":
                data = json.loads(result)
                return f"Found {len(data.get('matching_themes', {}))} matching themes"
            
            elif tool_name == "scratchpad_append":
                return "Note added"
            
            elif tool_name == "scratchpad_read":
                lines = result.strip().split('\n')
                return f"{len(lines)} note entries"
            
            elif tool_name == "spawn_sub_agent":
                try:
                    data = json.loads(result)
                    if 'error' in data:
                        return f"Error: {data['error'][:100]}..."
                    elif 'final_response' in data:
                        return f"Sub-agent completed: {data.get('iterations', 0)} iterations"
                    else:
                        return "Sub-agent completed"
                except:
                    return "Sub-agent response received"
            
        except (json.JSONDecodeError, KeyError, AttributeError) as e:
            # Fallback for non-JSON results or when result is already rendered
            if self.logger:
                self.logger.debug(f"[ToolExecutor] Preview generation fallback for {tool_name}: {type(e).__name__}")
            
            # Check if this is rendered output
            if any(marker in str(result) for marker in ["═", "━", "─", "THEMES", "STATISTICS", "RESULTS"]):
                # Extract meaningful line from rendered output
                lines = result.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not any(char * 5 in line for char in "═━─"):
                        if any(keyword in line for keyword in ["Found", "Total", "themes", "interviews", "matching"]):
                            return line[:200]
                return "Rendered output"
            
            # Simple fallback
            lines = result.strip().split('\n')
            if lines and lines[0]:
                return lines[0][:200] + "..." if len(lines[0]) > 200 else lines[0]
        
        return "Result received"