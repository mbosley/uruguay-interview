"""Logging utilities for the research agent"""

import logging
import json
import sys
import textwrap

# ANSI color codes for pretty terminal output
reset = "\033[0m"
bold = "\033[1m"
black = "\033[30m"
red = "\033[31m"
green = "\033[32m"
yellow = "\033[33m"
blue = "\033[34m"
magenta = "\033[35m"
cyan = "\033[36m"
white = "\033[37m"
bold_red = "\033[1;31m"
bold_green = "\033[1;32m"
bold_yellow = "\033[1;33m"
bold_blue = "\033[1;34m"


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels"""
    
    FORMATS = {
        logging.DEBUG: cyan + "🔍 %(message)s" + reset,
        logging.INFO: "%(message)s",
        logging.WARNING: yellow + "⚠️  %(message)s" + reset,
        logging.ERROR: red + "❌ %(message)s" + reset,
        logging.CRITICAL: bold_red + "🚨 %(message)s" + reset
    }
    
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class AgentLogger:
    """Specialized logger for agent activities"""
    
    def __init__(self, research_mode=False, debug=False, max_width=80):
        self.research_mode = research_mode
        self.debug_mode = debug  # Renamed to avoid conflict with debug() method
        self.max_width = max_width
        self.logger = logging.getLogger("agent")
        self.logger.setLevel(logging.DEBUG if debug else logging.INFO)
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # Console handler with colors
        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(ColoredFormatter())
        self.logger.addHandler(console)
    
    def _format_size(self, size):
        """Format byte size for display"""
        if size < 1024:
            return f"{size} chars"
        elif size < 1024 * 1024:
            return f"{size/1024:.1f}K chars"
        else:
            return f"{size/(1024*1024):.1f}M chars"
    
    def _wrap_text(self, text, indent="", subsequent_indent=None):
        """Wrap text to max width with proper indentation"""
        if subsequent_indent is None:
            subsequent_indent = indent
        
        wrapper = textwrap.TextWrapper(
            width=self.max_width,
            initial_indent=indent,
            subsequent_indent=subsequent_indent,
            break_long_words=False,
            break_on_hyphens=False
        )
        return wrapper.fill(text)
    
    def iteration_header(self, current, total):
        """Log iteration header - using double line for clear iteration boundaries"""
        self.logger.info("\n" + "═"*self.max_width)
        self.logger.info(f"🔄 ITERATION {current}/{total}")
        self.logger.info("═"*self.max_width)
    
    def complete(self, message):
        """Log completion message"""
        self.logger.info(f"✨ {message}")
    
    def progress(self, message):
        """Log progress update"""
        self.logger.info(f"▶️  {message}")
    
    def info(self, message):
        """Standard info logging"""
        self.logger.info(message)
    
    def error(self, message):
        """Error logging"""
        self.logger.error(message)
    
    def debug(self, message):
        """Debug logging"""
        self.logger.debug(message)
    
    def thinking(self, message):
        """Log agent's thinking process - using light dashes for subsections"""
        if message:
            # Show thinking in a more structured way
            self.logger.info("\n💭 AGENT THINKING:")
            self.logger.info("─" * self.max_width)
            # In research mode, show full thinking
            limit = 3000 if self.research_mode else 500
            if len(message) > limit:
                message = message[:limit-3] + "..."
            
            # Wrap each paragraph separately to preserve structure
            paragraphs = message.strip().split('\n')
            for para in paragraphs:
                if para.strip():  # Only process non-empty paragraphs
                    wrapped = self._wrap_text(para, indent="  ")
                    self.logger.info(wrapped)
                else:
                    self.logger.info("")  # Preserve blank lines
            self.logger.info("─" * self.max_width)
    
    def tool_call(self, tool_name, args):
        """Log tool usage"""
        # Create more informative descriptions based on tool and args
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
            note = args["note"]
            # Show full note with proper formatting
            self.logger.info(f"\n📝 ADDING TO SCRATCHPAD:")
            self.logger.info("─" * self.max_width)
            # Wrap each paragraph separately
            paragraphs = note.strip().split('\n')
            for para in paragraphs:
                if para.strip():
                    wrapped = self._wrap_text(para, indent="  ")
                    self.logger.info(wrapped)
                else:
                    self.logger.info("")  # Preserve blank lines
            self.logger.info("─" * self.max_width)
            return  # Don't print the standard tool message
        elif tool_name == "scratchpad_read":
            desc = "Reading research notes"
        elif tool_name == "get_corpus_stats":
            desc = "Getting corpus statistics"
        elif tool_name == "search_themes" and args.get("keyword"):
            desc = f'Searching themes for "{args["keyword"]}"'
        elif tool_name == "spawn_sub_agent" and args.get("question"):
            q_preview = args["question"][:50] + "..." if len(args["question"]) > 50 else args["question"]
            desc = f'Delegating: "{q_preview}"'
        else:
            # Fallback to original format
            if args:
                args_str = json.dumps(args, ensure_ascii=False)
                limit = 1000 if self.research_mode else 300
                if len(args_str) > limit:
                    args_str = args_str[:limit-3] + "..."
            else:
                args_str = "{}"
            desc = f"{tool_name}({args_str})"
        
        # Wrap long tool descriptions
        tool_line = f"🔧 {desc}"
        if len(tool_line) > self.max_width:
            wrapped = self._wrap_text(tool_line)
            self.logger.info(wrapped)
        else:
            self.logger.info(tool_line)
    
    def tool_result(self, size, preview=None, tool_name=None, result=None):
        """Log tool result with more context"""
        size_str = self._format_size(size)
        
        # Special handling for scratchpad_append - no result to show
        if tool_name == "scratchpad_append":
            return
        
        # Special handling for rendered outputs - show full content
        if result and (
            (tool_name == "get_interview_turn" and "INTERVIEW" in str(result) and ("SUMMARY" in str(result) or "TURN" in str(result))) or
            (tool_name == "get_corpus_stats" and "CORPUS STATISTICS" in str(result)) or
            (tool_name == "explore_meta_theme" and ("Total themes:" in str(result) or "Exploring:" in str(result))) or
            (tool_name == "search_interviews" and "SEARCH RESULTS" in str(result)) or
            (tool_name == "search_themes" and ("THEME SEARCH RESULTS" in str(result) or "Total themes:" in str(result)))
        ):
            self.logger.info(f"✅ {size_str}")
            # Show the full rendered output on new lines
            self.logger.info(result)
            return
        
        # Extract meaningful info from results
        extra_info = ""
        if tool_name == "search_interviews" and result:
            try:
                # Count matches in different categories
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
        elif tool_name == "list_interview_themes" and result:
            try:
                # Count unique themes
                lines = [l.strip() for l in result.strip().split('\n') if l.strip() and not l.startswith('Theme occurrences')]
                theme_count = len([l for l in lines if ': ' in l])
                if theme_count:
                    extra_info = f" {theme_count} unique themes listed"
            except:
                pass
        elif tool_name == "get_interview_turn" and ":" in str(preview or ""):
            # Already has good info in preview
            pass
        
        if preview:
            # Clean preview
            preview = preview.strip()
            limit = 2000 if self.research_mode else 400
            if len(preview) > limit:
                preview = preview[:limit-3] + "..."
            result_line = f"✅ {size_str}{extra_info} | {preview}"
            if len(result_line) > self.max_width:
                # Wrap the result line
                wrapped = self._wrap_text(result_line)
                self.logger.info(wrapped)
            else:
                self.logger.info(result_line)
        else:
            result_line = f"✅ {size_str}{extra_info}"
            if len(result_line) > self.max_width:
                wrapped = self._wrap_text(result_line)
                self.logger.info(wrapped)
            else:
                self.logger.info(result_line)