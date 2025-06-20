#!/usr/bin/env python3
"""
Generate complete annotated interview HTML from annotation data.
Generic version that works for any interview without manual customization.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

class InterviewHTMLGenerator:
    def __init__(self):
        # No hardcoded turns - will determine dynamically
        pass
        
    def load_annotation_data(self, filepath: str) -> Dict[str, Any]:
        """Load the annotation JSON data."""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def parse_transcript(self, transcript_text: str) -> List[Dict[str, str]]:
        """Parse transcript text into turns."""
        turns = []
        lines = transcript_text.strip().split('\n')
        current_speaker = None
        current_text = []
        speaker_map = {}  # Map abbreviations to full names
        
        # Find where the actual conversation starts
        in_conversation = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Skip metadata lines at the beginning
            if not in_conversation and any(marker in line for marker in ['ID:', 'ORGANIZACIÓN:', 'LOCALIDAD:', 'FECHA', 'Entrevistadores:', 'Entrevistados:', 'Hecha por:', 'Entregada:', 'Comisión']):
                continue
            
            # Detect speaker lines
            if '[' in line and ']' in line:
                in_conversation = True
                
                # Save previous turn if exists
                if current_speaker and current_text:
                    turns.append({
                        'speaker': current_speaker,
                        'text': ' '.join(current_text).strip()
                    })
                    current_text = []
                
                # Extract speaker info
                if line.strip() in ['[GM]', '[GB]', '[MHF]']:
                    # Just abbreviation - use map
                    abbrev = line.strip()[1:-1]
                    current_speaker = speaker_map.get(abbrev, abbrev)
                else:
                    # Full name with abbreviation
                    bracket_start = line.find('[')
                    bracket_end = line.find(']')
                    if bracket_start > 0:
                        name = line[:bracket_start].strip()
                        abbrev = line[bracket_start+1:bracket_end]
                        speaker_map[abbrev] = name
                        current_speaker = name
                    else:
                        current_speaker = line.strip()
            elif in_conversation and line:
                # This is content, not a speaker line
                current_text.append(line)
        
        # Don't forget the last turn
        if current_speaker and current_text:
            turns.append({
                'speaker': current_speaker,
                'text': ' '.join(current_text).strip()
            })
        
        return turns
    
    def merge_transcript_with_annotations(self, annotation_data: Dict[str, Any], transcript_turns: List[Dict[str, str]]):
        """Merge transcript text with annotation data."""
        ann_data = annotation_data.get('annotation_data', {})
        conv_analysis = ann_data.get('conversation_analysis', {})
        turns = conv_analysis.get('turns', [])
        
        # Merge consecutive turns from same speaker
        merged_transcript_turns = []
        current_merged = None
        
        for turn in transcript_turns:
            if current_merged is None:
                current_merged = {'speaker': turn['speaker'], 'text': turn['text']}
            elif current_merged['speaker'] == turn['speaker']:
                # Same speaker, merge the text
                current_merged['text'] += '\n\n' + turn['text']
            else:
                # Different speaker, save current and start new
                merged_transcript_turns.append(current_merged)
                current_merged = {'speaker': turn['speaker'], 'text': turn['text']}
        
        # Don't forget the last turn
        if current_merged:
            merged_transcript_turns.append(current_merged)
        
        # Merge transcript text into turn data
        for i, turn in enumerate(turns):
            if i < len(merged_transcript_turns):
                turn['speaker'] = merged_transcript_turns[i]['speaker']
                turn['content'] = merged_transcript_turns[i]['text']
                turn['turn_number'] = turn.get('turn_id', i + 1)
            else:
                # No transcript for this annotation
                turn['speaker'] = f'Speaker {i+1}'
                turn['content'] = '[Transcript not available for this turn]'
                turn['turn_number'] = turn.get('turn_id', i + 1)
    
    def determine_key_turns(self, turns: List[Dict[str, Any]]) -> set:
        """Dynamically determine key turns based on annotation data."""
        key_turns = set()
        
        for turn in turns:
            turn_id = turn.get('turn_id', turn.get('turn_number', 0))
            
            # Check functional significance
            func_analysis = turn.get('turn_analysis', {})
            func_confidence = func_analysis.get('function_confidence', 0)
            primary_func = func_analysis.get('primary_function', '')
            
            # Check emotional intensity
            emotional = turn.get('emotional_analysis', {})
            emotional_intensity = emotional.get('emotional_intensity', 0)
            
            # Check evidence quality
            evidence = turn.get('evidence_analysis', {})
            evidence_type = evidence.get('evidence_type', 'none')
            
            # Key turn criteria:
            # 1. High confidence problem identification or elaboration
            # 2. High emotional intensity
            # 3. Strong evidence present
            # 4. Explicit turn significance
            
            if (func_confidence > 0.85 and primary_func in ['problem_identification', 'elaboration', 'solution_proposal']) or \
               (emotional_intensity > 0.7) or \
               (evidence_type not in ['none', 'not_applicable']) or \
               ('key' in turn.get('turn_significance', '').lower()):
                key_turns.add(turn_id)
        
        # Always include first few turns
        key_turns.update([1, 2, 3])
        
        return key_turns
    
    def generate_turn_html(self, turn_num: int, message: Dict[str, Any], 
                          turn_analysis: Dict[str, Any], is_key: bool = False,
                          interviewers: List[str] = None) -> str:
        """Generate HTML for a single turn with all annotations."""
        speaker = message['speaker']
        text = message['text']
        
        # Determine if interviewer based on metadata
        if interviewers:
            is_interviewer = any(interviewer in speaker for interviewer in interviewers)
        else:
            # Fallback to common patterns
            is_interviewer = any(name in speaker.upper() for name in ['ENTREVISTADOR', 'INTERVIEWER', 'GM', 'GB'])
        
        speaker_class = 'interviewer' if is_interviewer else 'participant'
        
        # Determine if expanded by default (key turns)
        expanded_class = 'expanded' if is_key else 'collapsed'
        key_class = 'key-moment' if is_key else ''
        
        # Create preview text (first 60 chars)
        preview_text = text[:60] + ('...' if len(text) > 60 else '')
        
        # Build annotation grid
        annotations_html = self._build_annotations(turn_analysis)
        
        # Process text with emphasis from annotation data
        processed_text = self._process_text_with_quotes(text, turn_analysis)
        
        # Generate turn HTML
        turn_html = f'''
            <div class="turn {expanded_class} {key_class}" data-turn="{turn_num}">
                <div class="turn-header" onclick="toggleTurn(this)">
                    <span class="turn-number">TURN {turn_num}</span>
                    <div class="turn-preview">
                        <span class="speaker-badge {speaker_class}">{speaker.upper()}</span>
                        <span class="turn-preview-text">{preview_text}</span>
                    </div>
                    <span class="turn-expand-icon">⌄</span>
                </div>
                <div class="turn-content">
                    <div class="turn-content-inner">
                        <div class="speech-block">
                            <div class="speaker-name">{speaker}</div>
                            <div class="speech {speaker_class}">{processed_text}</div>
                        </div>
                        {annotations_html}
                    </div>
                </div>
            </div>
        '''
        return turn_html
    
    def _process_text_with_quotes(self, text: str, analysis: Dict[str, Any]) -> str:
        """Add emphasis spans based on annotation data."""
        # Look for high emotional intensity phrases
        emotional = analysis.get('emotional_analysis', {})
        if emotional.get('emotional_intensity', 0) > 0.8:
            # Could potentially highlight entire text or use NLP to find key phrases
            # For now, return as-is
            pass
        
        return text
    
    def _build_annotations(self, analysis: Dict[str, Any]) -> str:
        """Build the annotation grid HTML from analysis data."""
        if not analysis:
            return '<div class="minimal-annotation">No analysis available</div>'
        
        # Extract all dimensions
        functional = analysis.get('functional_analysis', {})
        content = analysis.get('content_analysis', {})
        emotional = analysis.get('emotional_analysis', {})
        evidence = analysis.get('evidence_analysis', {})
        uncertainty = analysis.get('uncertainty_analysis', {})
        
        # Check if this is a minimal turn
        if self._is_minimal_turn(functional, content, emotional, evidence, uncertainty):
            func_text = functional.get('primary_function', functional.get('function', 'Acknowledgment'))
            return f'<div class="minimal-annotation">Functional: {func_text}</div>'
        
        # Build full annotation grid
        annotations = []
        
        # Functional dimension
        if functional:
            primary_func = functional.get('primary_function', functional.get('function', 'Not specified'))
            confidence = functional.get('function_confidence', functional.get('confidence', 0))
            conf_text = f'<span class="confidence-tag">{int(confidence*100)}%</span>' if confidence > 0 else ''
            reasoning = functional.get('reasoning', '')
            annotations.append(f'''
                <div class="annotation-dimension functional">
                    <div class="dimension-label">
                        <span class="dimension-icon">🎯</span>
                        FUNCTIONAL
                    </div>
                    <div class="dimension-content">
                        {primary_func.replace('_', ' ').title()}
                        {conf_text}
                    </div>
                    <div class="dimension-detail">
                        {reasoning}
                    </div>
                </div>
            ''')
        
        # Content dimension
        if content and content.get('topics'):
            topics = ' • '.join(content.get('topics', []))
            geographic = ', '.join(content.get('geographic_scope', [])) if content.get('geographic_scope') else ''
            temporal = content.get('temporal_reference', '')
            detail_parts = [g for g in [geographic, temporal] if g]
            detail = ' | '.join(detail_parts) if detail_parts else ''
            annotations.append(f'''
                <div class="annotation-dimension content">
                    <div class="dimension-label">
                        <span class="dimension-icon">📄</span>
                        CONTENT
                    </div>
                    <div class="dimension-content">
                        {topics}
                    </div>
                    <div class="dimension-detail">
                        {detail}
                    </div>
                </div>
            ''')
        
        # Emotional dimension
        if emotional:
            valence = emotional.get('emotional_valence', emotional.get('valence', 'neutral'))
            intensity = emotional.get('emotional_intensity', 0)
            emotions = emotional.get('specific_emotions', [])
            if emotions:
                emotions_text = ', '.join(emotions)
            else:
                emotions_text = valence.replace('_', ' ').title()
            intensity_text = f'<span class="confidence-tag">{intensity}</span>' if intensity > 0 else ''
            narrative = emotional.get('emotional_narrative', '')
            annotations.append(f'''
                <div class="annotation-dimension emotional">
                    <div class="dimension-label">
                        <span class="dimension-icon">💭</span>
                        EMOTIONAL
                    </div>
                    <div class="dimension-content">
                        {emotions_text}
                        {intensity_text}
                    </div>
                    <div class="dimension-detail">
                        {narrative}
                    </div>
                </div>
            ''')
        
        # Evidence dimension
        if evidence and evidence.get('evidence_type', 'none') != 'none':
            ev_type = evidence.get('evidence_type', 'Not specified')
            specificity = evidence.get('specificity', '')
            narrative = evidence.get('evidence_narrative', '')
            if ev_type != 'none':
                annotations.append(f'''
                    <div class="annotation-dimension evidence">
                        <div class="dimension-label">
                            <span class="dimension-icon">📊</span>
                            EVIDENCE
                        </div>
                        <div class="dimension-content">
                            {ev_type.replace('_', ' ').title()}
                        </div>
                        <div class="dimension-detail">
                            {narrative if narrative and narrative != 'N/A' else specificity}
                        </div>
                    </div>
                ''')
        
        # Uncertainty dimension
        if uncertainty and uncertainty.get('coding_confidence', 1) < 0.8:
            confidence = uncertainty.get('coding_confidence', 0)
            ambiguous = ', '.join(uncertainty.get('ambiguous_aspects', []))
            notes = uncertainty.get('annotator_notes', '')
            annotations.append(f'''
                <div class="annotation-dimension uncertainty">
                    <div class="dimension-label">
                        <span class="dimension-icon">❓</span>
                        UNCERTAINTY
                    </div>
                    <div class="dimension-content">
                        Confidence: {confidence:.1f}
                    </div>
                    <div class="dimension-detail">
                        {ambiguous if ambiguous else notes}
                    </div>
                </div>
            ''')
        
        if annotations:
            return f'<div class="annotation-grid">{" ".join(annotations)}</div>'
        else:
            return '<div class="minimal-annotation">No detailed analysis available</div>'
    
    def _is_minimal_turn(self, *analyses) -> bool:
        """Check if this is a minimal turn (like 'Ajá' or 'Claro')."""
        for analysis in analyses:
            if analysis and any(analysis.values()):
                # Check if it's just a simple acknowledgment
                if isinstance(analysis, dict):
                    func = analysis.get('primary_function', analysis.get('function', '')).lower()
                    if func in ['acknowledgment', 'minimal_acknowledgment', 'echo_confirmation', 'echo']:
                        return True
        return False
    
    def generate_complete_html(self, annotation_data: Dict[str, Any], output_path: str):
        """Generate the complete HTML file."""
        # Navigate to the actual annotation data
        ann_data = annotation_data.get('annotation_data', {})
        
        # Extract interview metadata
        metadata = ann_data.get('interview_metadata', {})
        interview_id = metadata.get('interview_id', 'Unknown')
        location = f"{metadata.get('municipality', 'Unknown')}, {metadata.get('department', 'Unknown')}"
        date = metadata.get('date', 'Unknown')
        duration = metadata.get('duration_minutes', 0)
        interviewers = metadata.get('interviewer_ids', [])
        
        # Extract conversation analysis
        conv_analysis = ann_data.get('conversation_analysis', {})
        turns = conv_analysis.get('turns', [])
        
        # Determine key turns dynamically
        key_turns = self.determine_key_turns(turns)
        
        # Extract synthesis data
        interview_synthesis = {
            'analytical_synthesis': ann_data.get('analytical_synthesis', {}),
            'narrative_features': ann_data.get('narrative_features', {}),
            'key_priorities': self._extract_priority_list(ann_data.get('priority_analysis', {})),
            'key_narratives': ann_data.get('key_narratives', {})
        }
        
        # Generate turns HTML
        turns_html = []
        for turn in turns:
            turn_num = turn.get('turn_number', turn.get('turn_id', 0))
            message = {
                'speaker': turn.get('speaker', 'Unknown'),
                'text': turn.get('content', '')
            }
            # Extract all turn analyses
            turn_analysis = {
                'functional_analysis': turn.get('turn_analysis', {}),
                'content_analysis': turn.get('content_analysis', {}),
                'emotional_analysis': turn.get('emotional_analysis', {}),
                'evidence_analysis': turn.get('evidence_analysis', {}),
                'uncertainty_analysis': turn.get('uncertainty_tracking', {})
            }
            is_key = turn_num in key_turns
            turn_html = self.generate_turn_html(turn_num, message, turn_analysis, is_key, interviewers)
            turns_html.append(turn_html)
        
        # Generate complete HTML
        html_template = self._get_html_template()
        html_content = html_template.format(
            interview_id=interview_id,
            location=location,
            date=date,
            duration=duration,
            turns_html=''.join(turns_html),
            total_turns=len(turns),
            expanded_count=len(key_turns),
            priorities=self._extract_priorities(interview_synthesis),
            key_insight=self._extract_key_insight(interview_synthesis),
            narrative_summary=self._extract_narrative(interview_synthesis),
            memorable_quotes=self._extract_quotes(interview_synthesis)
        )
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Generated HTML file: {output_path}")
    
    def _extract_priority_list(self, priority_analysis: Dict[str, Any]) -> List[str]:
        """Extract priority list from priority analysis."""
        priorities = []
        
        # Extract national priorities
        national = priority_analysis.get('national_priorities', [])
        for p in national[:3]:  # Top 3 national
            priorities.append(p.get('theme', ''))
            
        # Extract local priorities
        local = priority_analysis.get('local_community_priorities', [])
        for p in local[:2]:  # Top 2 local
            priorities.append(p.get('theme', ''))
            
        return priorities
    
    def _extract_priorities(self, synthesis: Dict[str, Any]) -> str:
        """Extract priorities from synthesis."""
        priorities = synthesis.get('key_priorities', [])
        
        priority_html = []
        for i, priority in enumerate(priorities[:5], 1):
            priority_html.append(f'''
                <div class="priority-item">
                    <span class="priority-rank">{i}</span>
                    <span class="priority-name">{priority}</span>
                </div>
            ''')
        
        return '\n'.join(priority_html)
    
    def _extract_key_insight(self, synthesis: Dict[str, Any]) -> str:
        """Extract key insight from synthesis."""
        analytical = synthesis.get('analytical_synthesis', {})
        
        # Look for tensions/contradictions first
        tensions = analytical.get('tensions_contradictions', '')
        if tensions and len(tensions) > 50:
            return tensions
        
        # Then connections to broader themes
        connections = analytical.get('connections_to_broader_themes', '')
        if connections and len(connections) > 50:
            return connections
        
        # Default to first narrative feature
        narrative = synthesis.get('narrative_features', {})
        return narrative.get('narrative_confidence', 'Interview reveals complex perspectives on societal challenges.')
    
    def _extract_narrative(self, synthesis: Dict[str, Any]) -> str:
        """Extract narrative summary from synthesis."""
        narrative = synthesis.get('narrative_features', {})
        
        # Try to construct from available data
        frame = narrative.get('dominant_frame', '')
        frame_narrative = narrative.get('frame_narrative', '')
        
        if frame_narrative:
            return frame_narrative
        elif frame:
            return f"The conversation is framed through a {frame} perspective."
        else:
            return "The interview explores personal experiences and societal concerns."
    
    def _extract_quotes(self, synthesis: Dict[str, Any]) -> str:
        """Extract memorable quotes for emphasis."""
        key_narratives = synthesis.get('key_narratives', {})
        quotes = key_narratives.get('memorable_quotes', [])
        
        if quotes:
            quote_html = []
            for quote in quotes[:3]:  # Limit to 3 quotes
                quote_html.append(f'<blockquote class="memorable-quote">"{quote}"</blockquote>')
            return '\n'.join(quote_html)
        return ''
    
    def _get_html_template(self) -> str:
        """Return the HTML template."""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interview {interview_id} — {location}</title>
    <link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,300;0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        :root {{
            --background: #FAFAF8;
            --surface: #FFFFFF;
            --surface-secondary: #F8F6F3;
            --text-primary: #1A1816;
            --text-secondary: #4A453E;
            --text-muted: #8A847A;
            --interviewer: #1E5A8E;
            --participant: #8B4513;
            --accent: #DC2626;
            --accent-light: #FEE2E2;
            --function-color: #1E5A8E;
            --content-color: #059669;
            --emotion-color: #7C3AED;
            --evidence-color: #DC2626;
            --uncertainty-color: #F59E0B;
            --border: #E5E2DC;
            --shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
        }}
        
        body {{
            background: var(--background);
            color: var(--text-primary);
            font-family: 'Newsreader', Georgia, serif;
            font-size: 17px;
            line-height: 1.7;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }}
        
        /* Header */
        .header {{
            background: var(--surface);
            border-bottom: 1px solid var(--border);
            padding: 1.5rem 2rem;
        }}
        
        .header-content {{
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        }}
        
        .header h1 {{
            font-family: 'Inter', sans-serif;
            font-size: 1.125rem;
            font-weight: 500;
            color: var(--text-primary);
            letter-spacing: -0.01em;
        }}
        
        .header-meta {{
            display: flex;
            gap: 1.5rem;
            font-family: 'Inter', sans-serif;
            font-size: 0.875rem;
            color: var(--text-muted);
        }}
        
        /* Analysis Section */
        .analysis-section {{
            background: var(--surface);
            padding: 4rem 2rem;
            border-bottom: 1px solid var(--border);
        }}
        
        .analysis-content {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .analysis-header {{
            margin-bottom: 3rem;
        }}
        
        .analysis-title {{
            font-size: 2.25rem;
            font-weight: 500;
            line-height: 1.2;
            margin-bottom: 1.5rem;
            color: var(--text-primary);
            max-width: 800px;
        }}
        
        .analysis-subtitle {{
            font-size: 1.25rem;
            line-height: 1.6;
            color: var(--text-secondary);
            max-width: 800px;
        }}
        
        /* Analysis Grid */
        .analysis-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-bottom: 3rem;
        }}
        
        .analysis-card {{
            background: var(--surface-secondary);
            border-radius: 8px;
            padding: 2rem;
            border: 1px solid var(--border);
        }}
        
        .analysis-card-title {{
            font-family: 'Inter', sans-serif;
            font-size: 0.875rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--text-secondary);
            margin-bottom: 1.5rem;
            opacity: 0.7;
        }}
        
        /* Controls Section */
        .controls-section {{
            padding: 1.5rem 2rem;
            background: var(--surface-secondary);
            border-bottom: 1px solid var(--border);
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        
        .controls-content {{
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        }}
        
        .progress-indicator {{
            font-family: 'Inter', sans-serif;
            font-size: 0.875rem;
            color: var(--text-secondary);
        }}
        
        .control-buttons {{
            display: flex;
            gap: 0.75rem;
        }}
        
        .control-button {{
            padding: 0.5rem 1rem;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 4px;
            font-family: 'Inter', sans-serif;
            font-size: 0.8125rem;
            font-weight: 500;
            color: var(--text-secondary);
            cursor: pointer;
            transition: all 0.15s ease;
        }}
        
        .control-button:hover {{
            border-color: var(--text-primary);
            color: var(--text-primary);
        }}
        
        /* Conversation Section */
        .conversation-section {{
            padding: 3rem 2rem;
        }}
        
        .conversation-content {{
            max-width: 1100px;
            margin: 0 auto;
        }}
        
        /* Turn Styles */
        .turn {{
            border-bottom: 1px solid var(--border);
            position: relative;
            transition: background-color 0.15s ease;
        }}
        
        .turn:last-child {{
            border-bottom: none;
        }}
        
        .turn.collapsed {{
            background: var(--surface-secondary);
        }}
        
        .turn.key-moment {{
            border-left: 3px solid var(--accent);
        }}
        
        .turn-header {{
            padding: 1rem 1.5rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 1rem;
        }}
        
        .turn.collapsed .turn-header {{
            padding: 0.75rem 1.5rem;
        }}
        
        .turn-number {{
            font-family: 'Inter', sans-serif;
            font-size: 0.6875rem;
            font-weight: 500;
            color: var(--text-muted);
            min-width: 3rem;
            opacity: 0.6;
        }}
        
        .turn-preview {{
            flex: 1;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            min-width: 0;
        }}
        
        .speaker-badge {{
            font-family: 'Inter', sans-serif;
            font-size: 0.625rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            padding: 0.125rem 0.375rem;
            border-radius: 2px;
            flex-shrink: 0;
        }}
        
        .speaker-badge.interviewer {{
            background: rgba(30, 90, 142, 0.08);
            color: var(--interviewer);
        }}
        
        .speaker-badge.participant {{
            background: rgba(139, 69, 19, 0.08);
            color: var(--participant);
        }}
        
        .turn-preview-text {{
            color: var(--text-secondary);
            font-size: 0.875rem;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            opacity: 0.8;
        }}
        
        .turn-expand-icon {{
            font-size: 0.875rem;
            color: var(--text-muted);
            transition: transform 0.15s ease;
            opacity: 0.4;
        }}
        
        .turn.expanded .turn-expand-icon {{
            transform: rotate(180deg);
        }}
        
        /* Turn Content */
        .turn-content {{
            max-height: 0;
            overflow: hidden;
            opacity: 0;
            transition: all 0.2s ease;
        }}
        
        .turn.expanded .turn-content {{
            max-height: 3000px;
            opacity: 1;
        }}
        
        .turn-content-inner {{
            padding: 0 1.5rem 1.5rem 1.5rem;
        }}
        
        .speech-block {{
            margin-bottom: 1.25rem;
        }}
        
        .speaker-name {{
            font-family: 'Inter', sans-serif;
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--text-secondary);
            margin-bottom: 0.5rem;
        }}
        
        .speech {{
            font-size: 1.05rem;
            line-height: 1.7;
            color: var(--text-primary);
            white-space: pre-wrap;
        }}
        
        .speech.interviewer {{
            color: var(--text-secondary);
            font-style: italic;
        }}
        
        .emphasis {{
            background: linear-gradient(180deg, transparent 60%, rgba(220, 38, 38, 0.15) 60%);
            padding: 0 0.1rem;
        }}
        
        /* Complete Annotation Grid */
        .annotation-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 0.75rem;
            margin-top: 1rem;
            font-family: 'Inter', sans-serif;
            font-size: 0.8125rem;
        }}
        
        .annotation-dimension {{
            background: var(--surface-secondary);
            border-radius: 4px;
            padding: 0.875rem;
            border-left: 3px solid var(--border);
        }}
        
        .annotation-dimension.functional {{
            border-left-color: var(--function-color);
        }}
        
        .annotation-dimension.content {{
            border-left-color: var(--content-color);
        }}
        
        .annotation-dimension.emotional {{
            border-left-color: var(--emotion-color);
        }}
        
        .annotation-dimension.evidence {{
            border-left-color: var(--evidence-color);
        }}
        
        .annotation-dimension.uncertainty {{
            border-left-color: var(--uncertainty-color);
        }}
        
        .dimension-label {{
            font-size: 0.625rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            opacity: 0.6;
            margin-bottom: 0.375rem;
            display: flex;
            align-items: center;
            gap: 0.375rem;
        }}
        
        .dimension-icon {{
            font-size: 0.875rem;
            opacity: 0.8;
        }}
        
        .dimension-content {{
            color: var(--text-primary);
            line-height: 1.5;
        }}
        
        .dimension-detail {{
            font-size: 0.75rem;
            color: var(--text-secondary);
            margin-top: 0.25rem;
        }}
        
        .confidence-tag {{
            display: inline-block;
            padding: 0.125rem 0.375rem;
            background: var(--border);
            border-radius: 3px;
            font-size: 0.625rem;
            font-weight: 600;
            margin-left: 0.5rem;
            opacity: 0.7;
        }}
        
        /* Minimal annotations for simple turns */
        .minimal-annotation {{
            font-family: 'Inter', sans-serif;
            font-size: 0.75rem;
            color: var(--text-secondary);
            margin-top: 0.75rem;
            padding: 0.5rem 0.75rem;
            background: var(--surface-secondary);
            border-radius: 4px;
            display: inline-block;
        }}
        
        /* Priority list */
        .priority-list {{
            display: flex;
            flex-direction: column;
            gap: 0.875rem;
        }}
        
        .priority-item {{
            display: flex;
            align-items: center;
            gap: 0.875rem;
        }}
        
        .priority-rank {{
            width: 20px;
            height: 20px;
            background: var(--accent);
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Inter', sans-serif;
            font-size: 0.6875rem;
            font-weight: 600;
        }}
        
        .priority-name {{
            font-size: 0.95rem;
            color: var(--text-primary);
        }}
        
        .memorable-quote {{
            font-style: italic;
            color: var(--text-secondary);
            border-left: 3px solid var(--accent);
            padding-left: 1rem;
            margin: 1rem 0;
        }}
        
        /* Scrollbar */
        ::-webkit-scrollbar {{
            width: 10px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: transparent;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: var(--text-muted);
            border-radius: 5px;
            background-clip: padding-box;
            border: 3px solid transparent;
        }}
        
        /* Mobile */
        @media (max-width: 768px) {{
            .analysis-grid {{
                grid-template-columns: 1fr;
            }}
            
            .annotation-grid {{
                grid-template-columns: 1fr;
            }}
            
            .controls-content {{
                flex-direction: column;
                align-items: stretch;
            }}
        }}
    </style>
</head>
<body>
    <header class="header">
        <div class="header-content">
            <h1>Interview {interview_id} — {location}</h1>
            <div class="header-meta">
                <span>{date}</span>
                <span>{duration} minutes</span>
            </div>
        </div>
    </header>

    <section class="analysis-section">
        <div class="analysis-content">
            <div class="analysis-header">
                <h2 class="analysis-title">Interview {interview_id}: Citizen Perspectives</h2>
                <p class="analysis-subtitle">
                    {narrative_summary}
                </p>
            </div>
            
            <div class="analysis-grid">
                <div class="analysis-card">
                    <h3 class="analysis-card-title">Identified Priorities</h3>
                    <div class="priority-list">
                        {priorities}
                    </div>
                </div>
                
                <div class="analysis-card">
                    <h3 class="analysis-card-title">Key Insight</h3>
                    <div style="font-size: 1rem; line-height: 1.6; color: var(--text-primary);">
                        {key_insight}
                    </div>
                </div>
            </div>
            
            {memorable_quotes}
        </div>
    </section>

    <section class="controls-section">
        <div class="controls-content">
            <div class="progress-indicator">
                <span id="expandedCount">{expanded_count}</span> of {total_turns} turns expanded
            </div>
            <div class="control-buttons">
                <button class="control-button" onclick="expandAll()">Expand All</button>
                <button class="control-button" onclick="collapseAll()">Collapse All</button>
                <button class="control-button" onclick="showKeyMoments()">Key Moments</button>
            </div>
        </div>
    </section>

    <section class="conversation-section">
        <div class="conversation-content">
            {turns_html}
        </div>
    </section>

    <script>
        let expandedTurns = new Set();
        
        // Initialize expanded turns
        document.querySelectorAll('.turn.expanded').forEach(turn => {{
            expandedTurns.add(turn.dataset.turn);
        }});
        
        function updateProgressIndicator() {{
            const expanded = document.querySelectorAll('.turn.expanded').length;
            document.getElementById('expandedCount').textContent = expanded;
        }}
        
        function toggleTurn(element) {{
            const turn = element.parentElement;
            const turnId = turn.dataset.turn;
            
            if (turn.classList.contains('expanded')) {{
                turn.classList.remove('expanded');
                turn.classList.add('collapsed');
                expandedTurns.delete(turnId);
            }} else {{
                turn.classList.remove('collapsed');
                turn.classList.add('expanded');
                expandedTurns.add(turnId);
            }}
            
            updateProgressIndicator();
        }}
        
        function expandAll() {{
            document.querySelectorAll('.turn').forEach(turn => {{
                turn.classList.remove('collapsed');
                turn.classList.add('expanded');
                expandedTurns.add(turn.dataset.turn);
            }});
            updateProgressIndicator();
        }}
        
        function collapseAll() {{
            document.querySelectorAll('.turn').forEach(turn => {{
                turn.classList.remove('expanded');
                turn.classList.add('collapsed');
            }});
            expandedTurns.clear();
            updateProgressIndicator();
        }}
        
        function showKeyMoments() {{
            document.querySelectorAll('.turn').forEach(turn => {{
                turn.classList.remove('expanded');
                turn.classList.add('collapsed');
            }});
            expandedTurns.clear();
            
            document.querySelectorAll('.turn.key-moment').forEach(turn => {{
                turn.classList.remove('collapsed');
                turn.classList.add('expanded');
                expandedTurns.add(turn.dataset.turn);
            }});
            updateProgressIndicator();
        }}
        
        updateProgressIndicator();
    </script>
</body>
</html>'''


def main():
    """Generate HTML from annotation data."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python generate_interview_html_generic.py <interview_id>")
        print("Example: python generate_interview_html_generic.py 089")
        return
    
    interview_id = sys.argv[1].zfill(3)  # Ensure 3 digits
    
    # Look for annotation and transcript files
    data_dir = Path("data/processed/annotations/production")
    transcript_dir = Path("data/processed/interviews_txt")
    
    # Find interview files
    annotation_file = data_dir / f"{interview_id}_final_annotation.json"
    
    # Find transcript file with flexible naming
    transcript_file = None
    for file in transcript_dir.glob(f"*{interview_id}.txt"):
        transcript_file = file
        break
    
    if not annotation_file.exists():
        print(f"Error: Could not find annotation file for interview {interview_id}")
        print(f"Looking for: {annotation_file}")
        return
        
    if not transcript_file or not transcript_file.exists():
        print(f"Warning: Could not find transcript file for interview {interview_id}")
        print("Proceeding without transcript text...")
    
    print(f"Found annotation file: {annotation_file}")
    if transcript_file:
        print(f"Found transcript file: {transcript_file}")
    
    # Generate HTML
    generator = InterviewHTMLGenerator()
    annotation_data = generator.load_annotation_data(str(annotation_file))
    
    # Load and merge transcript if available
    if transcript_file:
        with open(transcript_file, 'r', encoding='utf-8') as f:
            transcript_text = f.read()
        
        # Parse transcript into turns
        transcript_turns = generator.parse_transcript(transcript_text)
        
        # Merge transcript with annotations
        generator.merge_transcript_with_annotations(annotation_data, transcript_turns)
    
    output_path = f"interview_{interview_id}_annotated.html"
    generator.generate_complete_html(annotation_data, output_path)


if __name__ == "__main__":
    main()