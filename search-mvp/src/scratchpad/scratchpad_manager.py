#!/usr/bin/env python3
"""
Scratchpad Manager - For agent chain-of-thought exploration with tool use
"""

import json
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

class ScratchpadManager:
    """Manages scratchpad files for agent exploration sessions"""
    
    def __init__(self, session_name: Optional[str] = None):
        self.scratchpad_dir = Path("scratchpads")
        self.scratchpad_dir.mkdir(exist_ok=True)
        
        if session_name:
            self.session_name = session_name
        else:
            # Auto-generate session name with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            self.session_name = f"exploration_{timestamp}"
        
        self.scratchpad_file = self.scratchpad_dir / f"{self.session_name}.md"
        self.tools_log_file = self.scratchpad_dir / f"{self.session_name}_tools.json"
        
        # Initialize files if they don't exist
        self._init_session()
    
    def _init_session(self):
        """Initialize a new scratchpad session"""
        if not self.scratchpad_file.exists():
            initial_content = f"""# Research Session: {self.session_name}

**Started:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Research Question
_What am I trying to understand?_


## Key Findings
_Major insights discovered during exploration_


## Tool Use Log
_Record of CLI commands and their outcomes_


## Chain of Thought
_Reasoning process and next steps_


## Hypotheses
_Working theories to test_


## Connections
_Links between interviews, themes, and concepts_


## Next Steps
_What to explore next_

"""
            with open(self.scratchpad_file, 'w', encoding='utf-8') as f:
                f.write(initial_content)
        
        if not self.tools_log_file.exists():
            with open(self.tools_log_file, 'w', encoding='utf-8') as f:
                json.dump({"session": self.session_name, "tool_calls": []}, f, indent=2)
    
    def add_entry(self, section: str, content: str, timestamp: bool = True):
        """Add an entry to a specific section of the scratchpad"""
        with open(self.scratchpad_file, 'r', encoding='utf-8') as f:
            current_content = f.read()
        
        # Prepare the entry
        if timestamp:
            entry = f"\n### {datetime.now().strftime('%H:%M')} - {content}\n"
        else:
            entry = f"\n{content}\n"
        
        # Find the section and add content
        section_marker = f"## {section}"
        if section_marker in current_content:
            # Insert after the section header
            parts = current_content.split(section_marker)
            if len(parts) >= 2:
                # Find the next section or end of file
                remaining = parts[1]
                next_section_pos = remaining.find('\n## ')
                if next_section_pos != -1:
                    before_next = remaining[:next_section_pos]
                    after_next = remaining[next_section_pos:]
                    new_content = parts[0] + section_marker + before_next + entry + after_next
                else:
                    new_content = parts[0] + section_marker + remaining + entry
            else:
                new_content = current_content + f"\n{section_marker}\n{entry}"
        else:
            # Add new section at the end
            new_content = current_content + f"\n\n{section_marker}\n{entry}"
        
        with open(self.scratchpad_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
    
    def run_tool(self, command: str, description: str = "") -> Dict:
        """Run a CLI command and log it"""
        # Change to the correct directory for CLI tools
        original_dir = os.getcwd()
        cli_dir = Path(__file__).parent.parent.parent
        
        try:
            os.chdir(cli_dir)
            
            # Run the command
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            tool_result = {
                "timestamp": datetime.now().isoformat(),
                "command": command,
                "description": description,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0
            }
            
            # Log to tools file
            self._log_tool_call(tool_result)
            
            # Parse JSON output if successful
            if tool_result["success"] and tool_result["stdout"]:
                try:
                    tool_result["parsed_output"] = json.loads(tool_result["stdout"])
                except json.JSONDecodeError:
                    pass
            
            return tool_result
            
        except subprocess.TimeoutExpired:
            tool_result = {
                "timestamp": datetime.now().isoformat(),
                "command": command,
                "description": description,
                "error": "Command timed out",
                "success": False
            }
            self._log_tool_call(tool_result)
            return tool_result
            
        except Exception as e:
            tool_result = {
                "timestamp": datetime.now().isoformat(),
                "command": command,
                "description": description,
                "error": str(e),
                "success": False
            }
            self._log_tool_call(tool_result)
            return tool_result
            
        finally:
            os.chdir(original_dir)
    
    def _log_tool_call(self, tool_result: Dict):
        """Log tool call to tools file"""
        try:
            with open(self.tools_log_file, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
        except:
            log_data = {"session": self.session_name, "tool_calls": []}
        
        log_data["tool_calls"].append(tool_result)
        
        with open(self.tools_log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
    
    def log_tool_use(self, command: str, result: Dict, insight: str = ""):
        """Add a tool use entry to the scratchpad"""
        if result["success"]:
            status = "✅"
            if "parsed_output" in result:
                output_summary = self._summarize_output(result["parsed_output"])
            else:
                output_summary = result["stdout"][:200] + ("..." if len(result["stdout"]) > 200 else "")
        else:
            status = "❌"
            output_summary = result.get("error", result.get("stderr", "Unknown error"))
        
        entry = f"""**Command:** `{command}`
{status} **Result:** {output_summary}
{f'**Insight:** {insight}' if insight else ''}"""
        
        self.add_entry("Tool Use Log", entry)
    
    def _summarize_output(self, parsed_output: Dict) -> str:
        """Create a brief summary of tool output"""
        output_type = parsed_output.get("type", "unknown")
        
        if output_type == "search_results":
            return f"Found {parsed_output.get('total_results', 0)} results for '{parsed_output.get('query', '')}'"
        elif output_type == "single_turn":
            turn_id = parsed_output.get("turn", {}).get("turn_id", "unknown")
            is_quote = parsed_output.get("enrichment", {}).get("is_notable_quote", False)
            quote_status = " (notable quote)" if is_quote else ""
            return f"Turn {turn_id}{quote_status}"
        elif output_type == "theme_list":
            return f"Found {parsed_output.get('total_themes', 0)} themes"
        elif output_type == "interview_list":
            return f"Found {parsed_output.get('total_interviews', 0)} interviews"
        elif output_type == "corpus_stats":
            return f"Corpus: {parsed_output.get('total_interviews', 0)} interviews, {parsed_output.get('total_turns', 0)} turns"
        else:
            return f"Type: {output_type}"
    
    def add_finding(self, finding: str):
        """Add a key finding"""
        self.add_entry("Key Findings", finding)
    
    def add_thought(self, thought: str):
        """Add to chain of thought"""
        self.add_entry("Chain of Thought", thought)
    
    def add_hypothesis(self, hypothesis: str):
        """Add a hypothesis"""
        self.add_entry("Hypotheses", hypothesis)
    
    def add_connection(self, connection: str):
        """Add a connection between concepts"""
        self.add_entry("Connections", connection)
    
    def add_next_step(self, step: str):
        """Add a next step"""
        self.add_entry("Next Steps", step)
    
    def set_research_question(self, question: str):
        """Set or update the research question"""
        with open(self.scratchpad_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace the research question section
        lines = content.split('\n')
        new_lines = []
        in_research_section = False
        found_section = False
        
        for line in lines:
            if line.startswith('## Research Question'):
                new_lines.append(line)
                new_lines.append(f"_{question}_")
                new_lines.append("")
                in_research_section = True
                found_section = True
                continue
            elif line.startswith('## ') and in_research_section:
                in_research_section = False
            
            if not in_research_section:
                new_lines.append(line)
        
        with open(self.scratchpad_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
    
    def show(self):
        """Display the current scratchpad content"""
        if self.scratchpad_file.exists():
            with open(self.scratchpad_file, 'r', encoding='utf-8') as f:
                return f.read()
        return "Scratchpad not found"
    
    def list_sessions(self) -> List[str]:
        """List all available scratchpad sessions"""
        sessions = []
        for md_file in self.scratchpad_dir.glob("*.md"):
            sessions.append(md_file.stem)
        return sorted(sessions)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Scratchpad Manager for Research Sessions')
    parser.add_argument('--session', help='Session name (default: auto-generated)')
    
    subparsers = parser.add_subparsers(dest='action', help='Actions')
    
    # New session
    new_parser = subparsers.add_parser('new', help='Start new session')
    new_parser.add_argument('name', nargs='?', help='Session name')
    
    # Add entry
    add_parser = subparsers.add_parser('add', help='Add entry to scratchpad')
    add_parser.add_argument('section', choices=['finding', 'thought', 'hypothesis', 'connection', 'step'])
    add_parser.add_argument('content', help='Content to add')
    
    # Run tool
    tool_parser = subparsers.add_parser('tool', help='Run CLI tool and log result')
    tool_parser.add_argument('command', help='CLI command to run')
    tool_parser.add_argument('--insight', help='Your insight about the result')
    
    # Show scratchpad
    show_parser = subparsers.add_parser('show', help='Show scratchpad content')
    
    # List sessions
    list_parser = subparsers.add_parser('list', help='List all sessions')
    
    args = parser.parse_args()
    
    if args.action == 'list':
        sessions = ScratchpadManager().list_sessions()
        print("Available sessions:")
        for session in sessions:
            print(f"  - {session}")
        return
    
    # Initialize scratchpad
    scratchpad = ScratchpadManager(args.session)
    
    if args.action == 'new':
        if args.name:
            scratchpad = ScratchpadManager(args.name)
        print(f"Created new session: {scratchpad.session_name}")
        print(f"Scratchpad: {scratchpad.scratchpad_file}")
    
    elif args.action == 'add':
        if args.section == 'finding':
            scratchpad.add_finding(args.content)
        elif args.section == 'thought':
            scratchpad.add_thought(args.content)
        elif args.section == 'hypothesis':
            scratchpad.add_hypothesis(args.content)
        elif args.section == 'connection':
            scratchpad.add_connection(args.content)
        elif args.section == 'step':
            scratchpad.add_next_step(args.content)
        print(f"Added {args.section} to scratchpad")
    
    elif args.action == 'tool':
        print(f"Running: {args.command}")
        result = scratchpad.run_tool(args.command)
        scratchpad.log_tool_use(args.command, result, args.insight or "")
        
        if result["success"]:
            print("✅ Command successful")
            if "parsed_output" in result:
                print(json.dumps(result["parsed_output"], indent=2))
            else:
                print(result["stdout"])
        else:
            print("❌ Command failed")
            print(result.get("error", result.get("stderr", "Unknown error")))
    
    elif args.action == 'show':
        print(scratchpad.show())
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()