"""
Simple automatic interview parser
Extracts turns with stable IDs from text interview files
"""

import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class InterviewParser:
    def __init__(self):
        self.speaker_pattern = re.compile(r'^\[([A-Z]{1,3})\]\s*(?:\([^)]+\))?\s*$')
        self.metadata_patterns = {
            'id': re.compile(r'Id\s+[Aa]genda:\s*(\d+)', re.IGNORECASE),
            'organization': re.compile(r'[Oo]rganización?:\s*(.+)', re.IGNORECASE),
            'location': re.compile(r'[Ll]ocalidad:\s*(.+)', re.IGNORECASE),
            'date': re.compile(r'[Ff]echa.*:\s*(\d{2}/\d{2}/\d{4})', re.IGNORECASE),
            'interviewers': re.compile(r'[Ee]ntrevistador(?:es)?:\s*(.+)', re.IGNORECASE),
            'interviewees': re.compile(r'[Ee]ntrevistados?:\s*(.+)', re.IGNORECASE)
        }
    
    def parse_file(self, filepath: Path) -> Dict:
        """Parse a single interview text file into structured JSON"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        # Extract metadata from header
        metadata = self._extract_metadata(lines)
        
        # Extract conversation turns
        turns = self._extract_turns(lines, metadata['interview_id'])
        
        return {
            'interview_id': metadata['interview_id'],
            'metadata': metadata,
            'turns': turns,
            'parsed_at': datetime.now().isoformat(),
            'total_turns': len(turns)
        }
    
    def _extract_metadata(self, lines: List[str]) -> Dict:
        """Extract metadata from the interview header"""
        metadata = {}
        header_text = '\n'.join(lines[:30])  # Look in first 30 lines
        
        for key, pattern in self.metadata_patterns.items():
            match = pattern.search(header_text)
            if match:
                metadata[key] = match.group(1).strip()
        
        # Extract interview ID from filename pattern if not found
        if 'id' not in metadata:
            # Look for the timestamp line like "20250528 1130 71"
            for line in lines:
                timestamp_match = re.search(r'(\d{8}\s+\d{4}\s+(\d+))', line.strip())
                if timestamp_match:
                    metadata['id'] = timestamp_match.group(2)
                    metadata['timestamp_line'] = timestamp_match.group(1)
                    break
        
        # Standardize ID
        interview_id = metadata.get('id', 'unknown')
        metadata['interview_id'] = f"{interview_id:0>3}" if interview_id.isdigit() else interview_id
        
        return metadata
    
    def _extract_turns(self, lines: List[str], interview_id: str) -> List[Dict]:
        """Extract conversation turns with stable IDs"""
        turns = []
        current_speaker = None
        current_text = []
        turn_number = 0
        
        # Find where conversation starts (after metadata)
        conversation_start = self._find_conversation_start(lines)
        
        for i, line in enumerate(lines[conversation_start:], conversation_start):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Check if this line starts a new speaker turn
            speaker_match = self.speaker_pattern.match(line)
            
            if speaker_match:
                # Save previous turn if exists
                if current_speaker and current_text:
                    turn_number += 1
                    turns.append(self._create_turn(
                        interview_id, turn_number, current_speaker, 
                        '\n'.join(current_text), i - len(current_text)
                    ))
                
                # Start new turn
                current_speaker = speaker_match.group(1)
                current_text = []
            
            else:
                # This line is part of the current speaker's text
                if current_speaker:  # Only collect text if we have a speaker
                    current_text.append(line)
        
        # Don't forget the last turn
        if current_speaker and current_text:
            turn_number += 1
            turns.append(self._create_turn(
                interview_id, turn_number, current_speaker, 
                '\n'.join(current_text), len(lines) - len(current_text)
            ))
        
        return turns
    
    def _find_conversation_start(self, lines: List[str]) -> int:
        """Find where the actual conversation starts (after metadata)"""
        for i, line in enumerate(lines):
            if self.speaker_pattern.match(line.strip()):
                return i
        return 0  # Fallback to beginning if no speakers found
    
    def _create_turn(self, interview_id: str, turn_number: int, 
                    speaker: str, text: str, line_number: int) -> Dict:
        """Create a standardized turn object"""
        turn_id = f"{interview_id}:{turn_number:0>2}"
        
        return {
            'turn_id': turn_id,
            'interview_id': interview_id,
            'turn_number': turn_number,
            'speaker': speaker,
            'text': text.strip(),
            'source_line': line_number,
            'word_count': len(text.split()),
            'char_count': len(text.strip())
        }

def test_parser():
    """Test the parser on a sample file"""
    parser = InterviewParser()
    
    # Test on interview 071
    test_file = Path("../data/processed/interviews_txt/20250528_1130_071.txt")
    
    if test_file.exists():
        result = parser.parse_file(test_file)
        
        print(f"Interview ID: {result['interview_id']}")
        print(f"Total turns: {result['total_turns']}")
        print(f"Metadata: {json.dumps(result['metadata'], indent=2)}")
        print("\nFirst 3 turns:")
        
        for turn in result['turns'][:3]:
            print(f"\n[{turn['turn_id']}] {turn['speaker']}: {turn['text'][:100]}...")
    
    else:
        print(f"Test file not found: {test_file}")

if __name__ == "__main__":
    test_parser()