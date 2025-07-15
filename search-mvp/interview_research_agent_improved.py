# interview_research_agent_improved.py
import json
import os
import sys
import subprocess
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from interview_research_tools import INTERVIEW_RESEARCH_TOOLS
import re

# Load environment variables
load_dotenv()

class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colors and clean formatting"""
    
    grey = "\x1b[38;21m"
    green = "\x1b[32m"
    yellow = "\x1b[33m"
    red = "\x1b[31m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    
    FORMATS = {
        logging.DEBUG: grey + "%(message)s" + reset,
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
    """Simplified, cleaner logging for the research agent"""
    
    def __init__(self, verbose=False, research_mode=False):
        self.logger = logging.getLogger('research_agent')
        self.logger.setLevel(logging.DEBUG if verbose else logging.INFO)
        self.research_mode = research_mode
        
        # Remove existing handlers
        self.logger.handlers.clear()
        
        # Console handler with custom formatting
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(ColoredFormatter())
        self.logger.addHandler(console_handler)
        
        # File handler for detailed logs
        file_handler = logging.FileHandler('logs/agent_session.log')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        ))
        self.logger.addHandler(file_handler)
    
    def iteration_header(self, current, total):
        """Clean iteration header"""
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"🔄 Iteration {current}/{total}")
    
    def thinking(self, message):
        """Log agent's thinking"""
        if message:
            # Clean up the message
            message = message.strip()
            limit = 2000 if self.research_mode else 500
            if len(message) > limit:
                message = message[:limit-3] + "..."
            self.logger.info(f"💭 {message}")
    
    def tool_call(self, tool_name, args):
        """Log tool usage"""
        # Format args nicely
        if args:
            args_str = json.dumps(args, ensure_ascii=False)
            limit = 1000 if self.research_mode else 300
            if len(args_str) > limit:
                args_str = args_str[:limit-3] + "..."
        else:
            args_str = "{}"
        
        self.logger.info(f"🔧 {tool_name}({args_str})")
    
    def tool_result(self, size, preview=None):
        """Log tool result"""
        size_str = self._format_size(size)
        if preview:
            # Clean preview
            preview = preview.strip()
            limit = 2000 if self.research_mode else 400
            if len(preview) > limit:
                preview = preview[:limit-3] + "..."
            self.logger.info(f"   ✅ {size_str} | Preview: {preview}")
        else:
            self.logger.info(f"   ✅ {size_str}")
    
    def scratchpad_entry(self, note):
        """Log scratchpad notes in a special way"""
        # Extract first meaningful line or first paragraph if short
        lines = note.strip().split('\n')
        limit = 1500 if self.research_mode else 300
        
        # Try to get a meaningful excerpt
        if len(lines) == 1:
            # Single line - show up to limit chars
            excerpt = lines[0]
            if len(excerpt) > limit:
                excerpt = excerpt[:limit-3] + "..."
        else:
            # Multiple lines - in research mode, show more content
            if self.research_mode:
                # Show first few lines that fit within limit
                excerpt = ""
                for line in lines:
                    if len(excerpt + line + "\n") <= limit:
                        excerpt += line + "\n"
                    else:
                        break
                excerpt = excerpt.strip()
            else:
                # Normal mode - show first line, or first two if first is short
                first_line = lines[0]
                if len(first_line) < 150 and len(lines) > 1:
                    excerpt = f"{first_line} {lines[1]}"
                else:
                    excerpt = first_line
            
            if len(excerpt) > limit:
                excerpt = excerpt[:limit-3] + "..."
        
        self.logger.info(f"📝 Note: {excerpt}")
    
    def progress(self, message):
        """General progress message"""
        self.logger.info(f"▶️  {message}")
    
    def complete(self, message):
        """Completion message"""
        self.logger.info(f"✨ {message}")
    
    def error(self, message):
        """Error message"""
        self.logger.error(message)
    
    def info(self, message):
        """Standard info message (for compatibility)"""
        self.logger.info(message)
    
    def _format_size(self, size):
        """Format byte size nicely"""
        if size < 1024:
            return f"{size} chars"
        elif size < 1024 * 10:
            return f"{size/1024:.1f}K chars"
        else:
            return f"{size/1024:.0f}K chars"

class InterviewResearchAgent:
    def __init__(self, api_key=None, model="kimi-k2-0711-preview", verbose=False, research_mode=False):
        self.client = OpenAI(
            api_key=api_key or os.getenv("MOONSHOT_API_KEY"),
            base_url="https://api.moonshot.ai/v1"
        )
        self.model = model
        self.tools = INTERVIEW_RESEARCH_TOOLS
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.logger = AgentLogger(verbose=verbose, research_mode=research_mode)
        self.research_mode = research_mode  # Show even more detail for research sessions
        
        # Track some stats
        self.stats = {
            'tool_calls': 0,
            'tokens_used': 0,
            'iterations': 0,
            'start_time': datetime.now()
        }
    
    async def autonomous_research(self, research_question, max_iterations=15):
        """Main research method with improved logging"""
        
        self.logger.progress(f"Starting research: {research_question}")
        
        # Initialize conversation (exactly like kimi_chat)
        final_messages = [{
            "role": "user",
            "content": f"""You are an expert qualitative researcher with access to a corpus of citizen consultation interviews from Uruguay (May 28-29, 2025). These interviews explore citizen perspectives on national and local priorities.

Research Question: {research_question}

Your task is to explore this question thoroughly using the available tools. Follow this research cycle:

📊 PHASE 1: ORIENTATION (Always start here)
- Use `get_corpus_stats()` to understand the corpus size and scope
- Use `list_interview_themes()` to see all themes - this reveals citizen concerns
- Use `search_themes(keyword)` to explore themes related to your question
- Look for patterns, unexpected themes, and research directions

📝 PHASE 2: PLANNING (Use scratchpad to strategize)
After orientation, ALWAYS write a research plan in your scratchpad:
- What patterns did you notice in the themes?
- Which interviews look most relevant? Why?
- What search strategies will you use?
- What evidence would answer the research question?

EXAMPLE PLANNING ENTRY:
"Just reviewed themes - fascinating patterns emerging:
1. Healthcare themes cluster around 'crisis' and 'access' - appears in 071, 084, 091
2. Education themes are overwhelmingly negative ('abandonment', 'exhaustion')
3. Security varies wildly - some interviews prioritize it, others barely mention it

My research plan:
FIRST WAVE - Get overview of key interviews:
- get_interview_turn("071:") - has healthcare_access_crisis theme
- get_interview_turn("084:") - also healthcare, check if urban/rural difference
- get_interview_turn("091:") - third healthcare interview for comparison

SECOND WAVE - Deep dive on specifics:
- search_interviews("lista de espera") - waiting lists seem crucial
- search_interviews("rural") AND search_interviews("urbano") - geographic patterns
- get_interview_turn("071:23-30") - if I find key sections

THIRD WAVE - Cross-cutting themes:
- Look for connections between healthcare and migration
- Check if education issues relate to healthcare worker shortages
- See if security concerns affect healthcare access

This structured approach should reveal both depth and breadth."

🔍 PHASE 3: TARGETED EXPLORATION (Execute your plan)
- Use `get_interview_turn("071:")` to get interview summaries first
- Use `search_interviews("specific term")` for targeted searches
- Use `get_interview_turn("071:23")` for specific quotes
- Track findings in scratchpad as you go

EXAMPLE TOOL CHAINING:
Step 1: get_interview_turn("071:") 
→ Notice mentions waiting times, rural perspective
Step 2: search_interviews("lista de espera")
→ Find 15 mentions across interviews, note which ones
Step 3: get_interview_turn("084:45-50")
→ Extract specific quote about 6-month wait
Step 4: scratchpad_append("Pattern confirmed: waiting times mentioned in 071:23 (3 months), 084:47 (6 months), 089:12 (hasta un año). Rural areas consistently report longer waits.")
Step 5: search_interviews("especialista")
→ Look for specialist access issues
Continue building evidence chains...

🔄 PHASE 4: ITERATION (Refine based on findings)
- Review your scratchpad with `scratchpad_read()`
- Identify gaps or new directions
- Make a new mini-plan and explore further
- Connect findings across interviews

EXAMPLE MID-RESEARCH REPLANNING:
scratchpad_append("CHECKPOINT: After analyzing 5 healthcare interviews, I'm seeing an unexpected pattern - it's not just about wait times, but about healthcare workers leaving rural areas. This wasn't in my original plan but seems crucial.

NEW MINI-PLAN:
1. search_interviews('médicos se van') - doctors leaving
2. search_interviews('falta de personal') - staff shortages  
3. get_interview_turn('068:') - noticed this has 'professional_exhaustion' theme
4. Look for connections to education (are healthcare training programs failing too?)

This pivot might reveal systemic workforce issues across sectors.")

IMPORTANT: Use your scratchpad as a thinking space throughout the research:

The scratchpad is your research journal. Use it to:
- 🔍 OBSERVE: What patterns do you notice? What surprises you?
- 💭 HYPOTHESIZE: What might explain these patterns? What tentative conclusions emerge?
- ❓ QUESTION: What gaps remain? What would you explore next?
- 🔗 CONNECT: How do different findings relate? What threads run through multiple interviews?
- 🤔 REFLECT: What does this mean for the research question? What's most significant?

Write naturally in your scratchpad - think out loud! Include:
- Initial reactions ("Interesting that 3 teachers all mention...")
- Evolving understanding ("Initially thought X, but now seeing Y...")
- Uncertainties ("Not clear whether this is local or national...")
- Surprising findings ("Unexpected: rural areas prioritize education higher...")
- Contradictions ("Interview 071 says X, but 089 suggests opposite...")

ALWAYS include citations (INTERVIEW:TURN format) but write conversationally.

EXAMPLE SCRATCHPAD ENTRIES:

[After seeing theme list]
"First look at education themes - I'm struck by how many are framed negatively: 
'abandonment', 'failures', 'breakdown', 'exhaustion' (see theme list). This isn't 
about education improvements or hopes, but crisis language. Makes me wonder - are 
these interviews capturing a moment of particular stress in the education system? 
Or is this how education is generally discussed?"

[After examining specific turns]
"Looking at turn 072:14 - teacher says 'es cada vez más abrumador' (it's increasingly 
overwhelming). This temporal element is important - not just that it's hard, but 
getting WORSE. Combined with 068:02 where teacher mentions 'la problemática se 
profundizó en el último quinquenio' (problems deepened in last 5 years). 

Pattern emerging: Recent deterioration, not longstanding issues. What happened 5 
years ago? Policy change? Budget cuts? Need to investigate..."

[Noticing patterns]
"Puzzling over education priority rankings - why such variation? 
- Rural areas rank it 1st or 2nd (077:, 080:, 068:)
- Urban/suburban rank it 3rd (070:, 076:, 092:)

Hypothesis: Could this reflect access issues? In rural areas, education might be 
seen as THE pathway out of isolation/poverty, while urban areas have more diverse 
opportunities? Or maybe rural communities see education infrastructure as more 
visibly failing (teacher in 068:151 describes schools where kids 'no saben para 
dónde van a ir' - don't know where they'll go next)."

[Finding contradictions]
"Security perceptions vary WILDLY:
- Interview 071: 'inseguridad es lo principal' (insecurity is the main thing)
- Interview 084: 'acá no hay problema de seguridad' (here there's no security problem)

Geography matters? Small town vs city? Or is it about personal experience - those 
who've been victims vs those who haven't? The woman in 071 mentions specific 
incidents, while 084 speaker talks more abstractly..."

[Connecting themes]
"Starting to see a triangle: EDUCATION-EMPLOYMENT-MIGRATION
- Poor education leads to no local jobs (068:44)
- No jobs leads to youth migration (multiple interviews)  
- Migration weakens schools further (fewer students = less resources)

It's a vicious cycle. Rural teacher (068:89) captures it perfectly: 'los jóvenes 
se van porque no hay oportunidades, pero sin jóvenes no hay futuro para el pueblo' 
(youth leave because there are no opportunities, but without youth there's no future 
for the town)."

[Building to insights]
"After looking at 20+ education-related turns, the word that keeps coming up is 
'abandono' (abandonment). Not just lack of resources, but active abandonment:
- Physical (buildings falling apart)
- Professional (teachers without support)
- Emotional (students feeling forgotten)
- Systemic (policies that ignore rural realities)

This isn't about tweaking budgets - it's about whether the state has essentially 
given up on rural education. Heavy stuff."

Remember: The scratchpad shows your thinking process. Don't just list facts - show 
how you're connecting dots, what surprises you, what patterns emerge. The messier and 
more honest, the better! Your uncertainties and evolving thoughts are valuable.

Your scratchpad will help readers understand not just WHAT you found but HOW you 
found it - the detective work behind the conclusions.

COMPLETE EXAMPLE: TOOL SEQUENCE WITH PLANNING
Research Question: "How do citizens view government response to their needs?"

1. get_corpus_stats() → "35 interviews, 5510 turns"
2. list_interview_themes() → Notice themes like "state_abandonment", "institutional_distrust"
3. scratchpad_append("Initial scan shows strong negative sentiment toward government. Themes include 'state_abandonment' (12 interviews), 'institutional_distrust' (8 interviews), 'bureaucratic_barriers' (15 interviews). Plan: First explore 'state_abandonment' theme to understand specific complaints, then contrast with any positive mentions of government programs.")
4. search_interviews("abandono estado") → 23 results across interviews
5. get_interview_turn("071:34-40") → Specific story about closed rural clinic
6. scratchpad_append("Found concrete example in 071:36 - rural clinic closed 2 years ago, nearest now 50km away. This isn't abstract 'abandonment' but literal withdrawal of services. Pattern emerging: abandonment = service withdrawal, not just neglect.")
7. search_interviews("programa social") → Looking for positive examples
8. get_interview_turn("089:") → Found mention of successful food program
9. scratchpad_append("Interesting contrast! 089 mentions INDA food program positively (089:78). But even here, citizen says 'es lo único que funciona' (it's the only thing that works). Success stories exist but are seen as exceptions proving the rule.")
10. scratchpad_read() → Review findings so far
11. scratchpad_append("NEW DIRECTION: The 'only thing that works' comment suggests citizens might judge government by consistency, not just presence. Need to explore reliability/predictability of services. Adjusting plan to search for mentions of intermittent services or broken promises.")
Continue iterating...

TOOL SELECTION GUIDE:

🗺️ For ORIENTATION:
- `get_corpus_stats()` → Quick corpus overview
- `list_interview_themes()` → See all themes (reveals what citizens talk about)
- `search_themes("education")` → Find themes with specific keywords

📑 For EXPLORATION:
- `get_interview_turn("071:")` → Interview summary (start here for context)
- `search_interviews("term")` → Find specific mentions across all interviews
- `get_interview_turn("071:23")` → Get exact quote and context
- `get_interview_turn("071:20-25")` → See conversation flow

💭 For THINKING:
- `scratchpad_append("note")` → Record observations, plans, connections
- `scratchpad_read()` → Review your research journey

SEARCH TIPS:
- Use Spanish terms when searching (e.g., "salud" not "health")
- Try variations: "educación", "escuela", "maestro", "docente"
- Search for emotion words: "abandono", "crisis", "esperanza"
- Look for specific policies or programs mentioned

Remember: Quality over quantity. It's better to deeply explore 5-6 relevant interviews than to skim 20. Build evidence chains by connecting multiple turns and interviews. When you have sufficient evidence and insights, provide a summary with specific citations."""
        }]
        
        iteration = 0
        tool_call_log = []
        final_response = "Research incomplete - reached maximum iterations or encountered error"
        
        while iteration < max_iterations:
            try:
                self.logger.iteration_header(iteration + 1, max_iterations)
                
                # Make API call with tools
                api_params = {
                    "model": self.model,
                    "messages": final_messages,
                    "temperature": 0.7,
                    "max_tokens": 4096,
                    "tools": [tool["schema"] for tool in self.tools.values()]
                }
                
                response = self.client.chat.completions.create(**api_params)
                message = response.choices[0].message
                
                # Check if agent wants to use tools
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    # Show agent's thinking if provided
                    if message.content:
                        self.logger.thinking(message.content)
                    
                    # Add assistant's message to conversation
                    final_messages.append({
                        "role": "assistant",
                        "content": message.content or "",
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": tc.type,
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            } for tc in message.tool_calls
                        ]
                    })
                    
                    # Execute each tool call
                    for tool_call in message.tool_calls:
                        tool_name = tool_call.function.name
                        tool_args_str = tool_call.function.arguments
                        
                        # Parse arguments
                        try:
                            tool_args = json.loads(tool_args_str) if tool_args_str else {}
                        except json.JSONDecodeError:
                            tool_args = {}
                        
                        self.logger.tool_call(tool_name, tool_args)
                        
                        # Execute tool
                        if tool_name in [schema["schema"]["function"]["name"] for schema in self.tools.values()]:
                            # Find the right tool
                            tool_config = None
                            for tool_key, tool_def in self.tools.items():
                                if tool_def["schema"]["function"]["name"] == tool_name:
                                    tool_config = tool_def
                                    break
                            
                            if tool_config:
                                result = self.execute_cli_tool(tool_name, tool_config["command"], tool_args)
                                
                                # Special handling for scratchpad
                                if tool_name == "scratchpad_append" and "note" in tool_args:
                                    self.logger.scratchpad_entry(tool_args["note"])
                                
                                # In research mode, show extra detail for certain tools
                                if self.research_mode and tool_name == "get_interview_turn":
                                    try:
                                        parsed = json.loads(result)
                                        if parsed.get("type") == "interview_summary":
                                            summary = parsed.get("summary", {}).get("overview", "")
                                            if summary:
                                                self.logger.info(f"   📋 Summary excerpt: {summary[:200]}...")
                                    except:
                                        pass
                            else:
                                result = f"Error: Tool configuration not found for '{tool_name}'"
                        else:
                            result = f"Error: Unknown tool '{tool_name}'"
                        
                        # Extract preview for certain tools
                        preview = None
                        if tool_name in ["search_interviews", "search_themes", "list_interview_themes"]:
                            # Try to extract meaningful content from JSON results
                            try:
                                parsed = json.loads(result)
                                
                                if tool_name == "search_interviews" and "results" in parsed:
                                    # For search results, show first few matches
                                    results = parsed["results"][:3]  # First 3 results
                                    previews = []
                                    for r in results:
                                        if r.get("type") == "theme_match":
                                            previews.append(f"Theme: {r.get('theme', '')}")
                                        elif r.get("type") == "turn_text_match":
                                            text = r.get("text", "")[:100]
                                            previews.append(f"Text: {text}")
                                        elif r.get("type") == "tag_match":
                                            previews.append(f"Tag: {r.get('tag', '')}")
                                    preview = " | ".join(previews)
                                
                                elif tool_name == "list_interview_themes" and "themes" in parsed:
                                    # Show a few theme names
                                    themes = list(parsed["themes"].keys())[:4]
                                    preview = f"Themes: {', '.join(themes)}"
                                
                                elif tool_name == "search_themes":
                                    # Show matching theme names
                                    if "matching_themes" in parsed:
                                        themes = list(parsed["matching_themes"].keys())[:3]
                                        preview = f"Found themes: {', '.join(themes)}"
                                
                            except (json.JSONDecodeError, KeyError):
                                # Fallback to simple line extraction
                                lines = result.strip().split('\n')
                                for line in lines:
                                    if line.strip() and not line.startswith('Found') and not line.startswith('Searching'):
                                        preview = line.strip()
                                        break
                        
                        self.logger.tool_result(len(result), preview)
                        
                        # Add tool result to conversation
                        final_messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result
                        })
                        
                        # Log tool call
                        tool_call_log.append({
                            "tool": tool_name,
                            "args": tool_args,
                            "result_length": len(result),
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        self.stats['tool_calls'] += 1
                    
                    iteration += 1
                    self.stats['iterations'] = iteration
                    continue
                    
                else:
                    # No tools used - agent is done
                    self.logger.complete("Research exploration complete")
                    final_response = message.content
                    break
                    
            except Exception as e:
                self.logger.error(f"Error in iteration {iteration + 1}: {str(e)}")
                break
        
        # Generate summary if needed
        if tool_call_log and (not final_response or final_response == "Research incomplete - reached maximum iterations or encountered error"):
            self.logger.progress(f"Generating comprehensive summary from {len(tool_call_log)} research actions...")
            
            try:
                # Read the scratchpad contents
                from src.tools.scratchpad_tools import read_notes
                scratchpad_content = read_notes(self.session_id)
                
                summary_prompt = f"""
You have explored the research question through {len(tool_call_log)} tool calls across {iteration} iterations. 

YOUR RESEARCH JOURNEY (from scratchpad):
{scratchpad_content}

Review your thinking process above. Notice how your understanding evolved, what questions emerged, and what patterns became clear.

Now synthesize your exploration into a research summary that balances structured data for parsing with narrative interpretation. Let your evolving insights inform the narrative.

# STRUCTURED FINDINGS

## Key_Findings
[List 3-5 major findings with citations]

Finding_1:
- Statement: [Clear claim]
- Evidence: [Supporting evidence with citations like `071:23`, `084:145`]
- Significance: [Why this matters]

Finding_2:
- Statement: [Clear claim]  
- Evidence: [Supporting evidence with citations]
- Significance: [Why this matters]

## Themes_Identified
[Major themes with example quotes]

Theme_1: [Theme name]
- Description: [What this theme encompasses]
- Example: "Direct quote from interview" (`071:23`)
- Frequency: [How often it appeared]

## Citation_Index
[Group citations by topic for easy reference]
- Healthcare access: `071:23`, `072:45`, `084:12`
- Rural challenges: `069:34`, `078:56`, `091:78`
- [Continue grouping]

# INTERPRETIVE ANALYSIS

## Narrative Summary
[2-3 paragraphs of free-form analysis with embedded citations. For example: "The recurring frustration with healthcare waiting times (`071:23`, `084:145`) connects to broader themes of rural isolation (`069:34`). Citizens repeatedly express..." Use citations naturally throughout your narrative to ground every interpretive claim in specific evidence.

BAD: "Many citizens are concerned about security" 
GOOD: "Citizens across multiple interviews express security concerns (`071:12`, `072:34`, `073:45`, `078:23`)"

BAD: "Rural communities face unique challenges"
GOOD: "Rural communities face unique challenges including transport barriers (`069:34`, `078:56`), healthcare access (`071:23`, `084:145`), and limited educational resources (`072:91`, `091:45`)"]

## Patterns and Connections
[Discuss relationships between findings with citations. For instance: "The teacher's observation about student hunger (`072:89`) directly relates to parent concerns about economic pressure (`073:45`). This pattern appears across multiple interviews (`069:12`, `078:34`, `091:56`)..." Every connection should reference specific turns.

BAD: "There seems to be a connection between poverty and education"
GOOD: "The connection between economic hardship and educational challenges appears in teacher testimonies about hungry students (`072:89`), parent concerns about school supplies (`073:45`, `084:67`), and administrator budget discussions (`091:23`)"]

## Research Reflection
[Brief reflection on the research process, including what search strategies revealed surprising connections. Even methodological observations should reference examples: "Searching for 'transport' unexpectedly revealed healthcare access issues (`071:45`, `084:23`)..."]

# TECHNICAL NOTES

Coverage:
- Interviews analyzed: [number/list]
- Search queries used: [list key searches]
- Limitations: [what wasn't fully explored]

CITATION REQUIREMENTS:
- Format: `INTERVIEW:TURN` (e.g., `071:23`) for specific quotes
- Format: `INTERVIEW:` (e.g., `071:`) to reference entire conversations
- EVERY SINGLE CLAIM must have citations - no exceptions
- Use citations in EVERY section, including interpretive analysis
- Embed citations naturally in narrative text"""
                
                final_messages.append({
                    "role": "user",
                    "content": summary_prompt
                })
                
                # Get final summary
                summary_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=final_messages,
                    temperature=0.7,
                    max_tokens=4096
                )
                
                final_response = summary_response.choices[0].message.content
                
            except Exception as e:
                self.logger.error(f"Error generating summary: {str(e)}")
                final_response = f"Error generating summary: {str(e)}"
        
        # Show final stats
        duration = datetime.now() - self.stats['start_time']
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"📊 Research Statistics:")
        self.logger.info(f"   • Duration: {duration.seconds}s")
        self.logger.info(f"   • Iterations: {self.stats['iterations']}")
        self.logger.info(f"   • Tool calls: {self.stats['tool_calls']}")
        self.logger.info(f"   • Session ID: {self.session_id}")
        self.logger.info(f"{'='*60}\n")
        
        # Prepare stats for JSON serialization
        serializable_stats = self.stats.copy()
        if 'start_time' in serializable_stats:
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
            "tool_calls": tool_call_log,
            "iterations": iteration,
            "session_id": self.session_id,
            "stats": serializable_stats,
            "scratchpad": scratchpad_content,
            "full_conversation": final_messages
        }
    
    def execute_cli_tool(self, tool_name, command_template, arguments):
        """Execute a CLI tool with the given arguments"""
        
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
                session_id = arguments.get("session_id", self.session_id)  # Use agent's session_id as default
                full_command = f'python -c "import base64; from src.tools.scratchpad_tools import append_note; print(append_note(base64.b64decode(\'{note_b64}\').decode(), \'{session_id}\'))"'
            else:
                # For scratchpad_read, always use agent's session_id
                session_id = arguments.get("session_id", self.session_id)
                full_command = f'python -c "from src.tools.scratchpad_tools import read_notes; print(read_notes(\'{session_id}\'))"'
        else:
            full_command = command
        
        # Execute command
        try:
            result = subprocess.run(
                full_command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            if result.returncode != 0:
                error_output = result.stderr.strip() if result.stderr else "No error output"
                return f"Command failed with error: {error_output}"
            
            return result.stdout.strip() if result.stdout else "Command completed with no output"
            
        except Exception as e:
            return f"Failed to execute command: {str(e)}"

async def main():
    """Main entry point for the research agent"""
    
    # Check for API key
    api_key = os.getenv("MOONSHOT_API_KEY")
    if not api_key:
        print("❌ Error: MOONSHOT_API_KEY not found in environment variables")
        print("Please set your Moonshot API key:")
        print("  export MOONSHOT_API_KEY='your-key-here'")
        return
    
    # Print welcome message
    print("🔬 Uruguay Interview Research Agent")
    print("=" * 60)
    print("Model: Kimi K2")
    print("Corpus: 35 citizen consultation interviews")
    print("=" * 60)
    
    # Check for flags
    research_mode = "--research" in sys.argv
    if research_mode:
        sys.argv.remove("--research")
        print("🔬 Research mode enabled: Extra detailed logging + complete scratchpad display")
    
    # Get research question
    if len(sys.argv) > 1:
        research_question = " ".join(sys.argv[1:])
    else:
        research_question = input("\n📝 Enter your research question: ")
    
    if not research_question.strip():
        print("❌ Error: Please provide a research question")
        return
    
    print(f"\n🎯 Research Question: {research_question}")
    print("=" * 60)
    
    # Create agent and run research
    agent = InterviewResearchAgent(api_key=api_key, verbose=True, research_mode=research_mode)
    
    try:
        results = await agent.autonomous_research(research_question, max_iterations=30)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"results/research_results_{timestamp}.json"
        
        # Ensure results directory exists
        os.makedirs("results", exist_ok=True)
        
        # Save JSON results
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
        except TypeError as e:
            print(f"⚠️  Warning: Could not serialize results to JSON: {e}")
            print("💾 Saving simplified results...")
            # Save a simplified version
            simplified_results = {
                "final_response": results["final_response"],
                "session_id": results["session_id"],
                "iterations": results["iterations"],
                "tool_calls_count": len(results["tool_calls"]),
                "timestamp": datetime.now().isoformat(),
                "error": f"Full results not serializable: {str(e)}"
            }
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(simplified_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Results saved to: {output_file}")
        
        # Also save markdown summary
        summary_file = f"results/research_summary_{timestamp}.md"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"# Research Summary: {research_question}\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Session ID: {results['session_id']}\n")
            f.write(f"Duration: {results['stats'].get('iterations', 0)} iterations, {results['stats'].get('tool_calls', 0)} tool calls\n\n")
            
            # Include scratchpad in research mode
            if research_mode and results.get('scratchpad'):
                f.write("## Research Process\n\n")
                f.write("*Agent's thinking process throughout the research:*\n\n")
                f.write("```\n")
                f.write(results['scratchpad'])
                f.write("\n```\n\n")
                f.write("---\n\n")
            
            f.write("## Research Summary\n\n")
            f.write(results['final_response'])
        
        print(f"📄 Summary saved to: {summary_file}")
        
        # Print scratchpad first if in research mode
        if research_mode:
            try:
                from src.tools.scratchpad_tools import read_notes
                scratchpad_content = read_notes(agent.session_id)
                if scratchpad_content and scratchpad_content.strip():
                    print("\n" + "="*60)
                    print("🗒️  RESEARCH SCRATCHPAD")
                    print("="*60)
                    print("Agent's thinking process throughout the research:")
                    print("-" * 60)
                    print(scratchpad_content)
                    print("-" * 60)
            except Exception as e:
                print(f"⚠️  Could not read scratchpad: {e}")
        
        # Print summary
        print("\n" + "="*60)
        print("📊 RESEARCH SUMMARY")
        print("="*60)
        print(results['final_response'])
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Research interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during research: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())