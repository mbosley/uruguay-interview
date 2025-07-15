#!/usr/bin/env python3
"""
Uruguay Interview CLI - Enhanced version for enriched data with annotations
"""

import json
import re
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Union

class EnrichedUruguayCLI:
    def __init__(self):
        # Look for data in the project root, not relative to search-mvp
        project_root = Path(__file__).parent.parent.parent.parent
        self.enriched_dir = project_root / "data" / "processed" / "enriched"
        self.interview_files = {}
        self._scan_interviews()
    
    def _scan_interviews(self):
        """Scan for available enriched interview files"""
        if not self.enriched_dir.exists():
            return
        
        # Look for enriched interview files (with turns data)
        for json_file in self.enriched_dir.glob("*_enriched.json"):
            # Extract interview ID from filename
            interview_id = json_file.stem.replace("_enriched", "")
            self.interview_files[interview_id] = json_file
    
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
        summary = {
            "type": "interview_summary",
            "interview_id": interview_id,
            "metadata": interview.get("metadata", {}),
            "summary": annotation.get("summary", "No summary available"),
            "key_themes": annotation.get("key_themes", []),
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
                "speakers": list(interview["indexes"]["turns_by_speaker"].keys()),
                "theme_count": len(interview["indexes"]["turns_by_theme"].keys()),
                "notable_quotes": len(interview["annotation"]["notable_quotes"])
            },
            "tips": {
                "explore_themes": f"To explore a specific theme, search for it or get specific turns",
                "get_full_interview": f"For all turns, use: get {interview_id}: --full",
                "notable_turns": f"Notable quote turns: {[q.get('turn') for q in annotation.get('notable_quotes', [])[:5]]}"
            }
        }
        
        return summary
    
    def search(self, query: str, interview_id: Optional[str] = None) -> Dict:
        """Search through enriched interviews"""
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
        
        # Search in themes
        for theme in interview["annotation"]["key_themes"]:
            theme_name = theme.get("theme", "")
            if query_lower in theme_name.lower() or query_lower in theme.get("description", "").lower():
                results.append({
                    "type": "theme_match",
                    "interview_id": interview["interview_id"],
                    "theme": theme_name,
                    "description": theme.get("description", "")[:200] + "...",
                    "turn_ids": theme.get("elaboration_turns", [])
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
    
    def list_themes(self, interview_id: Optional[str] = None, verbose: bool = False, summary_only: bool = False, filter_keyword: Optional[str] = None) -> Dict:
        """List all themes across interviews"""
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
            
            for theme_name, turn_ids in interview["indexes"]["turns_by_theme"].items():
                if theme_name not in theme_summary:
                    theme_summary[theme_name] = {
                        "interviews": [],
                        "total_turns": 0,
                        "interview_count": 0
                    }
                
                if verbose:
                    # Include full turn IDs in verbose mode
                    theme_summary[theme_name]["interviews"].append({
                        "interview_id": iid,
                        "turn_count": len(turn_ids),
                        "turn_ids": turn_ids
                    })
                else:
                    # Just track counts in concise mode
                    theme_summary[theme_name]["interviews"].append(iid)
                
                theme_summary[theme_name]["total_turns"] += len(turn_ids)
                theme_summary[theme_name]["interview_count"] = len(set(theme_summary[theme_name]["interviews"]))
        
        # Filter by keyword if provided
        if filter_keyword:
            filtered_themes = {
                theme: data 
                for theme, data in theme_summary.items() 
                if filter_keyword.lower() in theme.lower()
            }
            theme_summary = filtered_themes
        
        # Sort themes by prevalence (total turns)
        sorted_themes = dict(sorted(theme_summary.items(), 
                                  key=lambda x: x[1]["total_turns"], 
                                  reverse=True))
        
        if summary_only:
            # Ultra-concise: just theme names with turn counts
            summary_dict = {
                theme: f"{data['total_turns']} turns across {data['interview_count']} interviews"
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
        all_speakers = set()
        total_quotes = 0
        
        for interview_id in self.interview_files.keys():
            interview = self._load_interview(interview_id)
            if not interview:
                continue
            
            total_interviews += 1
            total_turns += len(interview["turns"])
            all_themes.update(interview["indexes"]["turns_by_theme"].keys())
            all_speakers.update(interview["indexes"]["turns_by_speaker"].keys())
            total_quotes += len(interview["annotation"]["notable_quotes"])
        
        return {
            "type": "corpus_stats",
            "total_interviews": total_interviews,
            "total_turns": total_turns,
            "unique_themes": len(all_themes),
            "unique_speakers": len(all_speakers),
            "total_notable_quotes": total_quotes,
            "avg_turns_per_interview": round(total_turns / total_interviews, 1) if total_interviews > 0 else 0
        }


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
            filter_keyword=args.filter if hasattr(args, 'filter') else None
        )
    elif args.command == 'stats':
        result = cli.stats()
    else:
        print("Unknown command")
        return
    
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()