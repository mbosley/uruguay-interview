# interview_research_agent.py
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

# Load environment variables
load_dotenv()

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/agent_debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class InterviewResearchAgent:
    def __init__(self, api_key=None, model="kimi-k2-0711-preview"):
        self.client = OpenAI(
            api_key=api_key or os.getenv("MOONSHOT_API_KEY"),
            base_url="https://api.moonshot.ai/v1"
        )
        self.model = model
        self.tools = INTERVIEW_RESEARCH_TOOLS
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    async def autonomous_research(self, research_question, max_iterations=15):
        """Main research method using Kimi's exact pattern"""
        
        # Initialize conversation (exactly like kimi_chat)
        final_messages = [{
            "role": "user",
            "content": f"""You are an expert qualitative researcher with access to a corpus of citizen consultation interviews from Uruguay (May 28-29, 2025). These interviews explore citizen perspectives on national and local priorities.

Research Question: {research_question}

Your task is to explore this question thoroughly using the available tools. Think step by step:
1. Start with corpus overview if helpful
2. Search for relevant themes and topics  
3. Examine specific turns and quotes
4. Build evidence chains and connections
5. Synthesize findings into insights

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

[Making connections]
"Interesting connection: The 'interconnected_crisis_violence_education_economy' theme 
(063:08, 063:25) explicitly links education to broader social issues. Parents can't 
help with homework when working multiple jobs, kids come to school hungry...

This connects to teacher exhaustion theme (072:) - teachers aren't just teaching, 
they're social workers, counselors, feeding programs. The 'administrative overload' 
might actually be about handling poverty/crisis management, not paperwork?"

[Evolving understanding]
"Initially focused on education as isolated sector, but now seeing it's deeply 
intertwined with economic crisis. Multiple interviews (063:, 072:, 091:) suggest 
education problems are symptoms, not root causes. This reframes the whole research 
question - maybe we should be asking not 'what's wrong with education?' but 'what 
societal fractures does education reveal?'"

[Contradictions to explore]
"Tension emerging: Interview 080 describes rural teachers as unmotivated, gaming the 
system through strategic leave-taking. But 068:02 shows 20-year veteran teacher 
deeply concerned about rural students' futures. Are these different regions? Different 
school types? Or capturing different aspects of teacher experience - burnout vs 
dedication existing side by side?"

[Quantifying observations]
"Tracking how often certain issues appear:
- Teacher burnout/exhaustion: 072:, 080:, (2 interviews explicitly, but hints in others?)
- Rural education gaps: 068:, 077:, 080:, 085: (at least 4 interviews)
- Link to poverty: 063:, 072:89, 091: (3+ interviews make explicit connection)
Need to be systematic - maybe search for 'pobreza' or 'poverty' to catch all mentions?"

[Methodological notes]
"Realizing I've been focusing on negative themes, but should check - are there ANY 
positive education mentions? Success stories? Hope for improvement? The absence of 
positive framings might be as telling as the presence of crisis language. Need to 
search for terms like 'mejora', 'esperanza', 'éxito' to test this..."

Use scratchpad_read periodically to review your thinking and build on previous insights.

Take your time and explore deeply. Use multiple tool calls to build a comprehensive understanding. When you have sufficient evidence and insights, provide a summary with specific citations."""
        }]
        
        iteration = 0
        tool_call_log = []
        final_response = "Research incomplete - reached maximum iterations or encountered error"
        
        while iteration < max_iterations:
            try:
                print(f"🔄 Iteration {iteration + 1}/{max_iterations}")
                logger.info(f"Starting iteration {iteration + 1}")
                
                # Log conversation state
                logger.info(f"Conversation has {len(final_messages)} messages")
                logger.info(f"Last message role: {final_messages[-1]['role']}")
                
                # Make API call with tools (exact Kimi pattern)
                api_params = {
                    "model": self.model,
                    "messages": final_messages,
                    "temperature": 0.7,
                    "max_tokens": 4096,
                    "tools": [tool["schema"] for tool in self.tools.values()]
                }
                
                logger.info(f"Making API call with {len(api_params['tools'])} tools available")
                logger.info(f"API params: model={api_params['model']}, temp={api_params['temperature']}")
                
                response = self.client.chat.completions.create(**api_params)
                message = response.choices[0].message
                
                logger.info(f"Got response: content_length={len(message.content or '')}")
                logger.info(f"Finish reason: {response.choices[0].finish_reason}")
                logger.info(f"Has tool_calls: {hasattr(message, 'tool_calls') and bool(message.tool_calls)}")
                
                # Check if Kimi wants to call tools (exact same logic)
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    logger.info(f"Agent wants to use {len(message.tool_calls)} tools")
                    
                    # Show agent's reasoning
                    if message.content:
                        print(f"💭 Agent thinking: {message.content}")
                        logger.info(f"Agent reasoning: {message.content}")
                    print(f"🔧 Making {len(message.tool_calls)} tool call(s)")
                    
                    # Add assistant's message with tool calls to conversation
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
                    
                    # Execute each tool call (exact same pattern)
                    for tool_call in message.tool_calls:
                        tool_name = tool_call.function.name
                        tool_args_str = tool_call.function.arguments
                        
                        print(f"  🔍 {tool_name}({tool_args_str})")
                        
                        # Parse arguments
                        try:
                            tool_args = json.loads(tool_args_str) if tool_args_str else {}
                        except json.JSONDecodeError:
                            tool_args = {}
                        
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
                            else:
                                result = f"Error: Tool configuration not found for '{tool_name}'"
                        else:
                            result = f"Error: Unknown tool '{tool_name}'"
                        
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
                        
                        print(f"    ✅ Result: {len(result)} characters")
                    
                    iteration += 1
                    continue  # Continue loop for follow-up response
                    
                else:
                    # No tools used - agent is done
                    print("🏁 Agent finished exploration")
                    logger.info("Agent chose not to use tools - finishing")
                    logger.info(f"Final response length: {len(message.content or '')}")
                    logger.info(f"Final response preview: {(message.content or '')[:200]}...")
                    final_response = message.content
                    break
                    
            except Exception as e:
                error_msg = f"Error in iteration {iteration}: {str(e)}"
                print(f"❌ {error_msg}")
                logger.error(f"Exception in iteration {iteration}: {e}")
                logger.error(f"Exception type: {type(e)}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                break
        
        # If we have tool calls but no final response, generate a summary
        if tool_call_log and (not final_response or final_response == "Research incomplete - reached maximum iterations or encountered error"):
            print(f"📋 Generating summary from {len(tool_call_log)} tool calls...")
            logger.info(f"Generating summary from findings - {len(tool_call_log)} tool calls made")
            
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
- Embed citations naturally in narrative text
- Group related citations when making broader claims
- Every claim, pattern, or interpretation must have supporting citations
- If you write "Citizens express..." or "Many interviewees..." you MUST cite who
- If you write "A pattern emerges..." you MUST cite where
- If you write "This suggests..." you MUST cite what evidence
- NO UNCITED GENERALIZATIONS - every statement needs evidence
"""
                
                final_messages.append({
                    "role": "user", 
                    "content": summary_prompt
                })
                
                # Get final summary (without tools)
                summary_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=final_messages,
                    temperature=0.7,
                    max_tokens=4096
                )
                
                final_response = summary_response.choices[0].message.content
                print("✅ Summary generated successfully")
                logger.info(f"Summary generated: {len(final_response)} characters")
                
            except Exception as e:
                logger.error(f"Failed to generate summary: {e}")
                final_response = f"Research completed with {len(tool_call_log)} tool calls, but summary generation failed: {str(e)}"
        
        return {
            "final_response": final_response,
            "tool_calls": tool_call_log,
            "iterations": iteration,
            "full_conversation": final_messages,
            "scratchpad_file": f"scratchpads/session_{self.session_id}.md"
        }
    
    def execute_cli_tool(self, tool_name: str, command: str, arguments: dict) -> str:
        """Execute CLI tool (borrowed from llm-mcp-server)"""
        try:
            # Add session_id to arguments for scratchpad tools
            if tool_name in ["scratchpad_append", "scratchpad_read"]:
                arguments["session_id"] = self.session_id
            
            # Build command with arguments
            if arguments:
                # For scratchpad tools, use base64 to safely pass arguments
                if tool_name in ["scratchpad_append", "scratchpad_read"]:
                    if "note" in arguments:
                        # Use base64 to safely encode the note content
                        import base64
                        note_b64 = base64.b64encode(arguments["note"].encode()).decode()
                        session_id = arguments.get("session_id", "")
                        full_command = f'python -c "import base64; from src.tools.scratchpad_tools import append_note; print(append_note(base64.b64decode(\'{note_b64}\').decode(), \'{session_id}\'))"'
                    else:
                        # For read operation
                        session_id = arguments.get("session_id", "")
                        full_command = f'python -c "from src.tools.scratchpad_tools import read_notes; print(read_notes(\'{session_id}\'))"'
                else:
                    # For CLI tools with placeholders, replace them
                    full_command = command
                    for key, value in arguments.items():
                        if key == "session_id":
                            continue  # Skip session_id for non-scratchpad tools
                        str_value = str(value)
                        # Check if placeholder exists in command
                        if f"{{{key}}}" in full_command:
                            # Quote the value if it contains spaces (for CLI arguments)
                            if ' ' in str_value and key in ['query', 'keyword']:
                                str_value = f'"{str_value}"'
                            full_command = full_command.replace(f"{{{key}}}", str_value)
                        else:
                            # For commands without placeholders, append as flags
                            if key == "interview_id" and value:
                                full_command += f" --interview {str_value}"
            else:
                full_command = command
            
            # Log the command being executed
            logger.info(f"Executing command: {full_command}")
            
            # Execute command 
            result = subprocess.run(
                full_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(Path(__file__).parent)  # Run from search-mvp directory
            )
            
            if result.returncode == 0:
                logger.info(f"Command succeeded, output length: {len(result.stdout)}")
                return result.stdout
            else:
                logger.error(f"Command failed with code {result.returncode}: {result.stderr}")
                return f"Command failed: {result.stderr if result.stderr else 'no error output'}"
                
        except subprocess.TimeoutExpired:
            return "Error: Command timed out"
        except Exception as e:
            return f"Error executing tool: {str(e)}"

# CLI interface
async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Interview Research Agent using Kimi')
    parser.add_argument('--question', required=True, help='Research question to explore')
    parser.add_argument('--api-key', help='Moonshot API key (or set MOONSHOT_API_KEY env var)')
    parser.add_argument('--max-iterations', type=int, default=15, help='Maximum tool call iterations')
    
    args = parser.parse_args()
    
    agent = InterviewResearchAgent(api_key=args.api_key)
    
    print(f"🔬 Starting research: {args.question}")
    print(f"🤖 Using model: {agent.model}")
    print("=" * 60)
    
    result = await agent.autonomous_research(args.question, args.max_iterations)
    
    print(f"\n📊 Research Complete!")
    print(f"🔧 Tool calls made: {len(result['tool_calls'])}")
    print(f"🔄 Iterations: {result['iterations']}")
    print(f"📝 Scratchpad: {result['scratchpad_file']}")
    print("=" * 60)
    print(f"\n{result['final_response']}")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"results/research_results_{timestamp}.json"
    with open(results_file, 'w') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Detailed results saved to: {results_file}")

if __name__ == "__main__":
    asyncio.run(main())