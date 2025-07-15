#!/usr/bin/env python3
"""
Uruguay Interview CLI - Simple commands for agent exploration
"""

import json
import re
import argparse
from pathlib import Path
from typing import Dict, List, Optional

class UruguayCLI:
    def __init__(self):
        self.structured_dir = Path("../data/processed/structured")
        self.interview_files = {}
        self._scan_interviews()
    
    def _scan_interviews(self):
        """Scan for available interview files"""
        if not self.structured_dir.exists():
            return
        
        for json_file in self.structured_dir.glob("[0-9]*.json"):
            # Extract interview ID from filename
            interview_id = json_file.stem
            self.interview_files[interview_id] = json_file
    
    def _load_interview(self, interview_id: str) -> Optional[Dict]:
        """Load a specific interview on demand"""
        if interview_id not in self.interview_files:
            return None
        
        with open(self.interview_files[interview_id], 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get(self, item_id: str) -> Dict:
        """Get a turn, range of turns, or interview by ID"""
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
                start_str, end_str = turn_range.split('-', 1)
                start_turn = int(start_str)
                end_turn = int(end_str)
            
            return self._get_turn_range(interview_id, start_turn, end_turn)
        
        # Parse "071:" format - return whole interview as turns
        elif item_id.endswith(':'):
            interview_id = item_id[:-1].zfill(3)
            return self._get_whole_interview_as_turns(interview_id)
        
        # Parse single turn ID format: "071:15"
        elif ':' in item_id:
            interview_id, turn_num = item_id.split(':', 1)
            interview_id = interview_id.zfill(3)  # Pad to 3 digits
            
            interview = self._load_interview(interview_id)
            if not interview:
                return {"error": f"Interview {interview_id} not found"}
            
            # Find the turn
            for turn in interview['turns']:
                if turn['turn_id'] == item_id:
                    # Add interview context
                    turn_with_context = turn.copy()
                    turn_with_context['interview_location'] = interview['metadata'].get('location', 'Unknown')
                    turn_with_context['interview_organization'] = interview['metadata'].get('organization', 'Unknown')
                    return turn_with_context
            
            return {"error": f"Turn {item_id} not found"}
        
        else:
            # It's an interview ID
            interview_id = item_id.zfill(3)
            interview = self._load_interview(interview_id)
            if interview:
                return {
                    "interview_id": interview['interview_id'],
                    "location": interview['metadata'].get('location', 'Unknown'),
                    "organization": interview['metadata'].get('organization', 'Unknown'),
                    "date": interview['metadata'].get('date', 'Unknown'),
                    "total_turns": interview['total_turns'],
                    "interviewers": interview['metadata'].get('interviewers', 'Unknown')
                }
            else:
                return {"error": f"Interview {interview_id} not found"}
    
    def _get_turn_range(self, interview_id: str, start_turn: int, end_turn: Optional[int]) -> Dict:
        """Get a range of turns from an interview"""
        interview = self._load_interview(interview_id)
        if not interview:
            return {"error": f"Interview {interview_id} not found"}
        
        # Set end_turn to max if not specified
        if end_turn is None:
            end_turn = len(interview['turns'])
        
        # Find turns in range
        range_turns = []
        for turn in interview['turns']:
            if start_turn <= turn['turn_number'] <= end_turn:
                turn_with_context = turn.copy()
                turn_with_context['interview_location'] = interview['metadata'].get('location', 'Unknown')
                turn_with_context['interview_organization'] = interview['metadata'].get('organization', 'Unknown')
                range_turns.append(turn_with_context)
        
        return {
            "range": f"{interview_id}:{start_turn}-{end_turn}",
            "interview_id": interview_id,
            "interview_location": interview['metadata'].get('location', 'Unknown'),
            "interview_organization": interview['metadata'].get('organization', 'Unknown'),
            "total_turns_in_range": len(range_turns),
            "turns": range_turns
        }
    
    def _get_whole_interview_as_turns(self, interview_id: str) -> Dict:
        """Get all turns from an interview in the same format as ranges"""
        interview = self._load_interview(interview_id)
        if not interview:
            return {"error": f"Interview {interview_id} not found"}
        
        # Add context to all turns
        all_turns = []
        for turn in interview['turns']:
            turn_with_context = turn.copy()
            turn_with_context['interview_location'] = interview['metadata'].get('location', 'Unknown')
            turn_with_context['interview_organization'] = interview['metadata'].get('organization', 'Unknown')
            all_turns.append(turn_with_context)
        
        return {
            "range": f"{interview_id}:all",
            "interview_id": interview_id,
            "interview_location": interview['metadata'].get('location', 'Unknown'),
            "interview_organization": interview['metadata'].get('organization', 'Unknown'),
            "date": interview['metadata'].get('date', 'Unknown'),
            "interviewers": interview['metadata'].get('interviewers', 'Unknown'),
            "total_turns_in_range": len(all_turns),
            "turns": all_turns
        }
    
    def search(self, query: str, interview_id: str = None, limit: int = 10) -> List[Dict]:
        """Search for text across interviews"""
        results = []
        query_lower = query.lower()
        
        # Determine which interviews to search
        if interview_id:
            interview_ids = [interview_id.zfill(3)]
        else:
            interview_ids = list(self.interview_files.keys())
        
        for iid in interview_ids:
            interview = self._load_interview(iid)
            if not interview:
                continue
            
            for turn in interview['turns']:
                if query_lower in turn['text'].lower():
                    result = {
                        "turn_id": turn['turn_id'],
                        "speaker": turn['speaker'],
                        "text": turn['text'][:200] + "..." if len(turn['text']) > 200 else turn['text'],
                        "word_count": turn['word_count'],
                        "interview_location": interview['metadata'].get('location', 'Unknown'),
                        "interview_organization": interview['metadata'].get('organization', 'Unknown')
                    }
                    results.append(result)
                    
                    if len(results) >= limit:
                        return results
        
        return results
    
    def list_interviews(self) -> List[Dict]:
        """List all available interviews"""
        interviews = []
        
        for interview_id in sorted(self.interview_files.keys()):
            interview = self._load_interview(interview_id)
            if interview:
                interviews.append({
                    "interview_id": interview['interview_id'],
                    "location": interview['metadata'].get('location', 'Unknown'),
                    "organization": interview['metadata'].get('organization', 'Unknown'),
                    "turns": interview['total_turns']
                })
        
        return interviews
    
    def list_turns(self, interview_id: str, speaker: str = None, min_words: int = None) -> List[str]:
        """List turn IDs from a specific interview"""
        interview_id = interview_id.zfill(3)
        interview = self._load_interview(interview_id)
        
        if not interview:
            return []
        
        turn_ids = []
        for turn in interview['turns']:
            # Filter by speaker if specified
            if speaker and turn['speaker'].upper() != speaker.upper():
                continue
            
            # Filter by minimum words if specified
            if min_words and turn['word_count'] < min_words:
                continue
            
            turn_ids.append(turn['turn_id'])
        
        return turn_ids

def main():
    parser = argparse.ArgumentParser(description='Uruguay Interview CLI')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Get command
    get_parser = subparsers.add_parser('get', help='Get turn or interview by ID')
    get_parser.add_argument('id', help='Turn ID (e.g., 071:15) or Interview ID (e.g., 071)')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search for text')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--interview', help='Limit to specific interview')
    search_parser.add_argument('--limit', type=int, default=10, help='Max results')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List interviews or turns')
    list_parser.add_argument('--interview', help='List turns from specific interview')
    list_parser.add_argument('--speaker', help='Filter by speaker')
    list_parser.add_argument('--min-words', type=int, help='Minimum word count')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = UruguayCLI()
    
    if args.command == 'get':
        result = cli.get(args.id)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.command == 'search':
        results = cli.search(args.query, args.interview, args.limit)
        print(json.dumps(results, indent=2, ensure_ascii=False))
    
    elif args.command == 'list':
        if args.interview:
            results = cli.list_turns(args.interview, args.speaker, args.min_words)
        else:
            results = cli.list_interviews()
        print(json.dumps(results, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()