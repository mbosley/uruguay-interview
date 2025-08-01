"""
Simple in-memory search engine for interview corpus
Provides get, search, and list commands for agent exploration
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import defaultdict

class InterviewSearchEngine:
    """Fast in-memory search for structured interview data"""
    
    def __init__(self):
        self.corpus = None
        self.interviews = {}  # interview_id -> interview data
        self.turns = {}      # turn_id -> turn data  
        self.text_index = defaultdict(set)  # word -> {turn_ids}
        self.speaker_index = defaultdict(set)  # speaker -> {turn_ids}
        self.interview_index = defaultdict(set)  # interview_id -> {turn_ids}
        self.loaded = False
    
    def load_corpus(self, corpus_file: Path = None):
        """Load the interview corpus into memory"""
        if corpus_file is None:
            corpus_file = Path("../data/processed/structured/_corpus.json")
        
        if not corpus_file.exists():
            raise FileNotFoundError(f"Corpus file not found: {corpus_file}")
        
        print(f"📚 Loading corpus from {corpus_file}...")
        
        with open(corpus_file, 'r', encoding='utf-8') as f:
            self.corpus = json.load(f)
        
        # Build indices
        self._build_indices()
        self.loaded = True
        
        print(f"✅ Loaded {len(self.interviews)} interviews, {len(self.turns)} turns")
    
    def _build_indices(self):
        """Build search indices for fast lookup"""
        for interview in self.corpus['interviews']:
            interview_id = interview['interview_id']
            self.interviews[interview_id] = interview
            
            for turn in interview['turns']:
                turn_id = turn['turn_id']
                self.turns[turn_id] = turn
                
                # Index by interview
                self.interview_index[interview_id].add(turn_id)
                
                # Index by speaker
                speaker = turn['speaker']
                self.speaker_index[speaker].add(turn_id)
                
                # Index by words (simple tokenization)
                text = turn['text'].lower()
                words = re.findall(r'\b\w+\b', text)
                for word in words:
                    self.text_index[word].add(turn_id)
    
    def get(self, item_id: str) -> Optional[Dict]:
        """Get a specific turn or interview by ID"""
        if not self.loaded:
            raise RuntimeError("Corpus not loaded. Call load_corpus() first.")
        
        # Try as turn ID first
        if item_id in self.turns:
            return self.turns[item_id]
        
        # Try as interview ID
        if item_id in self.interviews:
            return self.interviews[item_id]
        
        return None
    
    def search(self, query: str, in_interview: str = None, 
               speaker: str = None, limit: int = 20, mode: str = "any") -> List[Dict]:
        """Search for text across all turns
        
        Args:
            query: Search terms (multiple words supported)
            in_interview: Filter to specific interview ID
            speaker: Filter to specific speaker
            limit: Maximum results to return
            mode: "any" (OR search - default) or "all" (AND search)
        """
        if not self.loaded:
            raise RuntimeError("Corpus not loaded. Call load_corpus() first.")
        
        # Simple word-based search
        query_words = re.findall(r'\b\w+\b', query.lower())
        
        if not query_words:
            return []
        
        # Find turns based on search mode
        if mode == "all":
            # AND search - turns must contain ALL query words
            matching_turns = None
            for word in query_words:
                word_matches = self.text_index.get(word, set())
                if matching_turns is None:
                    matching_turns = word_matches.copy()
                else:
                    matching_turns &= word_matches
        else:
            # OR search (default) - turns containing ANY query word
            matching_turns = set()
            for word in query_words:
                word_matches = self.text_index.get(word, set())
                matching_turns |= word_matches
        
        if not matching_turns:
            return []
        
        # Apply filters
        if in_interview:
            interview_turns = self.interview_index.get(in_interview, set())
            matching_turns &= interview_turns
        
        if speaker:
            speaker_turns = self.speaker_index.get(speaker.upper(), set())
            matching_turns &= speaker_turns
        
        # Return turn data, sorted by interview and turn number
        results = []
        for turn_id in matching_turns:
            turn_data = self.turns[turn_id].copy()
            
            # Add interview metadata for context
            interview_id = turn_data['interview_id']
            interview = self.interviews[interview_id]
            turn_data['interview_location'] = interview['metadata'].get('location', 'Unknown')
            turn_data['interview_organization'] = interview['metadata'].get('organization', 'Unknown')
            
            results.append(turn_data)
        
        # Sort by interview ID and turn number
        results.sort(key=lambda x: (x['interview_id'], x['turn_number']))
        
        return results[:limit]
    
    def list_turns(self, interview_id: str = None, speaker: str = None, 
                   min_words: int = None, limit: int = 50) -> List[str]:
        """List turn IDs matching criteria"""
        if not self.loaded:
            raise RuntimeError("Corpus not loaded. Call load_corpus() first.")
        
        candidates = set(self.turns.keys())
        
        # Filter by interview
        if interview_id:
            if interview_id not in self.interview_index:
                return []
            candidates &= self.interview_index[interview_id]
        
        # Filter by speaker
        if speaker:
            speaker_upper = speaker.upper()
            if speaker_upper not in self.speaker_index:
                return []
            candidates &= self.speaker_index[speaker_upper]
        
        # Filter by minimum word count
        if min_words:
            filtered = set()
            for turn_id in candidates:
                if self.turns[turn_id]['word_count'] >= min_words:
                    filtered.add(turn_id)
            candidates = filtered
        
        # Sort and return
        sorted_turns = sorted(candidates, key=lambda tid: (
            self.turns[tid]['interview_id'], 
            self.turns[tid]['turn_number']
        ))
        
        return sorted_turns[:limit]
    
    def get_search_suggestions(self, query: str) -> Dict[str, Any]:
        """Provide search suggestions when no results are found"""
        query_words = re.findall(r'\b\w+\b', query.lower())
        suggestions = {
            "original_query": query,
            "query_words": query_words,
            "word_frequencies": {},
            "suggestions": []
        }
        
        # Check frequency of each word
        for word in query_words:
            count = len(self.text_index.get(word, set()))
            suggestions["word_frequencies"][word] = count
            
        # Generate suggestions based on word frequencies
        if all(count == 0 for count in suggestions["word_frequencies"].values()):
            suggestions["suggestions"].extend([
                "All search terms returned no matches",
                "Try searching in Spanish (citizens spoke Spanish)",
                "Check spelling, especially Spanish accents",
                "Try single words instead of phrases"
            ])
        elif all(count > 0 for count in suggestions["word_frequencies"].values()):
            # All words exist but not together
            suggestions["suggestions"].extend([
                f"Words exist separately but not together in any turn",
                f"Try searching for each word individually",
                f"Consider using related or broader terms"
            ])
            # Show which words are most/least common
            sorted_words = sorted(suggestions["word_frequencies"].items(), 
                                key=lambda x: x[1], reverse=True)
            suggestions["suggestions"].append(
                f"Most common: '{sorted_words[0][0]}' ({sorted_words[0][1]} turns)"
            )
            if len(sorted_words) > 1:
                suggestions["suggestions"].append(
                    f"Least common: '{sorted_words[-1][0]}' ({sorted_words[-1][1]} turns)"
                )
        else:
            # Some words found, some not
            found = [w for w, c in suggestions["word_frequencies"].items() if c > 0]
            not_found = [w for w, c in suggestions["word_frequencies"].items() if c == 0]
            suggestions["suggestions"].append(
                f"Found: {', '.join(found)}"
            )
            suggestions["suggestions"].append(
                f"Not found: {', '.join(not_found)}"
            )
            suggestions["suggestions"].append(
                "Try searching just for the found words"
            )
            
        return suggestions
    
    def get_stats(self) -> Dict:
        """Get corpus statistics"""
        if not self.loaded:
            return {"error": "Corpus not loaded"}
        
        # Speaker statistics
        speaker_counts = {speaker: len(turns) for speaker, turns in self.speaker_index.items()}
        
        # Interview statistics  
        interview_stats = []
        for interview_id, interview in self.interviews.items():
            stats = {
                'interview_id': interview_id,
                'location': interview['metadata'].get('location', 'Unknown'),
                'turns': interview['total_turns'],
                'organization': interview['metadata'].get('organization', 'Unknown')
            }
            interview_stats.append(stats)
        
        return {
            'total_interviews': len(self.interviews),
            'total_turns': len(self.turns),
            'total_unique_speakers': len(self.speaker_index),
            'speaker_distribution': dict(sorted(speaker_counts.items(), 
                                              key=lambda x: x[1], reverse=True)[:10]),
            'interviews': sorted(interview_stats, key=lambda x: x['interview_id'])
        }

# Simple CLI interface
def main():
    """Interactive CLI for testing"""
    engine = InterviewSearchEngine()
    
    try:
        engine.load_corpus()
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return
    
    print("\n🔍 Uruguay Interview Search")
    print("Commands: get <id>, search <query>, list [--interview <id>], stats, quit")
    
    while True:
        try:
            command = input("\n> ").strip()
            
            if command.lower() in ['quit', 'exit', 'q']:
                break
                
            parts = command.split()
            if not parts:
                continue
                
            cmd = parts[0].lower()
            
            if cmd == 'get' and len(parts) > 1:
                result = engine.get(parts[1])
                if result:
                    if 'turn_id' in result:  # It's a turn
                        print(f"[{result['turn_id']}] {result['speaker']}: {result['text'][:200]}...")
                    else:  # It's an interview
                        print(f"Interview {result['interview_id']}: {result['total_turns']} turns")
                        print(f"Location: {result['metadata'].get('location', 'Unknown')}")
                else:
                    print("❌ Not found")
            
            elif cmd == 'search' and len(parts) > 1:
                query = ' '.join(parts[1:])
                results = engine.search(query, limit=5)
                print(f"Found {len(results)} matches:")
                for result in results:
                    print(f"[{result['turn_id']}] {result['speaker']} ({result['interview_location']}): {result['text'][:100]}...")
            
            elif cmd == 'list':
                # Parse optional filters
                interview_filter = None
                if '--interview' in parts:
                    idx = parts.index('--interview')
                    if idx + 1 < len(parts):
                        interview_filter = parts[idx + 1]
                
                results = engine.list_turns(interview_id=interview_filter, limit=10)
                print(f"Found {len(results)} turns:")
                for turn_id in results:
                    turn = engine.get(turn_id)
                    print(f"  {turn_id}: {turn['speaker']} ({turn['word_count']} words)")
            
            elif cmd == 'stats':
                stats = engine.get_stats()
                print(f"📊 Corpus Statistics:")
                print(f"   Interviews: {stats['total_interviews']}")
                print(f"   Turns: {stats['total_turns']}")
                print(f"   Speakers: {stats['total_unique_speakers']}")
                print(f"   Top speakers: {list(stats['speaker_distribution'].items())[:5]}")
            
            else:
                print("❌ Unknown command. Try: get <id>, search <query>, list, stats, quit")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n👋 Goodbye!")

if __name__ == "__main__":
    main()