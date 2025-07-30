"""Report generation for the research agent"""

import json
from typing import List, Dict, Any
from .prompts import get_citation_style_guide, get_report_template


class ReportGenerator:
    """Handles report generation and formatting"""
    
    def __init__(self, logger=None, max_width=80):
        self.logger = logger
        self.max_width = max_width
    
    def build_summary_prompt(
        self, 
        research_question: str,
        tool_call_log: List[Dict[str, Any]],
        scratchpad_content: str,
        iteration_count: int
    ) -> str:
        """Build the prompt for summary generation"""
        
        # Build tool call summary
        tool_call_summary = []
        for tc in tool_call_log:
            args_str = json.dumps(tc['args'], ensure_ascii=False)
            if len(args_str) > 100:
                tool_call_summary.append(f"- {tc['tool']}({args_str[:100]}...)")
            else:
                tool_call_summary.append(f"- {tc['tool']}({args_str})")
        tool_calls_text = '\n'.join(tool_call_summary)
        
        summary_prompt = f"""
You have explored the research question through {len(tool_call_log)} tool calls across {iteration_count} iterations. 

IMPORTANT INSTRUCTIONS:
1. You MUST use the UN-style report format shown below
2. DO NOT use any other format (e.g., "STRUCTURED FINDINGS", simple lists, or custom formats)
3. Follow the section structure EXACTLY as provided
4. Include extensive citations as specified

CRITICAL ANTI-HALLUCINATION GUIDELINES:
- ONLY report findings that appear in your tool results or scratchpad notes
- If you lack data for a section, explicitly state: "Limited data available on [topic]"
- Use phrases like "Based on available interviews..." or "From the {len(tool_call_log)} interviews examined..."
- Never extrapolate beyond what citizens actually said
- If research was incomplete, acknowledge it: "Further research needed to understand..."
- Distinguish between strong patterns (many interviews) and isolated mentions (1-2 interviews)

HELPFUL PATTERNS FOR HONEST REPORTING:
✓ "Among the X interviews examined, Y citizens expressed..."
✓ "While this research captured perspectives on A and B, data on C was limited"
✓ "The available evidence suggests... though broader consultation would be needed to confirm"
✗ Avoid: Making claims without citations
✗ Avoid: Generalizing from limited data
✗ Avoid: Filling gaps with plausible-sounding content

YOUR RESEARCH JOURNEY (from scratchpad):
{scratchpad_content}

TOOLS USED:
You made {len(tool_call_log)} tool calls during your research:
{tool_calls_text}

Review your thinking process above. Notice how your understanding evolved, what questions emerged, and what patterns became clear.

Now synthesize your exploration into a comprehensive research report following UN documentation standards.

{get_citation_style_guide()}

{get_report_template()}"""
        
        return summary_prompt
    
    def format_sub_agent_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Format sub-agent results for the parent agent"""
        # Extract tool usage summary
        tool_calls = results.get("tool_calls", [])
        tool_summary = {}
        for call in tool_calls:
            tool_name = call.get("tool", "unknown")
            tool_summary[tool_name] = tool_summary.get(tool_name, 0) + 1
        
        # Determine what the sub-agent primarily did
        actions = []
        if "search_interviews" in tool_summary:
            actions.append(f"searched {tool_summary['search_interviews']}x")
        if "get_interview_turn" in tool_summary:
            actions.append(f"examined {tool_summary['get_interview_turn']} turns")
        if "list_interview_themes" in tool_summary:
            actions.append(f"analyzed themes")
        if "search_themes" in tool_summary:
            actions.append(f"explored themes {tool_summary['search_themes']}x")
        
        action_summary = ", ".join(actions) if actions else "conducted research"
        
        # Simplify results for parent agent
        return {
            "final_response": results.get("final_response", ""),
            "iterations": results.get("iterations", 0),
            "tool_calls_count": len(tool_calls),
            "tool_summary": tool_summary,
            "action_summary": action_summary,
            "key_findings": results.get("scratchpad", ""),
            "stats": results.get("stats", {})
        }
    
    def extract_sources(self, text: str) -> List[Dict[str, str]]:
        """Extract citation sources from text"""
        import re
        # Look for patterns like [[064:23]] or [[071:summary]]
        pattern = r'\[\[(\d{3}):(\w+)\]\]'
        matches = re.findall(pattern, text)
        
        sources = []
        for interview_id, turn_id in matches:
            sources.append({
                "interview": interview_id,
                "turn": turn_id,
                "reference": f"{interview_id}:{turn_id}"
            })
        
        return sources