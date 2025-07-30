"""Render interview JSON data as readable plain text"""

import json
import textwrap
from typing import Dict, Any, List, Optional


class InterviewRenderer:
    """Render interview data in a human-readable format"""
    
    def __init__(self, max_width: int = 80):
        self.max_width = max_width
        self.wrapper = textwrap.TextWrapper(
            width=max_width,
            break_long_words=False,
            break_on_hyphens=False
        )
    
    def render(self, data: str) -> str:
        """Render interview data from JSON string to readable text"""
        try:
            parsed = json.loads(data)
            
            # Determine the type of data and render accordingly
            if parsed.get("type") == "interview_summary":
                return self._render_summary(parsed)
            elif parsed.get("type") == "single_turn":
                return self._render_single_turn(parsed)
            elif parsed.get("type") == "turn_range":
                return self._render_turns(parsed)
            elif parsed.get("turns"):
                return self._render_turns(parsed)
            elif parsed.get("interview_id") and parsed.get("themes"):
                return self._render_themes(parsed)
            elif parsed.get("total_interviews") and parsed.get("total_turns"):
                return self._render_corpus_stats(parsed)
            elif parsed.get("meta_themes") or (parsed.get("themes") and not parsed.get("interview_id")):
                return self._render_all_themes(parsed)
            else:
                # Fallback to original JSON if structure unknown
                return data
                
        except (json.JSONDecodeError, KeyError):
            # Return original if not valid JSON
            return data
    
    def _render_summary(self, data: Dict[str, Any]) -> str:
        """Render interview summary in readable format"""
        lines = []
        
        # Header
        interview_id = data.get("interview_id", "Unknown")
        lines.append("\n" + "─" * self.max_width)
        lines.append(f"INTERVIEW {interview_id} - SUMMARY")
        lines.append("─" * self.max_width)
        
        # Metadata
        metadata = data.get("metadata", {})
        if metadata:
            lines.append("\n📍 METADATA:")
            # Try to get location from different possible fields
            location = metadata.get("location") or metadata.get("place") or ""
            if location:
                lines.append(f"  Location: {location}")
            
            # Try to get date from different fields
            date = metadata.get("date") or metadata.get("interview_date") or ""
            if date:
                lines.append(f"  Date: {date}")
            
            # Duration
            if metadata.get("duration"):
                lines.append(f"  Duration: {metadata['duration']}")
            
            # Participants - handle both list and count
            participants = metadata.get("participants", [])
            if isinstance(participants, list) and participants:
                lines.append(f"  Participants: {len(participants)}")
            elif isinstance(participants, int) and participants > 0:
                lines.append(f"  Participants: {participants}")
            
            # Total turns from metadata if available
            if metadata.get("total_turns"):
                lines.append(f"  Total turns: {metadata['total_turns']}")
        
        # Key themes
        themes = data.get("key_themes", [])
        if themes:
            lines.append("\n🎯 KEY THEMES:")
            for theme in themes[:5]:  # Top 5 themes
                if isinstance(theme, dict):
                    theme_name = theme.get("theme", "")
                    # Use intensity if count is not available
                    count = theme.get("count")
                    intensity = theme.get("intensity", "")
                    if count:
                        lines.append(f"  • {theme_name} ({count} mentions)")
                    elif intensity:
                        lines.append(f"  • {theme_name} ({intensity} intensity)")
                    else:
                        lines.append(f"  • {theme_name}")
                else:
                    lines.append(f"  • {theme}")
        
        # Summary text
        summary = data.get("summary", "")
        if summary:
            lines.append("\n📝 SUMMARY:")
            wrapped = self._wrap_text(summary, indent="  ")
            lines.append(wrapped)
        
        # Key insights
        insights = data.get("key_insights", [])
        if insights:
            lines.append("\n💡 KEY INSIGHTS:")
            for i, insight in enumerate(insights, 1):
                wrapped = self._wrap_text(f"{i}. {insight}", indent="  ")
                lines.append(wrapped)
        
        # Notable quotes
        quotes = data.get("notable_quotes", [])
        if quotes:
            lines.append("\n💬 NOTABLE QUOTES:")
            for quote in quotes[:3]:  # Top 3 quotes
                if isinstance(quote, dict):
                    # Handle both 'text' and 'quote' field names
                    text = quote.get("quote", quote.get("text", ""))
                    speaker = quote.get("speaker", "Unknown")
                    turn = quote.get("turn", "")
                    
                    if text:  # Only show if there's actual quote text
                        wrapped = self._wrap_text(f'"{text}"', indent="  ")
                        lines.append(wrapped)
                        if turn:
                            lines.append(f"    - {speaker}, Turn {turn}")
                        else:
                            lines.append(f"    - {speaker}")
                else:
                    wrapped = self._wrap_text(f'"{quote}"', indent="  ")
                    lines.append(wrapped)
        
        # Total turns - check multiple possible locations
        total_turns = data.get("total_turns") or data.get("stats", {}).get("total_turns") or metadata.get("total_turns", 0)
        if total_turns:
            lines.append(f"\n📊 Total turns in interview: {total_turns}")
        
        # Additional stats if available
        stats = data.get("stats", {})
        if stats.get("theme_count"):
            lines.append(f"📂 Themes in interview: {stats['theme_count']}")
        if stats.get("notable_quotes"):
            lines.append(f"💬 Notable quotes: {stats['notable_quotes']}")
        
        lines.append("─" * self.max_width)
        
        return "\n".join(lines)
    
    def _render_turns(self, data: Dict[str, Any]) -> str:
        """Render interview turns in readable format"""
        lines = []
        
        interview_id = data.get("interview_id", "Unknown")
        turns = data.get("turns", [])
        
        if not turns:
            return "No turns found"
        
        # Header
        lines.append("\n" + "─" * self.max_width)
        if len(turns) == 1:
            lines.append(f"INTERVIEW {interview_id} - TURN {turns[0].get('turn_number', '?')}")
        else:
            first_turn = turns[0].get('turn_number', '?')
            last_turn = turns[-1].get('turn_number', '?')
            lines.append(f"INTERVIEW {interview_id} - TURNS {first_turn}-{last_turn}")
        lines.append("─" * self.max_width)
        
        # Render each turn
        for turn in turns:
            turn_num = turn.get("turn_number", "?")
            speaker = turn.get("speaker", "Unknown")
            text = turn.get("text", "")
            
            # Format speaker line
            speaker_line = f"\n[{turn_num}] {speaker}:"
            lines.append(speaker_line)
            
            # Wrap and indent the text
            wrapped = self._wrap_text(text, indent="    ")
            lines.append(wrapped)
            
            # Add themes if present
            themes = turn.get("themes", [])
            if themes:
                theme_list = ", ".join(themes) if isinstance(themes, list) else str(themes)
                lines.append(f"    [Themes: {theme_list}]")
        
        lines.append("\n" + "─" * self.max_width)
        
        return "\n".join(lines)
    
    def _render_themes(self, data: Dict[str, Any]) -> str:
        """Render interview themes in readable format"""
        lines = []
        
        interview_id = data.get("interview_id", "Unknown")
        themes = data.get("themes", {})
        
        lines.append("\n" + "─" * self.max_width)
        lines.append(f"THEMES - INTERVIEW {interview_id}")
        lines.append("─" * self.max_width)
        
        if isinstance(themes, dict):
            # Themes with turn numbers
            sorted_themes = sorted(themes.items(), key=lambda x: len(x[1]), reverse=True)
            for theme, turns in sorted_themes:
                turn_list = ", ".join(str(t) for t in turns) if isinstance(turns, list) else str(turns)
                lines.append(f"\n• {theme}")
                wrapped = self._wrap_text(f"  Turns: {turn_list}", indent="  ")
                lines.append(wrapped)
        else:
            # Simple theme list
            for theme in themes:
                lines.append(f"• {theme}")
        
        lines.append("\n" + "─" * self.max_width)
        
        return "\n".join(lines)
    
    def _render_single_turn(self, data: Dict[str, Any]) -> str:
        """Render a single turn with enrichment data"""
        lines = []
        
        turn_data = data.get("turn", {})
        enrichment = data.get("enrichment", {})
        
        interview_id = turn_data.get("interview_id", "Unknown")
        turn_num = turn_data.get("turn_number", "?")
        
        # Header
        lines.append("\n" + "─" * self.max_width)
        lines.append(f"INTERVIEW {interview_id} - TURN {turn_num}")
        lines.append("─" * self.max_width)
        
        # Turn content
        speaker = turn_data.get("speaker", "Unknown")
        text = turn_data.get("text", "")
        
        lines.append(f"\n[{turn_num}] {speaker}:")
        wrapped = self._wrap_text(text, indent="    ")
        lines.append(wrapped)
        
        # Add enrichment information
        if enrichment.get("themes"):
            themes = enrichment["themes"]
            theme_list = ", ".join(themes) if isinstance(themes, list) else str(themes)
            lines.append(f"\n    📂 Themes: {theme_list}")
        
        if enrichment.get("is_notable_quote") and enrichment.get("quote_context"):
            context = enrichment["quote_context"]
            lines.append(f"\n    💬 Notable quote: {context.get('context', '')}")
            if context.get("tags"):
                tags = ", ".join(context["tags"])
                lines.append(f"    🏷️  Tags: {tags}")
        
        lines.append("\n" + "─" * self.max_width)
        
        return "\n".join(lines)
    
    def _wrap_text(self, text: str, indent: str = "") -> str:
        """Wrap text with proper indentation"""
        if not text:
            return indent
        
        # Set up wrapper with the indent
        self.wrapper.initial_indent = indent
        self.wrapper.subsequent_indent = indent
        
        # Handle multiple paragraphs
        paragraphs = text.split('\n')
        wrapped_paragraphs = []
        
        for para in paragraphs:
            if para.strip():
                wrapped = self.wrapper.fill(para)
                wrapped_paragraphs.append(wrapped)
            else:
                wrapped_paragraphs.append(indent)
        
        return '\n'.join(wrapped_paragraphs)