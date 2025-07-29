# interview_research_tools_enhanced.py
"""
Enhanced research tools that include hierarchical theme exploration
This extends the original tools with issue tag and meta-theme navigation
"""

# Import original tools
from interview_research_tools import INTERVIEW_RESEARCH_TOOLS

# Add new hierarchical tools
ENHANCED_RESEARCH_TOOLS = INTERVIEW_RESEARCH_TOOLS.copy()

# Add the new tools
ENHANCED_RESEARCH_TOOLS.update({
    "explore_issue_tag": {
        "command": "python -c \"from interview_research_tools_v2 import explore_issue_tag; print(explore_issue_tag('{issue_tag}'))\"",
        "schema": {
            "type": "function",
            "function": {
                "name": "explore_issue_tag",
                "description": "Explore interviews by high-level issue tag (e.g., 'healthcare', 'education', 'security'). Returns all related meta-themes, themes, and sample interviews. Best for: Starting broad exploration of a policy area, understanding how an issue manifests across different communities.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "issue_tag": {
                            "type": "string",
                            "description": "Issue tag to explore. Options: healthcare, education, economy, security, infrastructure, housing, governance, social_welfare, rural_development, environment, culture, youth"
                        }
                    },
                    "required": ["issue_tag"]
                }
            }
        }
    },
    
    "explore_meta_theme": {
        "command": "python -c \"from interview_research_tools_v2 import explore_meta_theme; print(explore_meta_theme('{meta_theme_id}'))\"",
        "schema": {
            "type": "function",
            "function": {
                "name": "explore_meta_theme",
                "description": "Explore interviews by consolidated meta-theme (e.g., 'healthcare_crisis', 'education_system_failure'). Returns theme distribution, location patterns, and top interviews. Best for: Focused exploration of a specific systemic issue.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "meta_theme_id": {
                            "type": "string",
                            "description": "Meta-theme ID to explore (e.g., 'healthcare_crisis', 'education_system_failure', 'employment_structural_crisis')"
                        }
                    },
                    "required": ["meta_theme_id"]
                }
            }
        }
    },
    
    "search_themes_semantic": {
        "command": "python -c \"from interview_research_tools_v2 import search_themes; print(search_themes('{query}', {top_k}))\"",
        "schema": {
            "type": "function",
            "function": {
                "name": "search_themes_semantic",
                "description": "Search for themes using semantic similarity to your query. Returns ranked themes with their meta-themes, issue tags, and sample quotes. Best for: Finding themes related to specific concepts or when you're not sure of exact terminology.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query describing the themes you're looking for"
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Number of top themes to return",
                            "default": 10
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    },
    
    "get_theme_hierarchy": {
        "command": "python -c \"from interview_research_tools_v2 import get_hierarchy; print(get_hierarchy())\"",
        "schema": {
            "type": "function",
            "function": {
                "name": "get_theme_hierarchy",
                "description": "Get the complete theme hierarchy showing issue tags → meta-themes → specific themes. Best for: Understanding the overall structure of citizen concerns, planning systematic exploration.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
    },
    
    "analyze_cross_cutting_themes": {
        "command": "python -c \"from interview_research_tools_v2 import analyze_intersections; print(analyze_intersections({issue_tags}))\"",
        "schema": {
            "type": "function",
            "function": {
                "name": "analyze_cross_cutting_themes",
                "description": "Analyze themes that appear across multiple issue tags to understand intersectional issues. Best for: Understanding how different policy areas interact (e.g., how healthcare and poverty intersect).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "issue_tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of issue tags to analyze for intersections"
                        }
                    },
                    "required": ["issue_tags"]
                }
            }
        }
    }
})

# Update the spawn_sub_agent tool description to mention hierarchical exploration
if "spawn_sub_agent" in ENHANCED_RESEARCH_TOOLS:
    ENHANCED_RESEARCH_TOOLS["spawn_sub_agent"]["schema"]["function"]["description"] = """Delegate a focused research task to a sub-agent when you need deep exploration of a specific theme, issue tag, or meta-theme. The sub-agent will conduct thorough research and return findings. Best for: Parallel exploration of multiple themes, detailed analysis of complex topics, or when following the theme hierarchy reveals multiple areas needing investigation. Example: After using explore_issue_tag('healthcare'), delegate specific meta-themes to sub-agents."""

# Export the enhanced tools
INTERVIEW_RESEARCH_TOOLS = ENHANCED_RESEARCH_TOOLS