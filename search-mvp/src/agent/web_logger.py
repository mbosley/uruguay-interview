"""Web-enabled logger that emits console output as events"""

import asyncio
from typing import Optional, Callable
from .logger import AgentLogger, reset


class WebLogger(AgentLogger):
    """Logger that also emits console output as events for web display"""
    
    def __init__(self, event_handler=None, research_mode=False, debug=False, max_width=80):
        super().__init__(research_mode, debug, max_width)
        self.event_handler = event_handler
        self.buffer = []
        self.buffering = False
    
    async def _emit_output(self, text: str):
        """Emit console output as event"""
        if self.event_handler:
            # Strip ANSI color codes for web display
            clean_text = self._strip_ansi(text)
            await self.event_handler.emit_event("console_output", {
                "text": clean_text
            })
            # Ensure event is sent immediately
            await asyncio.sleep(0)
    
    def _strip_ansi(self, text: str) -> str:
        """Remove ANSI escape codes from text"""
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)
    
    def _format_citations(self, text: str) -> str:
        """Keep citations in their original double bracket format"""
        # No longer converting citations - keep them as [[XXX:YYY]]
        return text
    
    def _schedule_emit(self, text: str):
        """Schedule emission of output event"""
        if self.event_handler:
            try:
                # Try to get current event loop
                loop = asyncio.get_running_loop()
                # Create task without waiting
                task = loop.create_task(self._emit_output(text))
                # Add error handler to avoid uncaught exceptions
                task.add_done_callback(lambda t: t.exception() if t.done() else None)
            except RuntimeError:
                # No event loop - this shouldn't happen in our async context
                pass
    
    def _log_and_emit(self, message: str):
        """Log to console and emit as event"""
        # Log normally
        self.logger.info(message)
        
        # Schedule event emission
        self._schedule_emit(message + '\n')
    
    def iteration_header(self, current, total):
        """Log iteration header"""
        text = f"\n{'═'*self.max_width}\n🔄 ITERATION {current}/{total}\n{'═'*self.max_width}"
        self._log_and_emit(text)
    
    def complete(self, message):
        """Log completion message"""
        self._log_and_emit(f"✨ {message}")
    
    def progress(self, message):
        """Log progress update"""
        self._log_and_emit(f"▶️  {message}")
    
    def info(self, message):
        """Standard info logging"""
        self._log_and_emit(message)
    
    def error(self, message):
        """Error logging"""
        self.logger.error(message)
        self._schedule_emit(f"❌ {message}\n")
    
    def debug(self, message):
        """Debug logging"""
        self.logger.debug(message)
        if self.debug_mode:
            self._schedule_emit(f"🔍 {message}\n")
    
    def thinking(self, message):
        """Log agent's thinking process"""
        if message:
            # Convert citations to human-readable format
            message = self._format_citations(message)
            
            lines = [
                "\n💭 AGENT THINKING:",
                "─" * self.max_width
            ]
            
            # Process message
            limit = 3000 if self.research_mode else 500
            if len(message) > limit:
                message = message[:limit-3] + "..."
            
            # Wrap paragraphs
            paragraphs = message.strip().split('\n')
            for para in paragraphs:
                if para.strip():
                    wrapped = self._wrap_text(para, indent="  ")
                    lines.append(wrapped)
                else:
                    lines.append("")
            
            lines.append("─" * self.max_width)
            
            # Log and emit
            full_text = '\n'.join(lines)
            self._log_and_emit(full_text)
    
    def tool_call(self, tool_name, args):
        """Log tool usage"""
        # Create tool description (same logic as parent)
        if tool_name == "search_interviews" and args.get("query"):
            desc = f'Searching for "{args["query"]}"'
        elif tool_name == "get_interview_turn" and args.get("turn_id"):
            turn_id = args["turn_id"]
            if ":" in turn_id and turn_id.endswith(":"):
                desc = f"Getting summary of interview {turn_id[:-1]}"
            elif ":" in turn_id and "-" in turn_id:
                desc = f"Reading turns {turn_id}"
            elif ":" in turn_id:
                desc = f"Reading turn {turn_id}"
            else:
                desc = f"Getting {turn_id}"
        elif tool_name == "list_interview_themes":
            if args.get("interview_id"):
                desc = f"Listing themes for interview {args['interview_id']}"
            else:
                desc = "Getting all 121 themes across corpus"
        elif tool_name == "scratchpad_append" and args.get("note"):
            # Special handling for scratchpad
            note = args["note"]
            
            # Convert citations to human-readable format
            note = self._format_citations(note)
            
            lines = [
                "\n📝 ADDING TO SCRATCHPAD:",
                "─" * self.max_width
            ]
            
            paragraphs = note.strip().split('\n')
            for para in paragraphs:
                if para.strip():
                    wrapped = self._wrap_text(para, indent="  ")
                    lines.append(wrapped)
                else:
                    lines.append("")
            
            lines.append("─" * self.max_width)
            full_text = '\n'.join(lines)
            self._log_and_emit(full_text)
            return
        elif tool_name == "scratchpad_read":
            desc = "Reading research notes"
        elif tool_name == "complete_research":
            # First emit the tool call line
            desc = f"complete_research({{\"summary\": \"{args.get('summary', '')[:50]}...\", \"evidence_count\": {args.get('evidence_count', 0)}}})"
            tool_line = f"🔧 {desc}"
            if len(tool_line) > self.max_width:
                tool_line = self._wrap_text(tool_line)
            self._log_and_emit(tool_line)
            
            # Then handle the special formatting
            summary = args.get("summary", "Research completed")
            evidence_count = args.get("evidence_count", 0)
            
            # Format citations in the summary
            formatted_summary = self._format_citations(summary)
            
            lines = [
                "",
                "═" * self.max_width,
                "🏁 EARLY COMPLETION REQUESTED",
                "═" * self.max_width,
                "📋 Summary:",
                "─" * self.max_width
            ]
            
            # Wrap the summary paragraphs
            paragraphs = formatted_summary.strip().split('\n')
            for para in paragraphs:
                if para.strip():
                    wrapped = self._wrap_text(para, indent="  ")
                    lines.append(wrapped)
                else:
                    lines.append("")
            
            lines.extend([
                "─" * self.max_width,
                "",
                f"📊 Evidence collected: {evidence_count} interviews/sources",
                "═" * self.max_width
            ])
            
            full_text = '\n'.join(lines)
            self._log_and_emit(full_text)
            return
        elif tool_name == "get_corpus_stats":
            desc = "Getting corpus statistics"
        elif tool_name == "search_themes" and args.get("keyword"):
            desc = f'Searching themes for "{args["keyword"]}"'
        elif tool_name == "spawn_sub_agent" and args.get("question"):
            q_preview = args["question"][:50] + "..." if len(args["question"]) > 50 else args["question"]
            desc = f'Delegating: "{q_preview}"'
        else:
            # Fallback
            import json
            args_str = json.dumps(args, ensure_ascii=False)
            limit = 1000 if self.research_mode else 300
            if len(args_str) > limit:
                args_str = args_str[:limit-3] + "..."
            desc = f"{tool_name}({args_str})"
        
        # Format and emit
        tool_line = f"🔧 {desc}"
        if len(tool_line) > self.max_width:
            tool_line = self._wrap_text(tool_line)
        
        self._log_and_emit(tool_line)
    
    def tool_result(self, size, preview=None, tool_name=None, result=None):
        """Log tool result"""
        size_str = self._format_size(size)
        
        # Skip scratchpad_append and complete_research (handled in tool_call)
        if tool_name in ["scratchpad_append", "complete_research"]:
            return
        
        # Check if the result appears to be formatted output (contains emoji headers or structured content)
        is_formatted = False
        if result:
            result_str = str(result)
            # Check for common formatted output indicators
            formatted_indicators = [
                "📊", "🔍", "🎯", "📚", "💬", "📈",  # Emojis used in formatting
                "CORPUS STATISTICS", "INTERVIEW THEMES", "SEARCH RESULTS",  # Headers
                "INTERVIEW", "TURN", "SUMMARY"  # Interview formatting
            ]
            is_formatted = any(indicator in result_str for indicator in formatted_indicators)
        
        # If we have formatted output, display it in full
        if is_formatted:
            self._log_and_emit(f"✅ {size_str}")
            # Format citations in the result
            formatted_result = self._format_citations(str(result))
            
            # Apply text wrapping to each line
            wrapped_lines = []
            for line in formatted_result.split('\n'):
                # Special handling for bullet points - wrap them with indent preserved
                if line.startswith('  • ') and len(line) > self.max_width:
                    # Extract the bullet content
                    bullet_content = line[4:]  # Remove '  • '
                    wrapped = self._wrap_text(bullet_content, indent="    ")  # Indent continuation
                    wrapped_lines.append('  • ' + wrapped[4:])  # Re-add bullet, remove extra indent from first line
                elif len(line) > self.max_width:
                    wrapped = self._wrap_text(line)
                    wrapped_lines.append(wrapped)
                else:
                    wrapped_lines.append(line)
            
            self._log_and_emit('\n'.join(wrapped_lines))
            return
        
        # Build result line
        extra_info = ""
        if tool_name == "search_interviews" and result:
            try:
                lines = result.strip().split('\n')
                theme_matches = sum(1 for line in lines if line.startswith("THEME MATCH:"))
                tag_matches = sum(1 for line in lines if line.startswith("TAG MATCH:"))
                text_matches = sum(1 for line in lines if line.startswith("MATCH:"))
                if theme_matches or tag_matches or text_matches:
                    parts = []
                    if theme_matches: parts.append(f"{theme_matches} themes")
                    if tag_matches: parts.append(f"{tag_matches} tags")
                    if text_matches: parts.append(f"{text_matches} text matches")
                    extra_info = f" Found: {', '.join(parts)}"
            except:
                pass
        
        # Format final line
        if preview:
            preview = preview.strip()
            limit = 2000 if self.research_mode else 400
            if len(preview) > limit:
                preview = preview[:limit-3] + "..."
            result_line = f"✅ {size_str}{extra_info} | {preview}"
        else:
            result_line = f"✅ {size_str}{extra_info}"
        
        if len(result_line) > self.max_width:
            result_line = self._wrap_text(result_line)
        
        self._log_and_emit(result_line)