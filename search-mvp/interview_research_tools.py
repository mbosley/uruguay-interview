# interview_research_tools.py
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
    
    "list_interview_themes": {
        "command": "python src/cli/enriched_cli.py themes --summary",
        "schema": {
            "type": "function", 
            "function": {
                "name": "list_interview_themes",
                "description": "Get complete list of all 121 themes across the corpus with occurrence counts. ALWAYS USE THIS EARLY to understand what citizens discuss. Reveals crisis patterns, priority themes, and unexpected topics. Essential for research planning.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "interview_id": {
                            "type": "string",
                            "description": "Optional: limit to specific interview (e.g. '072')"
                        }
                    }
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
                "description": "Get corpus overview: 35 interviews, 5510 turns, 121 themes. Quick orientation to understand scope. Always start here.",
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
    
    "search_themes": {
        "command": "python src/cli/enriched_cli.py themes --summary --filter {keyword}",
        "schema": {
            "type": "function",
            "function": {
                "name": "search_themes", 
                "description": "Search for themes containing specific keywords. Returns matching themes with their prevalence.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "keyword": {
                            "type": "string",
                            "description": "Keyword to search for in theme names (e.g. 'education', 'health', 'rural')"
                        }
                    },
                    "required": ["keyword"]
                }
            }
        }
    }
}