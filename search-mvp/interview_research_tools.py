# interview_research_tools.py
"""
Interview Research Tools
Includes both original tools and hierarchical theme exploration tools
"""

INTERVIEW_RESEARCH_TOOLS = {
    "search_interviews": {
        "command": "python src/cli/enriched_cli.py search {query}",
        "schema": {
            "type": "function",
            "function": {
                "name": "search_interviews",
                "description": "Search for specific words/phrases across all 35 interviews. Returns theme matches, tag matches, and text excerpts. Best for: finding specific quotes, tracking how topics are discussed, discovering which interviews mention your topic. Pro tip: Search in Spanish for better results.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string", 
                            "description": "Search term or phrase to find in interviews"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    },
    
    "get_interview_turn": {
        "command": "python src/cli/enriched_cli.py get {turn_id}", 
        "schema": {
            "type": "function",
            "function": {
                "name": "get_interview_turn",
                "description": "Get a specific turn, range of turns, or interview summary. Use '072:' for interview summary (recommended for initial exploration), '072:24' for specific turn, '072:20-25' for turn range.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "turn_id": {
                            "type": "string",
                            "description": "Turn ID (e.g. '072:24'), range (e.g. '072:20-25'), or interview summary (e.g. '072:'). Interview summaries include metadata, key themes, notable quotes, and guidance for deeper exploration."
                        }
                    },
                    "required": ["turn_id"]
                }
            }
        }
    },
    
    
    "get_corpus_stats": {
        "command": "python src/cli/enriched_cli.py stats",
        "schema": {
            "type": "function",
            "function": {
                "name": "get_corpus_stats", 
                "description": "Get corpus overview with meta-theme categories. Shows: 35 interviews, 5510 turns, 121 themes organized into 17 meta-themes like 'Educational System Breakdown', 'Employment Crisis', etc. ALWAYS START HERE to see the thematic landscape.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        }
    },
    
    "scratchpad_append": {
        "command": "python -c \"from src.tools.scratchpad_tools import append_note; print(append_note('''{note}''', '{session_id}'))\"",
        "schema": {
            "type": "function",
            "function": {
                "name": "scratchpad_append",
                "description": "Add to your research journal. Think out loud! Record observations, questions, hypotheses, connections, surprises, contradictions. Write naturally about what you're discovering and how your understanding is evolving. ALWAYS include citations (e.g., 071:23) but focus on your thinking process.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "note": {
                            "type": "string",
                            "description": "Your thinking, written naturally. Share observations, questions, evolving understanding. Include citations (e.g., 071:23) within your narrative thinking."
                        }
                    },
                    "required": ["note"]
                }
            }
        }
    },
    
    "scratchpad_read": {
        "command": "python -c \"from src.tools.scratchpad_tools import read_notes; print(read_notes('{session_id}'))\"",
        "schema": {
            "type": "function",
            "function": {
                "name": "scratchpad_read",
                "description": "Review your research journal to see how your thinking has evolved. Use this to build on previous insights, notice patterns in your observations, and identify what to explore next.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
    },
    
    "explore_meta_theme": {
        "command": "python src/cli/enriched_cli.py themes --summary --meta-theme {meta_theme}",
        "schema": {
            "type": "function",
            "function": {
                "name": "explore_meta_theme", 
                "description": "Deep dive into a specific meta-theme category. Shows all themes within that category with turn counts and interview locations. IMPORTANT: Use the exact key from corpus stats (with underscores), not the display name. Examples: 'security_and_drugs' (NOT 'Security Crisis and Drug Proliferation'), 'education_system_failure', 'healthcare_access', 'employment_crisis'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "meta_theme": {
                            "type": "string",
                            "description": "Meta-theme key from corpus stats. Use underscores, not spaces. Examples: security_and_drugs, education_system_failure, healthcare_access, employment_crisis, rural_urban_disparity"
                        }
                    },
                    "required": ["meta_theme"]
                }
            }
        }
    },
    
    "spawn_sub_agent": {
        "command": "python interview_research_agent_improved.py --sub-agent --depth {depth} --parent {parent_id} --max-depth {max_depth} \"{question}\"",
        "schema": {
            "type": "function",
            "function": {
                "name": "spawn_sub_agent",
                "description": "Delegate a specific research sub-question to a specialized agent. Use this when: 1) You identify a complex theme needing deep exploration, 2) Multiple parallel investigations would be efficient, 3) You need focused analysis on a specific aspect. The sub-agent conducts independent research and returns structured findings. Example: After finding education themes across many interviews, delegate 'Analyze teacher perspectives on rural education challenges' to explore deeply.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "Specific, focused research question for the sub-agent. Should be narrower than your main question."
                        },
                        "context": {
                            "type": "string",
                            "description": "Brief context about what you've found so far and why this delegation is needed. Include relevant interview IDs or themes."
                        },
                        "max_iterations": {
                            "type": "integer",
                            "description": "Maximum iterations for the sub-agent (default: 10, max: 20)",
                            "default": 10,
                            "maximum": 20
                        }
                    },
                    "required": ["question", "context"]
                }
            }
        }
    }
}