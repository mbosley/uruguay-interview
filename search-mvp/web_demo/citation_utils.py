"""
Utilities for parsing and handling citations in research output
"""

import re
import json
import os
from typing import Dict, List, Tuple, Optional

class CitationParser:
    """Parse and handle interview citations"""
    
    # Pattern to match citations like "071:23" or "084:45-50"
    CITATION_PATTERN = r'\b(\d{3}):(\d+)(?:-(\d+))?\b'
    
    def __init__(self, corpus_path: str):
        self.corpus = self._load_corpus(corpus_path)
        self.enriched_data = self._load_enriched_data(corpus_path)
    
    def _load_corpus(self, base_path: str) -> Dict:
        """Load the enriched corpus data"""
        enriched_path = os.path.join(base_path, "../data/processed/enriched/_enriched_corpus_summary.json")
        try:
            with open(enriched_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load enriched corpus: {e}")
            return {}
    
    def _load_enriched_data(self, base_path: str) -> Dict:
        """Load individual enriched interview files"""
        enriched_dir = os.path.join(base_path, "../data/processed/enriched")
        enriched_data = {}
        
        try:
            for filename in os.listdir(enriched_dir):
                if filename.startswith("interview_") and filename.endswith("_enriched.json"):
                    interview_id = filename.split('_')[1]
                    with open(os.path.join(enriched_dir, filename), 'r', encoding='utf-8') as f:
                        enriched_data[interview_id] = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load enriched interviews: {e}")
        
        return enriched_data
    
    def parse_citations(self, text: str) -> List[Dict]:
        """Extract all citations from text"""
        citations = []
        
        for match in re.finditer(self.CITATION_PATTERN, text):
            interview_id = match.group(1)
            start_turn = int(match.group(2))
            end_turn = int(match.group(3)) if match.group(3) else start_turn
            
            citations.append({
                'full_citation': match.group(0),
                'interview_id': interview_id,
                'start_turn': start_turn,
                'end_turn': end_turn,
                'start_pos': match.start(),
                'end_pos': match.end()
            })
        
        return citations
    
    def get_turn_preview(self, interview_id: str, turn_num: int, max_length: int = 200) -> Optional[Dict]:
        """Get a preview of a specific turn"""
        try:
            if interview_id in self.enriched_data:
                interview = self.enriched_data[interview_id]
                
                # Find the turn
                for turn in interview.get('turns', []):
                    if turn.get('turn_number') == turn_num:
                        text = turn.get('text', '')
                        speaker = turn.get('speaker', 'Unknown')
                        
                        # Truncate if needed
                        if len(text) > max_length:
                            text = text[:max_length] + "..."
                        
                        return {
                            'speaker': speaker,
                            'text': text,
                            'turn_number': turn_num,
                            'themes': turn.get('themes', []),
                            'tags': turn.get('tags', [])
                        }
        except Exception as e:
            print(f"Error getting turn preview: {e}")
        
        return None
    
    def get_interview_summary(self, interview_id: str) -> Optional[Dict]:
        """Get the enriched summary for an interview"""
        try:
            if interview_id in self.enriched_data:
                interview = self.enriched_data[interview_id]
                return {
                    'id': interview_id,
                    'summary': interview.get('interview_summary', {}),
                    'metadata': interview.get('metadata', {}),
                    'themes': interview.get('themes', []),
                    'key_quotes': interview.get('key_quotes', [])
                }
        except Exception as e:
            print(f"Error getting interview summary: {e}")
        
        return None
    
    def format_text_with_citations(self, text: str) -> str:
        """Convert citations in text to HTML with data attributes"""
        citations = self.parse_citations(text)
        
        # Sort by position (reverse) to replace from end to start
        citations.sort(key=lambda x: x['start_pos'], reverse=True)
        
        formatted_text = text
        for citation in citations:
            preview = self.get_turn_preview(citation['interview_id'], citation['start_turn'])
            
            if preview:
                # Create HTML span with data attributes
                replacement = (
                    f'<span class="citation" '
                    f'data-interview="{citation["interview_id"]}" '
                    f'data-turn="{citation["start_turn"]}" '
                    f'data-preview="{preview["text"][:100]}" '
                    f'data-speaker="{preview["speaker"]}">'
                    f'{citation["full_citation"]}'
                    f'</span>'
                )
            else:
                # Citation without preview
                replacement = f'<span class="citation-no-preview">{citation["full_citation"]}</span>'
            
            formatted_text = (
                formatted_text[:citation['start_pos']] + 
                replacement + 
                formatted_text[citation['end_pos']:]
            )
        
        return formatted_text