#!/usr/bin/env python3
"""
Uruguay Interview CLI - Enhanced version for enriched data with annotations
"""

import json
import re
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Union
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from search.simple_search import InterviewSearchEngine

class EnrichedUruguayCLI:
    def __init__(self):
        # Look for data in the project root, not relative to search-mvp
        project_root = Path(__file__).parent.parent.parent.parent
        self.enriched_dir = project_root / "data" / "processed" / "enriched"
        self.interview_files = {}
        self.theme_consolidation = None
        self._scan_interviews()
        self._load_theme_consolidation()
        
        # Initialize search engine for improved search
        self.search_engine = None
        try:
            self.search_engine = InterviewSearchEngine()
            corpus_path = project_root / "data" / "processed" / "structured" / "_corpus.json"
            if corpus_path.exists():
                self.search_engine.load_corpus(corpus_path)
        except Exception:
            # Fall back to old search if engine not available
            pass
    
    def _scan_interviews(self):
        """Scan for available enriched interview files"""
        if not self.enriched_dir.exists():
            return
        
        # Look for enriched interview files (with turns data)
        for json_file in self.enriched_dir.glob("*_enriched.json"):
            # Extract interview ID from filename
            interview_id = json_file.stem.replace("_enriched", "")
            self.interview_files[interview_id] = json_file
    
    def _load_theme_consolidation(self):
        """Load theme consolidation mapping if available"""
        consolidation_path = self.enriched_dir / "theme_consolidation.json"
        if consolidation_path.exists():
            with open(consolidation_path, 'r', encoding='utf-8') as f:
                self.theme_consolidation = json.load(f)
    
    def _load_interview(self, interview_id: str) -> Optional[Dict]:
        """Load a specific enriched interview on demand"""
        if interview_id not in self.interview_files:
            return None
        
        with open(self.interview_files[interview_id], 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get(self, item_id: str, full: bool = False) -> Dict:
        """Get a turn, range of turns, or interview by ID"""
        # Handle interview-only format: "071:" (get summary or full interview)
        if item_id.endswith(':'):
            interview_id = item_id[:-1].zfill(3)
            if full:
                return self._get_whole_interview_as_turns(interview_id)
            else:
                return self._get_interview_summary(interview_id)
        
        # Parse turn range format: "071:15-20" or "071:15-"
        if ':' in item_id and ('-' in item_id.split(':', 1)[1]):
            interview_id, turn_range = item_id.split(':', 1)
            interview_id = interview_id.zfill(3)
            
            # Parse range: "15-20" or "15-" or "-20"
            if turn_range.startswith('-'):
                start_turn = 1
                end_turn = int(turn_range[1:])
            elif turn_range.endswith('-'):
                start_turn = int(turn_range[:-1])
                end_turn = None  # Will be set to max later
            else:
                start_turn, end_turn = map(int, turn_range.split('-'))
            
            return self._get_turn_range(interview_id, start_turn, end_turn)
        
        # Single turn format: "071:15"
        if ':' in item_id:
            interview_id, turn_num = item_id.split(':')
            interview_id = interview_id.zfill(3)
            turn_num = int(turn_num)
            return self._get_single_turn(interview_id, turn_num)
        
        # Just interview ID: "071" (return metadata and summary)
        interview_id = item_id.zfill(3)
        return self._get_interview_summary(interview_id)
    
    def _get_single_turn(self, interview_id: str, turn_num: int) -> Dict:
        """Get a single turn with context"""
        interview = self._load_interview(interview_id)
        if not interview:
            return {"error": f"Interview {interview_id} not found"}
        
        turn_id = f"{interview_id}:{turn_num:0>2}"
        
        # Check if turn exists in index
        if turn_id not in interview["indexes"]["turn_by_id"]:
            return {"error": f"Turn {turn_id} not found"}
        
        turn_data = interview["indexes"]["turn_by_id"][turn_id]
        
        # Add enrichment context
        enrichment = {
            "is_notable_quote": turn_id in interview["indexes"]["notable_quote_turns"],
            "themes": [],
            "quote_context": None
        }
        
        # Find which themes this turn belongs to
        for theme, turn_ids in interview["indexes"]["turns_by_theme"].items():
            if turn_id in turn_ids:
                enrichment["themes"].append(theme)
        
        # Find quote context if it's a notable quote
        for quote in interview["annotation"]["notable_quotes"]:
            if quote.get("turn") == turn_id:
                enrichment["quote_context"] = {
                    "context": quote.get("context", ""),
                    "tags": quote.get("tags", [])
                }
                break
        
        return {
            "type": "single_turn",
            "turn": turn_data,
            "enrichment": enrichment
        }
    
    def _get_turn_range(self, interview_id: str, start: int, end: Optional[int]) -> Dict:
        """Get a range of turns"""
        interview = self._load_interview(interview_id)
        if not interview:
            return {"error": f"Interview {interview_id} not found"}
        
        turns = interview["turns"]
        
        if end is None:
            end = len(turns)
        
        # Filter turns in range
        selected_turns = []
        for turn in turns:
            turn_num = turn["turn_number"]
            if start <= turn_num <= end:
                selected_turns.append(turn)
        
        return {
            "type": "turn_range",
            "interview_id": interview_id,
            "range": f"{start}-{end}",
            "turns": selected_turns,
            "count": len(selected_turns)
        }
    
    def _get_whole_interview_as_turns(self, interview_id: str) -> Dict:
        """Get all turns from an interview"""
        interview = self._load_interview(interview_id)
        if not interview:
            return {"error": f"Interview {interview_id} not found"}
        
        return {
            "type": "full_interview",
            "interview_id": interview_id,
            "metadata": interview["metadata"],
            "turns": interview["turns"],
            "total_turns": len(interview["turns"])
        }
    
    def _get_interview_summary(self, interview_id: str) -> Dict:
        """Get interview summary and metadata"""
        interview = self._load_interview(interview_id)
        if not interview:
            return {"error": f"Interview {interview_id} not found"}
        
        # Build a useful summary for research
        annotation = interview.get("annotation", {})
        summary_obj = annotation.get("summary", {})
        
        # Extract themes with hierarchy
        themes = []
        meta_themes = set()
        issue_tags = annotation.get("issue_tags", [])
        
        key_themes = summary_obj.get("key_themes", [])
        for theme_obj in key_themes:
            if isinstance(theme_obj, dict):
                theme_info = {
                    "theme": theme_obj.get("theme", ""),
                    "description": theme_obj.get("description", ""),
                    "intensity": theme_obj.get("intensity", ""),
                    "meta_theme": theme_obj.get("meta_theme", ""),
                    "issue_tags": theme_obj.get("issue_tags", [])
                }
                themes.append(theme_info)
                if theme_obj.get("meta_theme"):
                    meta_themes.add(theme_obj.get("meta_theme"))
        
        summary = {
            "type": "interview_summary",
            "interview_id": interview_id,
            "metadata": interview.get("metadata", {}),
            "summary": summary_obj.get("overview", "No summary available"),
            "key_themes": themes,
            "meta_themes": list(meta_themes),
            "issue_tags": issue_tags,
            "priority_rankings": annotation.get("priorities", {}),
            "tags": annotation.get("tags", {}),
            "notable_quotes": [
                {
                    "turn": quote.get("turn"),
                    "quote": quote.get("quote", "")[:200] + "..." if len(quote.get("quote", "")) > 200 else quote.get("quote", ""),
                    "context": quote.get("context", "")
                }
                for quote in annotation.get("notable_quotes", [])[:3]  # Just first 3
            ],
            "stats": {
                "total_turns": len(interview["turns"]),
                "speakers": list(interview.get("indexes", {}).get("turns_by_speaker", {}).keys()),
                "theme_count": len(themes),
                "meta_theme_count": len(meta_themes),
                "issue_tag_count": len(issue_tags),
                "notable_quotes": len(annotation.get("notable_quotes", []))
            },
            "tips": {
                "explore_themes": f"To explore a specific theme, search for it or get specific turns",
                "get_full_interview": f"For all turns, use: get {interview_id}: --full",
                "notable_turns": f"Notable quote turns: {[q.get('turn') for q in annotation.get('notable_quotes', [])[:5]]}"
            }
        }
        
        return summary
    
    def search(self, query: str, interview_id: Optional[str] = None, aggregate: bool = True) -> Dict:
        """Search through enriched interviews"""
        # Try to use the improved search engine first
        if self.search_engine and self.search_engine.loaded and not interview_id:
            try:
                # Use the new OR-based search
                search_results = self.search_engine.search(query, limit=100)
                
                if not search_results:
                    # Get search suggestions
                    suggestions = self.search_engine.get_search_suggestions(query)
                    return {
                        "type": "search_results",
                        "query": query,
                        "total_results": 0,
                        "results": [],
                        "search_suggestions": suggestions
                    }
                
                # Convert to our format
                results = []
                for turn in search_results:
                    results.append({
                        "type": "turn_text_match",
                        "interview_id": turn['interview_id'],
                        "turn_id": turn['turn_id'],
                        "speaker": turn['speaker'],
                        "text": turn['text'],
                        "interview_location": turn.get('interview_location', 'Unknown')
                    })
                
                # If aggregate is True and we have many results, return aggregated view
                if aggregate and len(results) > 20:
                    return self._aggregate_search_results(query, results)
                
                return {
                    "type": "search_results",
                    "query": query,
                    "total_results": len(results),
                    "results": results[:50]  # Limit to 50 results
                }
                
            except Exception:
                # Fall back to old search method
                pass
        
        # Original search implementation
        results = []
        
        # Determine which interviews to search
        if interview_id:
            interview_ids = [interview_id.zfill(3)]
        else:
            interview_ids = list(self.interview_files.keys())
        
        for iid in interview_ids:
            interview = self._load_interview(iid)
            if not interview:
                continue
            
            interview_results = self._search_interview(interview, query)
            if interview_results:
                results.extend(interview_results)
        
        # If aggregate is True and we have many results, return aggregated view
        if aggregate and len(results) > 20:
            return self._aggregate_search_results(query, results)
        
        return {
            "type": "search_results",
            "query": query,
            "total_results": len(results),
            "results": results
        }
    
    def _search_interview(self, interview: Dict, query: str) -> List[Dict]:
        """Search within a single interview"""
        results = []
        query_lower = query.lower()
        
        # Search in tags
        for tag_category, tags in interview["annotation"]["tags"].items():
            for tag in tags:
                if query_lower in tag.lower():
                    results.append({
                        "type": "tag_match",
                        "interview_id": interview["interview_id"],
                        "category": tag_category,
                        "tag": tag,
                        "relevance": "high" if query_lower == tag.lower() else "medium"
                    })
        
        # Search in themes (handle new structure)
        annotation = interview.get("annotation", {})
        summary = annotation.get("summary", {})
        key_themes = summary.get("key_themes", [])
        
        for theme_obj in key_themes:
            if isinstance(theme_obj, dict):
                theme_name = theme_obj.get("theme", "")
                theme_desc = theme_obj.get("description", "")
                meta_theme = theme_obj.get("meta_theme", "")
                
                # Check if query matches theme name, description, or meta-theme
                if (query_lower in theme_name.lower() or 
                    query_lower in theme_desc.lower() or
                    query_lower in meta_theme.lower()):
                    
                    results.append({
                        "type": "theme_match",
                        "interview_id": interview["interview_id"],
                        "theme": theme_name,
                        "meta_theme": meta_theme,
                        "issue_tags": theme_obj.get("issue_tags", []),
                        "description": theme_desc[:200] + "..." if len(theme_desc) > 200 else theme_desc,
                        "turn_ids": theme_obj.get("elaboration_turns", [])
                    })
        
        # Search in issue tags
        interview_issue_tags = annotation.get("issue_tags", [])
        for tag in interview_issue_tags:
            if query_lower in tag.lower():
                results.append({
                    "type": "issue_tag_match",
                    "interview_id": interview["interview_id"],
                    "issue_tag": tag,
                    "themes": [t.get("theme") for t in key_themes if isinstance(t, dict) and tag in t.get("issue_tags", [])]
                })
        
        # Search in turn text
        for turn in interview["turns"]:
            if query_lower in turn["text"].lower():
                results.append({
                    "type": "turn_text_match",
                    "interview_id": interview["interview_id"],
                    "turn_id": turn["turn_id"],
                    "speaker": turn["speaker"],
                    "text": self._highlight_match(turn["text"], query),
                    "is_notable_quote": turn["turn_id"] in interview["indexes"]["notable_quote_turns"]
                })
        
        return results
    
    def _highlight_match(self, text: str, query: str) -> str:
        """Add simple highlighting to matched text"""
        return re.sub(f"({re.escape(query)})", r"**\1**", text, flags=re.IGNORECASE)
    
    def _aggregate_search_results(self, query: str, results: List[Dict]) -> Dict:
        """Aggregate search results for large result sets"""
        # Count matches by interview
        matches_by_interview = {}
        for result in results:
            interview_id = result["interview_id"]
            if interview_id not in matches_by_interview:
                matches_by_interview[interview_id] = {
                    "count": 0,
                    "turn_ids": []
                }
            matches_by_interview[interview_id]["count"] += 1
            
            # Collect turn IDs for text matches
            if result["type"] == "turn_text_match":
                matches_by_interview[interview_id]["turn_ids"].append(result["turn_id"])
        
        # Sort interviews by match count
        sorted_interviews = sorted(
            matches_by_interview.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )
        
        # Build top interviews list
        top_interviews = []
        for interview_id, data in sorted_interviews[:5]:  # Top 5
            top_interviews.append({
                "interview_id": interview_id,
                "match_count": data["count"],
                "sample_turns": data["turn_ids"][:3]  # First 3 turn IDs
            })
        
        return {
            "type": "aggregated_search_results",
            "query": query,
            "total_matches": len(results),
            "interviews_with_matches": len(matches_by_interview),
            "top_interviews": top_interviews
        }
    
    def list_themes(self, interview_id: Optional[str] = None, verbose: bool = False, summary_only: bool = False, filter_keyword: Optional[str] = None, meta_theme_filter: Optional[str] = None) -> Dict:
        """List all themes across interviews with hierarchical structure"""
        theme_summary = {}
        
        # Determine which interviews to analyze
        if interview_id:
            interview_ids = [interview_id.zfill(3)]
        else:
            interview_ids = list(self.interview_files.keys())
        
        for iid in interview_ids:
            interview = self._load_interview(iid)
            if not interview:
                continue
            
            # Get themes from new annotation structure
            annotation = interview.get("annotation", {})
            summary = annotation.get("summary", {})
            key_themes = summary.get("key_themes", [])
            
            for theme_obj in key_themes:
                if isinstance(theme_obj, dict):
                    theme_name = theme_obj.get("theme", "")
                    if not theme_name:
                        continue
                    
                    if theme_name not in theme_summary:
                        theme_summary[theme_name] = {
                            "interviews": [],
                            "interview_details": {},  # Store turn info per interview
                            "total_occurrences": 0,
                            "interview_count": 0,
                            "meta_theme": theme_obj.get("meta_theme", ""),
                            "issue_tags": theme_obj.get("issue_tags", [])
                        }
                    
                    # Get all turn IDs
                    primary_turns = theme_obj.get("primary_evidence", [])
                    elaboration_turns = theme_obj.get("elaboration_turns", [])
                    all_turns = primary_turns + elaboration_turns
                    turn_count = len(all_turns)
                    
                    if verbose:
                        theme_summary[theme_name]["interviews"].append({
                            "interview_id": iid,
                            "turn_count": turn_count,
                            "description": theme_obj.get("description", ""),
                            "intensity": theme_obj.get("intensity", "")
                        })
                    else:
                        theme_summary[theme_name]["interviews"].append(iid)
                    
                    # Always store turn details for summary mode
                    theme_summary[theme_name]["interview_details"][iid] = {
                        "turns": all_turns,
                        "turn_count": turn_count
                    }
                    
                    theme_summary[theme_name]["total_occurrences"] += turn_count
                    theme_summary[theme_name]["interview_count"] += 1
        
        # Filter by keyword if provided
        if filter_keyword:
            filtered_themes = {
                theme: data 
                for theme, data in theme_summary.items() 
                if filter_keyword.lower() in theme.lower()
            }
            theme_summary = filtered_themes
        
        # Sort themes by prevalence (total occurrences)
        sorted_themes = dict(sorted(theme_summary.items(), 
                                  key=lambda x: x[1]["total_occurrences"], 
                                  reverse=True))
        
        if summary_only:
            # Group by meta-theme for hierarchical view
            if self.theme_consolidation:
                meta_themes = self.theme_consolidation.get("meta_themes", {})
                hierarchy = {}
                
                for theme, data in sorted_themes.items():
                    meta_theme = data.get("meta_theme", "uncategorized")
                    # Skip empty meta_theme names
                    if not meta_theme or not meta_theme.strip():
                        meta_theme = "uncategorized"
                    
                    if meta_theme not in hierarchy:
                        hierarchy[meta_theme] = {
                            "name": meta_themes.get(meta_theme, {}).get("name", meta_theme),
                            "themes": {}
                        }
                    hierarchy[meta_theme]["themes"][theme] = {
                        "total_turns": data['total_occurrences'],
                        "interview_count": data['interview_count'],
                        "interviews": data.get('interviews', []),
                        "interview_details": data.get('interview_details', {})
                    }
                
                # Filter by specific meta_theme if requested
                if meta_theme_filter:
                    # Find matching meta_theme (case-insensitive)
                    meta_theme_lower = meta_theme_filter.lower()
                    filtered_hierarchy = {}
                    
                    for key, value in hierarchy.items():
                        if (key.lower() == meta_theme_lower or 
                            value.get("name", "").lower() == meta_theme_lower or
                            meta_theme_lower in key.lower() or
                            meta_theme_lower in value.get("name", "").lower()):
                            filtered_hierarchy[key] = value
                    
                    if filtered_hierarchy:
                        hierarchy = filtered_hierarchy
                    else:
                        # No matches found
                        return {
                            "type": "theme_hierarchy",
                            "meta_themes": {},
                            "total_themes": 0,
                            "mode": "meta_theme_filter",
                            "filter": meta_theme_filter,
                            "error": f"No meta-theme found matching '{meta_theme_filter}'"
                        }
                
                return {
                    "type": "theme_hierarchy",
                    "meta_themes": hierarchy,
                    "total_themes": sum(len(m["themes"]) for m in hierarchy.values()),
                    "mode": "summary",
                    "filtered": filter_keyword is not None,
                    "meta_theme_filter": meta_theme_filter
                }
            else:
                # Fallback to flat list if no consolidation
                summary_dict = {
                    theme: {
                        "total_turns": data['total_occurrences'],
                        "interview_count": data['interview_count'],
                        "interviews": data.get('interviews', [])
                    }
                    for theme, data in sorted_themes.items()
                }
                return {
                    "type": "theme_summary",
                    "themes": summary_dict,
                    "total_themes": len(sorted_themes),
                    "mode": "summary"
                }
        
        return {
            "type": "theme_list",
            "themes": sorted_themes,
            "total_themes": len(sorted_themes),
            "mode": "verbose" if verbose else "concise"
        }
    
    def list(self) -> Dict:
        """List all available interviews with summary stats"""
        interviews = []
        
        for interview_id in sorted(self.interview_files.keys()):
            interview = self._load_interview(interview_id)
            if not interview:
                continue
            
            interviews.append({
                "interview_id": interview_id,
                "total_turns": len(interview["turns"]),
                "speakers": list(interview["indexes"]["turns_by_speaker"].keys()),
                "theme_count": len(interview["indexes"]["turns_by_theme"]),
                "notable_quotes": len(interview["annotation"]["notable_quotes"]),
                "top_themes": list(interview["indexes"]["turns_by_theme"].keys())[:3]
            })
        
        return {
            "type": "interview_list",
            "interviews": interviews,
            "total_interviews": len(interviews)
        }
    
    def stats(self) -> Dict:
        """Get corpus-wide statistics"""
        total_interviews = 0
        total_turns = 0
        all_themes = set()
        all_meta_themes = set()
        all_issue_tags = set()
        all_speakers = set()
        total_quotes = 0
        
        # Track meta-theme breakdown
        meta_theme_breakdown = {}
        
        for interview_id in self.interview_files.keys():
            interview = self._load_interview(interview_id)
            if not interview:
                continue
            
            total_interviews += 1
            total_turns += len(interview["turns"])
            
            # Get themes from new structure
            annotation = interview.get("annotation", {})
            summary = annotation.get("summary", {})
            key_themes = summary.get("key_themes", [])
            
            for theme_obj in key_themes:
                if isinstance(theme_obj, dict):
                    theme = theme_obj.get("theme", "")
                    meta_theme = theme_obj.get("meta_theme", "uncategorized")
                    
                    if theme:
                        all_themes.add(theme)
                    
                    if meta_theme:
                        all_meta_themes.add(meta_theme)
                        
                        # Track in breakdown
                        if meta_theme not in meta_theme_breakdown:
                            meta_theme_breakdown[meta_theme] = {
                                "name": self.theme_consolidation.get("meta_themes", {}).get(meta_theme, {}).get("name", meta_theme),
                                "themes": set()
                            }
                        meta_theme_breakdown[meta_theme]["themes"].add(theme)
            
            all_issue_tags.update(annotation.get("issue_tags", []))
            all_speakers.update(interview.get("indexes", {}).get("turns_by_speaker", {}).keys())
            total_quotes += len(annotation.get("notable_quotes", []))
        
        stats_result = {
            "type": "corpus_stats",
            "total_interviews": total_interviews,
            "total_turns": total_turns,
            "unique_themes": len(all_themes),
            "unique_meta_themes": len(all_meta_themes),
            "unique_issue_tags": len(all_issue_tags),
            "unique_speakers": len(all_speakers),
            "total_notable_quotes": total_quotes,
            "avg_turns_per_interview": round(total_turns / total_interviews, 1) if total_interviews > 0 else 0
        }
        
        # Add consolidation info if available
        if self.theme_consolidation:
            stats_result["theme_consolidation"] = {
                "available": True,
                "total_meta_themes": len(self.theme_consolidation.get("meta_themes", {})),
                "total_issue_tags": len(self.theme_consolidation.get("metadata", {}).get("issue_tags", {}))
            }
            
            # Convert theme sets to counts for JSON serialization
            meta_theme_dict = {}
            for meta_key, meta_info in meta_theme_breakdown.items():
                meta_theme_dict[meta_key] = {
                    "name": meta_info["name"],
                    "theme_count": len(meta_info["themes"])
                }
            
            stats_result["meta_theme_breakdown"] = meta_theme_dict
        
        return stats_result


def main():
    parser = argparse.ArgumentParser(description='Uruguay Interview Enriched CLI')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Get command
    get_parser = subparsers.add_parser('get', help='Get turn(s) or interview')
    get_parser.add_argument('item_id', help='Turn ID (071:15), range (071:15-20), or interview summary (071:)')
    get_parser.add_argument('--full', action='store_true', help='For interview requests (071:), return all turns instead of just summary')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search interviews')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--interview', help='Limit search to specific interview')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List interviews')
    
    # Themes command
    themes_parser = subparsers.add_parser('themes', help='List themes')
    themes_parser.add_argument('--interview', help='Limit to specific interview')
    themes_parser.add_argument('--verbose', action='store_true', help='Include all turn IDs (generates large output)')
    themes_parser.add_argument('--summary', action='store_true', help='Ultra-concise output (just counts)')
    themes_parser.add_argument('--filter', help='Filter themes by keyword')
    themes_parser.add_argument('--meta-theme', help='Show detailed themes for a specific meta-theme')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show corpus statistics')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = EnrichedUruguayCLI()
    
    if args.command == 'get':
        result = cli.get(args.item_id, full=args.full if hasattr(args, 'full') else False)
    elif args.command == 'search':
        result = cli.search(args.query, args.interview)
    elif args.command == 'list':
        result = cli.list()
    elif args.command == 'themes':
        result = cli.list_themes(
            args.interview, 
            verbose=args.verbose if hasattr(args, 'verbose') else False,
            summary_only=args.summary if hasattr(args, 'summary') else False,
            filter_keyword=args.filter if hasattr(args, 'filter') else None,
            meta_theme_filter=args.meta_theme if hasattr(args, 'meta_theme') else None
        )
    elif args.command == 'stats':
        result = cli.stats()
    else:
        print("Unknown command")
        return
    
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()