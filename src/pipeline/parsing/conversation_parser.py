"""
Conversation parser for extracting structured turns from interview text.
"""
import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ConversationTurn:
    """Represents a single turn in a conversation."""
    turn_number: int
    speaker: str
    speaker_id: Optional[str]
    text: str
    word_count: int
    start_line: int
    end_line: int


class ConversationParser:
    """Parses raw interview text into structured conversation turns."""
    
    # Common speaker patterns in interview transcripts
    SPEAKER_PATTERNS = [
        r'^\[([A-Z]{1,4})\]$',  # [AM], [CR], [JP], etc.
        r'^([A-Z]{1,4}):\s*$',  # AM:, CR:, JP:
        r'^([A-Za-z]+\s*\d*):\s*$',  # Entrevistador:, Participante1:
        r'^\[([A-Za-z]+(?:\s+\d+)?)\]$',  # [Entrevistador], [Participante 1]
    ]
    
    # Patterns to exclude (often metadata or timestamps)
    EXCLUDE_PATTERNS = [
        r'^\d{8}\s+\d{4}\s+\d+$',  # Timestamp patterns like "20250528 0900 58"
        r'^Id Agenda:',
        r'^ORGANIZACIÓN:',
        r'^Localidad:',
        r'^Fecha de la entrevista:',
        r'^Entrevistadores:',
        r'^Entrevistados:',
        r'^Sobre la institución:',
        r'^Transcripción hecha por',
        r'^Entregada el',
        r'^_{3,}$',  # Lines with just underscores
    ]
    
    def parse_conversation(self, raw_text: str) -> List[ConversationTurn]:
        """
        Parse raw interview text into structured conversation turns.
        
        Args:
            raw_text: Raw interview transcript text
            
        Returns:
            List of ConversationTurn objects
        """
        turns = []
        lines = raw_text.split('\n')
        
        current_speaker = None
        current_speaker_id = None
        current_text_lines = []
        current_start_line = None
        turn_number = 0
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            
            # Skip empty lines and excluded patterns
            if not line or self._should_exclude_line(line):
                continue
            
            # Check if this line indicates a new speaker
            speaker_match = self._extract_speaker(line)
            
            if speaker_match:
                # Save previous turn if we have one
                if current_speaker and current_text_lines:
                    turn_number += 1
                    turn_text = ' '.join(current_text_lines).strip()
                    if turn_text:  # Only save if there's actual content
                        turns.append(ConversationTurn(
                            turn_number=turn_number,
                            speaker=current_speaker,
                            speaker_id=current_speaker_id,
                            text=turn_text,
                            word_count=len(turn_text.split()),
                            start_line=current_start_line,
                            end_line=line_num - 1
                        ))
                
                # Start new turn
                current_speaker = speaker_match['speaker']
                current_speaker_id = speaker_match['speaker_id']
                current_text_lines = []
                current_start_line = line_num
                
            else:
                # This is content for the current speaker
                if current_speaker:
                    current_text_lines.append(line)
        
        # Don't forget the last turn
        if current_speaker and current_text_lines:
            turn_number += 1
            turn_text = ' '.join(current_text_lines).strip()
            if turn_text:
                turns.append(ConversationTurn(
                    turn_number=turn_number,
                    speaker=current_speaker,
                    speaker_id=current_speaker_id,
                    text=turn_text,
                    word_count=len(turn_text.split()),
                    start_line=current_start_line,
                    end_line=len(lines) - 1
                ))
        
        logger.info(f"Parsed {len(turns)} conversation turns")
        return turns
    
    def _extract_speaker(self, line: str) -> Optional[Dict[str, str]]:
        """
        Extract speaker information from a line.
        
        Returns:
            Dict with 'speaker' and 'speaker_id' keys, or None if no speaker found
        """
        for pattern in self.SPEAKER_PATTERNS:
            match = re.match(pattern, line.strip())
            if match:
                speaker_raw = match.group(1)
                
                # Determine speaker type and ID
                speaker_id = None
                speaker = speaker_raw
                
                # Handle numbered participants (e.g., "Participante 1")
                if ' ' in speaker_raw:
                    parts = speaker_raw.split()
                    if len(parts) == 2 and parts[1].isdigit():
                        speaker = parts[0]
                        speaker_id = parts[1]
                
                # Normalize speaker names
                speaker = self._normalize_speaker_name(speaker)
                
                return {
                    'speaker': speaker,
                    'speaker_id': speaker_id
                }
        
        return None
    
    def _normalize_speaker_name(self, speaker: str) -> str:
        """Normalize speaker names for consistency."""
        speaker_lower = speaker.lower()
        
        # Map common variations (keep Spanish terms)
        if speaker_lower in ['entrevistador', 'ent', 'e']:
            return 'Entrevistador'
        elif speaker_lower in ['entrevistado', 'participante', 'p']:
            return 'Participante'
        elif speaker_lower in ['moderador', 'mod', 'm']:
            return 'Moderador'
        else:
            # Keep original for specific initials like AM, CR, JP
            return speaker.upper()
    
    def _should_exclude_line(self, line: str) -> bool:
        """Check if a line should be excluded from parsing."""
        for pattern in self.EXCLUDE_PATTERNS:
            if re.match(pattern, line):
                return True
        return False
    
    def get_conversation_summary(self, turns: List[ConversationTurn]) -> Dict[str, Any]:
        """Generate summary statistics for a conversation."""
        if not turns:
            return {}
        
        # Count speakers
        speakers = {}
        total_words = 0
        
        for turn in turns:
            speaker_key = f"{turn.speaker}_{turn.speaker_id}" if turn.speaker_id else turn.speaker
            if speaker_key not in speakers:
                speakers[speaker_key] = {
                    'speaker': turn.speaker,
                    'speaker_id': turn.speaker_id,
                    'turn_count': 0,
                    'word_count': 0
                }
            
            speakers[speaker_key]['turn_count'] += 1
            speakers[speaker_key]['word_count'] += turn.word_count
            total_words += turn.word_count
        
        return {
            'total_turns': len(turns),
            'total_words': total_words,
            'unique_speakers': len(speakers),
            'speakers': list(speakers.values()),
            'avg_words_per_turn': total_words / len(turns) if turns else 0
        }


if __name__ == "__main__":
    # Test with sample text
    sample_text = """
Id Agenda: 58

ORGANIZACIÓN: Directiva del Centro Esperanza Young (CEY)

[AM]
Nos han contactado a ver si podríamos recibir desde Paysandú también
porque en la zona es el único centro referente que hay.

[CR]
¿Y hace cuánto que está el centro?

[JP]
25 años. Sí, el año pasado festejamos 25 años.

[CR]
Tanto tiempo que están en los territorios.

[JP]
Exacto. Por algo hace tanto que están y se mantienen.
"""
    
    parser = ConversationParser()
    turns = parser.parse_conversation(sample_text)
    
    print(f"Parsed {len(turns)} turns:")
    for turn in turns:
        print(f"Turn {turn.turn_number} - {turn.speaker}: {turn.text[:50]}...")
    
    summary = parser.get_conversation_summary(turns)
    print(f"\nSummary: {summary}")