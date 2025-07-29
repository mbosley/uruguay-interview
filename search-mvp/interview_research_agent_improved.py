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
import time

# Load environment variables
load_dotenv()

# Import provider configuration
try:
    from config.providers import get_provider_config, PROVIDERS
except ImportError:
    # Fallback if providers.py doesn't exist yet
    from dataclasses import dataclass
    @dataclass
    class ProviderConfig:
        name: str
        base_url: str
        api_key_env: str
        model_name: str
        description: str
    
    def get_provider_config(provider_name=None):
        return ProviderConfig(
            name="moonshot",
            base_url="https://api.moonshot.ai/v1",
            api_key_env="MOONSHOT_API_KEY",
            model_name="kimi-k2-0711-preview",
            description="Moonshot AI hosting"
        )

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
        
        # Console handler with custom formatting - only add if verbose
        if verbose:
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
    def __init__(self, api_key=None, model=None, verbose=False, research_mode=False, 
                 depth=0, max_depth=3, parent_session_id=None, is_sub_agent=False, provider=None,
                 event_callback=None):
        
        # Get provider configuration
        self.provider_config = get_provider_config(provider)
        self.event_callback = event_callback
        
        # Set up API client
        api_key = api_key or os.getenv(self.provider_config.api_key_env)
        if not api_key:
            raise ValueError(f"{self.provider_config.api_key_env} not found. "
                           f"Please set: export {self.provider_config.api_key_env}='your-key-here'")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=self.provider_config.base_url
        )
        
        # Use provider's model name unless explicitly overridden
        self.model = model or self.provider_config.model_name
        
        # Log provider info for root agents
        if verbose and not is_sub_agent:
            speed_info = f" ({self.provider_config.tokens_per_second} tok/s)" if hasattr(self.provider_config, 'tokens_per_second') and self.provider_config.tokens_per_second else ""
            print(f"🚀 Using {self.provider_config.name}: {self.provider_config.description}{speed_info}")
        self.tools = INTERVIEW_RESEARCH_TOOLS
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.logger = AgentLogger(verbose=verbose, research_mode=research_mode)
        self.research_mode = research_mode  # Show even more detail for research sessions
        
        # Hierarchy tracking for recursive agents
        self.depth = depth
        self.max_depth = max_depth
        self.parent_session_id = parent_session_id
        self.is_sub_agent = is_sub_agent
        
        # Track some stats
        self.stats = {
            'tool_calls': 0,
            'tokens_used': 0,
            'iterations': 0,
            'start_time': datetime.now(),
            'depth': depth,
            'sub_agents_spawned': 0,
            'input_tokens': 0,
            'output_tokens': 0,
            'total_cost': 0.0
        }
    
    async def emit_event(self, event_type: str, data: dict, iteration: int = None):
        """Emit event to callback if available"""
        if self.event_callback:
            event = {
                "type": event_type,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
            if iteration is not None:
                event["iteration"] = iteration
            await self.event_callback(event)
    
    def _extract_sources(self, text: str) -> list:
        """Extract interview references from text"""
        import re
        # Look for patterns like "Interview 023" or "interview 071"
        pattern = r'[Ii]nterview\s+(\d{3})'
        matches = re.findall(pattern, text)
        # Return unique sorted list
        return sorted(list(set([f"Interview {id}" for id in matches])))[:10]
    
    async def autonomous_research(self, research_question, max_iterations=15):
        """Main research method with improved logging"""
        
        if not self.is_sub_agent:
            self.logger.progress(f"Starting research: {research_question}")
        
        # Initialize conversation (exactly like kimi_chat)
        # Add context about agent hierarchy if this is a sub-agent
        hierarchy_context = ""
        if self.depth > 0:
            hierarchy_context = f"\nYou are a specialized sub-agent at depth level {self.depth} (max depth: {self.max_depth}). "
            if self.depth >= self.max_depth:
                hierarchy_context += "You CANNOT spawn further sub-agents as you are at maximum depth. Focus on direct investigation."
            else:
                hierarchy_context += f"You can spawn sub-agents if needed (remaining depth: {self.max_depth - self.depth})."
        
        final_messages = [{
            "role": "user",
            "content": f"""You are an expert qualitative researcher with access to a corpus of citizen consultation interviews from Uruguay (May 28-29, 2025). These interviews explore citizen perspectives on national and local priorities.{hierarchy_context}

Research Question: {research_question}

Your task is to explore this question thoroughly using the available tools. 

IMPORTANT: 
- If the research question contains specific instructions about which tools to use (e.g., "use spawn_sub_agent", "just run get_corpus_stats"), follow those instructions directly without going through all phases.
- For testing scenarios or when explicitly asked to demonstrate a tool, skip the full research cycle.
- Otherwise, use this recommended research cycle for thorough research:

📊 PHASE 1: ORIENTATION (Start here for general research)
- Use `get_corpus_stats()` to understand the corpus size and scope
- Use `list_interview_themes()` to see all themes - this reveals citizen concerns
- Use `search_themes(keyword)` to explore themes related to your question
- Look for patterns, unexpected themes, and research directions

📝 PHASE 2: PLANNING (Use scratchpad to strategize)
After orientation, write a research plan in your scratchpad:
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

🚀 DELEGATION STRATEGY (For Complex Research):
When your research reveals multiple complex threads or the scope is too large for thorough exploration:

WHEN TO DELEGATE:
- You discover 3+ distinct sub-themes each needing deep investigation
- A theme appears across many interviews requiring specialized analysis
- You need parallel exploration of contrasting perspectives (urban vs rural)
- Time/iteration limits prevent you from exploring all important aspects

HOW TO DELEGATE EFFECTIVELY:
1. First complete orientation phase to understand the landscape
2. Identify specific, focused questions for sub-agents
3. Provide context about what you've discovered and why delegation is needed
4. Sub-agents will conduct independent research and return findings

EXAMPLE DELEGATION PATTERN:
After discovering education crisis has multiple dimensions:
- spawn_sub_agent("Analyze teacher retention and burnout in rural schools", "Found 'professional_exhaustion' theme in interviews 068, 072, 089. Need deep dive into teacher perspectives and support systems.")
- spawn_sub_agent("Investigate student dropout patterns and family economic pressures", "Multiple interviews mention students leaving for work. See interviews 071, 084, 091.")
- spawn_sub_agent("Examine infrastructure and resource allocation in education", "Physical abandonment theme appears frequently. Focus on interviews mentioning building conditions, materials.")

Sub-agents will return structured findings that you can synthesize into your final analysis.

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

🚀 For DELEGATION (when scope is large):
- `spawn_sub_agent("focused question", "context")` → Delegate deep exploration
- Use when: Multiple themes need investigation, complex topic requires specialization
- Example: After finding healthcare crisis across regions, delegate: "Analyze rural vs urban healthcare experiences"

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
                
                # Emit iteration start event
                await self.emit_event("iteration_start", {
                    "current": iteration + 1,
                    "max": max_iterations
                }, iteration + 1)
                
                # Make API call with tools
                api_params = {
                    "model": self.model,
                    "messages": final_messages,
                    "temperature": 0.7,
                    "max_tokens": 4096,
                    "tools": [tool["schema"] for tool in self.tools.values()]
                }
                
                # Debug: Log API call details
                if self.research_mode and self.provider_config.name == "groq":
                    self.logger.info(f"   🔍 API Call: iteration={iteration}, model={self.model}, provider={self.provider_config.name}")
                    self.logger.info(f"   🔑 API Key: {self.client.api_key[:10]}...{self.client.api_key[-4:]}")
                    self.logger.info(f"   📝 Messages: {len(final_messages)} messages, last role: {final_messages[-1]['role'] if final_messages else 'none'}")
                
                response = self.client.chat.completions.create(**api_params)
                message = response.choices[0].message
                
                # Track token usage and costs
                if hasattr(response, 'usage'):
                    self.stats['input_tokens'] += response.usage.prompt_tokens
                    self.stats['output_tokens'] += response.usage.completion_tokens
                    
                    # Calculate cost based on provider
                    if self.provider_config.cost_per_1k_input and self.provider_config.cost_per_1k_output:
                        input_cost = (response.usage.prompt_tokens / 1000) * self.provider_config.cost_per_1k_input
                        output_cost = (response.usage.completion_tokens / 1000) * self.provider_config.cost_per_1k_output
                        iteration_cost = input_cost + output_cost
                        self.stats['total_cost'] += iteration_cost
                        
                        # Log cost in research mode
                        if self.research_mode and not self.is_sub_agent:
                            self.logger.info(f"   💰 Iteration cost: ${iteration_cost:.6f} ({response.usage.total_tokens} tokens)")
                
                # Check if agent wants to use tools
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    # Show agent's thinking if provided
                    if message.content:
                        self.logger.thinking(message.content)
                        # Emit thinking event
                        await self.emit_event("thinking", {
                            "content": message.content
                        }, iteration + 1)
                    
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
                    
                    # Separate spawn_sub_agent calls from other tools
                    spawn_calls = []
                    other_calls = []
                    
                    for tool_call in message.tool_calls:
                        tool_name = tool_call.function.name
                        if tool_name == "spawn_sub_agent":
                            spawn_calls.append(tool_call)
                        else:
                            other_calls.append(tool_call)
                    
                    # Execute non-spawn tools sequentially first
                    for tool_call in other_calls:
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
                        }, iteration + 1)
                        
                        # Execute tool
                        if tool_name in [schema["schema"]["function"]["name"] for schema in self.tools.values()]:
                            # Find the right tool
                            tool_config = None
                            for tool_key, tool_def in self.tools.items():
                                if tool_def["schema"]["function"]["name"] == tool_name:
                                    tool_config = tool_def
                                    break
                            
                            if tool_config:
                                result = await self.execute_cli_tool(tool_name, tool_config["command"], tool_args)
                                
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
                        
                        # Emit tool_result event
                        await self.emit_event("tool_result", {
                            "tool": tool_name,
                            "metadata": {
                                "size": len(result),
                                "preview": preview or result[:200] + "..." if len(result) > 200 else result
                            }
                        }, iteration + 1)
                        
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
                            "result": result,  # Include the actual result
                            "result_length": len(result),
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        self.stats['tool_calls'] += 1
                    
                    # Execute spawn_sub_agent calls in parallel
                    if spawn_calls:
                        self.logger.info(f"🚀 Executing {len(spawn_calls)} sub-agents in parallel...")
                        # Show what each sub-agent will research
                        for i, tool_call in enumerate(spawn_calls, 1):
                            try:
                                args = json.loads(tool_call.function.arguments)
                                question = args.get('question', 'Unknown')
                                self.logger.info(f"   {i}. {question[:100]}...")
                            except:
                                pass
                        
                        start_time = time.time()
                        
                        # Prepare tasks for parallel async execution
                        spawn_tasks = []
                        task_metadata = []
                        
                        for tool_call in spawn_calls:
                            tool_name = tool_call.function.name
                            tool_args_str = tool_call.function.arguments
                            
                            # Parse arguments
                            try:
                                tool_args = json.loads(tool_args_str) if tool_args_str else {}
                            except json.JSONDecodeError:
                                tool_args = {}
                            
                            # Find tool config
                            tool_config = None
                            for tool_key, tool_def in self.tools.items():
                                if tool_def["schema"]["function"]["name"] == tool_name:
                                    tool_config = tool_def
                                    break
                            
                            if tool_config:
                                self.logger.tool_call(tool_name, tool_args)
                                
                                # Emit tool_call event
                                await self.emit_event("tool_call", {
                                    "tool": tool_name,
                                    "args": tool_args,
                                    "id": tool_call.id
                                }, iteration + 1)
                                
                                # Create async task
                                task = self.execute_cli_tool(
                                    tool_name,
                                    tool_config["command"],
                                    tool_args
                                )
                                spawn_tasks.append(task)
                                task_metadata.append((tool_call, tool_args))
                        
                        # Execute all spawn tasks in parallel
                        results = await asyncio.gather(*spawn_tasks, return_exceptions=True)
                        
                        # Process results
                        for i, result in enumerate(results):
                            tool_call, tool_args = task_metadata[i]
                            
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
                                
                                self.stats['tool_calls'] += 1
                            else:
                                # Parse sub-agent result for better logging
                                try:
                                    parsed_result = json.loads(result)
                                    if isinstance(parsed_result, dict):
                                        # Extract key information from sub-agent response
                                        summary = parsed_result.get('final_response', '')[:200] + '...'
                                        tool_calls = parsed_result.get('tool_calls_count', 0)
                                        iterations = parsed_result.get('iterations', 0)
                                        action_summary = parsed_result.get('action_summary', 'conducted research')
                                        
                                        preview = f"✓ {iterations} iterations, {tool_calls} tool calls"
                                        self.logger.info(f"   🔍 Sub-agent {action_summary}")
                                        self.logger.info(f"   📊 Key finding: {summary[:150]}...")
                                        
                                        # Show tool usage breakdown if available
                                        if 'tool_summary' in parsed_result:
                                            tools_used = ', '.join([f"{t}({c})" for t, c in parsed_result['tool_summary'].items()])
                                            self.logger.info(f"   🔧 Tools used: {tools_used}")
                                        
                                        # Aggregate sub-agent costs
                                        if 'stats' in parsed_result and 'total_cost' in parsed_result['stats']:
                                            sub_cost = parsed_result['stats']['total_cost']
                                            self.stats['total_cost'] += sub_cost
                                            if sub_cost > 0:
                                                self.logger.info(f"   💰 Sub-agent cost: ${sub_cost:.6f}")
                                    else:
                                        preview = "Sub-agent completed"
                                except json.JSONDecodeError:
                                    preview = "Sub-agent completed (non-JSON response)"
                                
                                self.logger.tool_result(len(result), preview)
                                
                                # Emit tool_result event
                                await self.emit_event("tool_result", {
                                    "tool": "spawn_sub_agent",
                                    "metadata": {
                                        "size": len(result),
                                        "preview": preview
                                    }
                                }, iteration + 1)
                                
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
                                
                                self.stats['tool_calls'] += 1
                        
                        elapsed = time.time() - start_time
                        self.logger.info(f"✅ All sub-agents completed in {elapsed:.1f}s (parallel execution)")
                    
                    iteration += 1
                    self.stats['iterations'] = iteration
                    
                    # Add small delay for Groq to avoid rate limiting
                    if self.provider_config.name == "groq" and iteration < max_iterations:
                        await asyncio.sleep(0.5)
                    
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
                
                # Track summary generation costs
                if hasattr(summary_response, 'usage'):
                    self.stats['input_tokens'] += summary_response.usage.prompt_tokens
                    self.stats['output_tokens'] += summary_response.usage.completion_tokens
                    
                    if self.provider_config.cost_per_1k_input and self.provider_config.cost_per_1k_output:
                        input_cost = (summary_response.usage.prompt_tokens / 1000) * self.provider_config.cost_per_1k_input
                        output_cost = (summary_response.usage.completion_tokens / 1000) * self.provider_config.cost_per_1k_output
                        summary_cost = input_cost + output_cost
                        self.stats['total_cost'] += summary_cost
                
                final_response = summary_response.choices[0].message.content
                
            except Exception as e:
                self.logger.error(f"Error generating summary: {str(e)}")
                final_response = f"Error generating summary: {str(e)}"
        
        # Emit final response events
        await self.emit_event("response_start", {})
        await self.emit_event("response_end", {
            "response": final_response,
            "sources": self._extract_sources(final_response)
        })
        
        # Emit stats
        duration = (datetime.now() - self.stats['start_time']).total_seconds()
        await self.emit_event("stats", {
            "duration": duration,
            "iterations": self.stats['iterations'], 
            "toolCalls": self.stats['tool_calls'],
            "llmCalls": iteration + 1,
            "inputTokens": self.stats['input_tokens'],
            "outputTokens": self.stats['output_tokens'],
            "totalCost": self.stats['total_cost']
        })
        
        # Show final stats (only for root agents)
        if not self.is_sub_agent:
            duration = datetime.now() - self.stats['start_time']
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"📊 Research Statistics:")
            self.logger.info(f"   • Duration: {duration.seconds}s")
            self.logger.info(f"   • Iterations: {self.stats['iterations']}")
            self.logger.info(f"   • Tool calls: {self.stats['tool_calls']}")
            
            # Show token usage and costs
            if self.stats['input_tokens'] > 0:
                total_tokens = self.stats['input_tokens'] + self.stats['output_tokens']
                self.logger.info(f"   • Tokens: {total_tokens:,} (in: {self.stats['input_tokens']:,}, out: {self.stats['output_tokens']:,})")
                
                # Show cost if applicable
                if self.stats['total_cost'] > 0:
                    self.logger.info(f"   • Cost: ${self.stats['total_cost']:.4f} ({self.provider_config.name})")
                else:
                    self.logger.info(f"   • Cost: Free ({self.provider_config.name})")
            
            # Show sub-agent spawns if any
            if self.stats['sub_agents_spawned'] > 0:
                self.logger.info(f"   • Sub-agents: {self.stats['sub_agents_spawned']}")
                
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
    
    async def execute_cli_tool(self, tool_name, command_template, arguments):
        """Execute a CLI tool with the given arguments"""
        
        # Special handling for spawn_sub_agent first
        if tool_name == "spawn_sub_agent":
            # Check depth limit
            if self.depth >= self.max_depth:
                return json.dumps({"error": f"Cannot spawn sub-agent: already at maximum depth ({self.max_depth})"})
            
            # Get parameters
            question = arguments.get("question", "")
            context = arguments.get("context", "")
            max_iterations = arguments.get("max_iterations", 10)
            
            # Build command directly
            command = command_template
            command = command.replace("{depth}", str(self.depth + 1))
            command = command.replace("{parent_id}", self.session_id)
            command = command.replace("{max_depth}", str(self.max_depth))
            command = command.replace("{question}", question)
            
            # Add provider flag to pass down to sub-agent
            command += f" --provider={self.provider_config.name}"
            
            self.stats['sub_agents_spawned'] += 1
            self.logger.info(f"🚀 Delegating to sub-agent (depth {self.depth + 1}):")
            self.logger.info(f"   📝 Question: {question[:150]}...")
            self.logger.info(f"   🎯 Context: {context[:100]}..." if context else "   🎯 No context provided")
            self.logger.info(f"   ⚙️  Max iterations: {max_iterations}")
            
            full_command = command
            
        else:
            # Normal placeholder replacement for other tools
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
            # Use longer timeout for sub-agents
            # With Groq's speed, even complex research should complete in 2-3 minutes
            timeout = 180 if tool_name == "spawn_sub_agent" else 30
            
            # Use asyncio subprocess to avoid blocking the event loop
            process = await asyncio.create_subprocess_shell(
                full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                
                if process.returncode != 0:
                    error_output = stderr.decode().strip() if stderr else "No error output"
                    return f"Command failed with error: {error_output}"
                
                return stdout.decode().strip() if stdout else "Command completed with no output"
            
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise subprocess.TimeoutExpired(full_command, timeout)
            
        except subprocess.TimeoutExpired:
            return json.dumps({
                "error": f"Sub-agent timed out after {timeout} seconds",
                "partial_output": "Sub-agent may still be running. Consider reducing max_iterations or simplifying the research question."
            })
        except Exception as e:
            return f"Failed to execute command: {str(e)}"

async def main():
    """Main entry point for the research agent"""
    
    # Check for sub-agent mode early
    is_sub_agent = "--sub-agent" in sys.argv
    
    # Parse provider from command line or environment
    provider = None
    for arg in sys.argv:
        if arg.startswith("--provider="):
            provider = arg.split("=")[1]
            sys.argv.remove(arg)
            break
    
    # Get provider config (will auto-detect if not specified)
    try:
        provider_config = get_provider_config(provider)
        api_key = os.getenv(provider_config.api_key_env)
        
        if not api_key:
            print(f"❌ Error: {provider_config.api_key_env} not found")
            print(f"Please set: export {provider_config.api_key_env}='your-key-here'")
            if provider_config.name == "groq":
                print("  Get your key at: https://console.groq.com/")
            elif provider_config.name == "moonshot":
                print("  Get your key at: https://platform.moonshot.cn/")
            return
    except Exception as e:
        print(f"❌ Error configuring provider: {e}")
        return
    
    # Print welcome message (only for root agents)
    if not is_sub_agent:
        print("🔬 Uruguay Interview Research Agent")
        print("=" * 60)
        print(f"Provider: {provider_config.description}")
        print(f"Model: {provider_config.model_name}")
        if hasattr(provider_config, 'tokens_per_second') and provider_config.tokens_per_second:
            print(f"Speed: {provider_config.tokens_per_second} tokens/sec")
        print("Corpus: 35 citizen consultation interviews")
        print("=" * 60)
    
    # Check for flags
    research_mode = "--research" in sys.argv
    if research_mode:
        sys.argv.remove("--research")
        if not is_sub_agent:
            print("🔬 Research mode enabled: Extra detailed logging + complete scratchpad display")
    depth = 0
    max_depth = 3
    parent_session_id = None
    
    if is_sub_agent:
        sys.argv.remove("--sub-agent")
        
        # Parse depth
        for i, arg in enumerate(sys.argv):
            if arg == "--depth" and i + 1 < len(sys.argv):
                depth = int(sys.argv[i + 1])
                sys.argv.pop(i)
                sys.argv.pop(i)
                break
        
        # Parse parent
        for i, arg in enumerate(sys.argv):
            if arg == "--parent" and i + 1 < len(sys.argv):
                parent_session_id = sys.argv[i + 1]
                sys.argv.pop(i)
                sys.argv.pop(i)
                break
        
        # Parse max-depth
        for i, arg in enumerate(sys.argv):
            if arg == "--max-depth" and i + 1 < len(sys.argv):
                max_depth = int(sys.argv[i + 1])
                sys.argv.pop(i)
                sys.argv.pop(i)
                break
    
    # Get research question
    if len(sys.argv) > 1:
        research_question = " ".join(sys.argv[1:])
    else:
        research_question = input("\n📝 Enter your research question: ")
    
    if not research_question.strip():
        print("❌ Error: Please provide a research question")
        return
    
    # Don't print headers for sub-agents
    if not is_sub_agent:
        print(f"\n🎯 Research Question: {research_question}")
        print("=" * 60)
    
    # Create agent and run research
    agent = InterviewResearchAgent(
        api_key=api_key, 
        verbose=not is_sub_agent,  # Sub-agents run quietly
        research_mode=research_mode,
        depth=depth,
        max_depth=max_depth,
        parent_session_id=parent_session_id,
        is_sub_agent=is_sub_agent,
        provider=provider
    )
    
    try:
        # Run research with appropriate iteration limit
        max_iter = 10 if is_sub_agent else 30
        results = await agent.autonomous_research(research_question, max_iterations=max_iter)
        
        # Sub-agents output JSON to stdout and exit
        if is_sub_agent:
            # Extract key information for summary
            tool_summary = {}
            for tc in results["tool_calls"]:
                tool_name = tc["tool"]
                if tool_name not in tool_summary:
                    tool_summary[tool_name] = 0
                tool_summary[tool_name] += 1
            
            # Create a brief summary of what the sub-agent did
            actions = []
            if "get_corpus_stats" in tool_summary:
                actions.append("analyzed corpus statistics")
            if "search_interviews" in tool_summary:
                actions.append(f"searched interviews {tool_summary['search_interviews']}x")
            if "get_interview_turn" in tool_summary:
                actions.append(f"examined {tool_summary['get_interview_turn']} interview segments")
            if "search_themes" in tool_summary:
                actions.append(f"explored themes {tool_summary['search_themes']}x")
            
            action_summary = ", ".join(actions) if actions else "conducted research"
            
            # Simplify results for parent agent
            sub_agent_results = {
                "final_response": results["final_response"],
                "session_id": results["session_id"],
                "parent_session_id": parent_session_id,
                "depth": depth,
                "iterations": results["iterations"],
                "tool_calls_count": len(results["tool_calls"]),
                "tool_summary": tool_summary,
                "action_summary": action_summary,
                "key_findings": results.get("scratchpad", ""),
                "stats": results["stats"]
            }
            print(json.dumps(sub_agent_results, ensure_ascii=False))
            return
        
        # Regular agents save results to files
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