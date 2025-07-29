"""
Handle citation rendering and interaction in Streamlit
"""

import re
import streamlit as st
from typing import Dict, List, Tuple
import json

class CitationHandler:
    """Handle citation parsing and rendering for Streamlit"""
    
    CITATION_PATTERN = r'\b(\d{3}):(\d+)(?:-(\d+))?\b'
    
    def __init__(self, corpus_data: Dict):
        self.corpus_data = corpus_data
        
    def parse_text_with_citations(self, text: str) -> List[Dict]:
        """Parse text and extract citation information"""
        segments = []
        last_end = 0
        
        for match in re.finditer(self.CITATION_PATTERN, text):
            # Add text before citation
            if match.start() > last_end:
                segments.append({
                    'type': 'text',
                    'content': text[last_end:match.start()]
                })
            
            # Add citation
            interview_id = match.group(1)
            start_turn = int(match.group(2))
            end_turn = int(match.group(3)) if match.group(3) else start_turn
            
            segments.append({
                'type': 'citation',
                'content': match.group(0),
                'interview_id': interview_id,
                'start_turn': start_turn,
                'end_turn': end_turn
            })
            
            last_end = match.end()
        
        # Add remaining text
        if last_end < len(text):
            segments.append({
                'type': 'text',
                'content': text[last_end:]
            })
        
        return segments
    
    def render_text_with_citations(self, text: str, key_prefix: str = ""):
        """Render text with clickable citations in Streamlit"""
        segments = self.parse_text_with_citations(text)
        
        # Use columns to render inline
        cols = st.columns(len(segments))
        
        for i, segment in enumerate(segments):
            with cols[i]:
                if segment['type'] == 'text':
                    st.write(segment['content'])
                else:
                    # Create a button for the citation
                    if st.button(
                        segment['content'], 
                        key=f"{key_prefix}_cite_{i}_{segment['interview_id']}_{segment['start_turn']}",
                        help=self._get_preview(segment['interview_id'], segment['start_turn'])
                    ):
                        # Store in session state for navigation
                        st.session_state['view_interview'] = {
                            'interview_id': segment['interview_id'],
                            'turn': segment['start_turn']
                        }
                        st.rerun()
    
    def render_with_inline_citations(self, text: str):
        """Alternative: Render using markdown with tooltips"""
        segments = self.parse_text_with_citations(text)
        
        # Build the display text with placeholders
        display_parts = []
        citation_info = []
        
        for segment in segments:
            if segment['type'] == 'text':
                display_parts.append(segment['content'])
            else:
                # Get preview for tooltip
                preview = self._get_preview(segment['interview_id'], segment['start_turn'])
                
                # Create citation with number reference
                citation_num = len(citation_info) + 1
                display_parts.append(f"**[{segment['content']}]**[^{citation_num}]")
                
                citation_info.append({
                    'citation': segment['content'],
                    'preview': preview,
                    'interview_id': segment['interview_id'],
                    'turn': segment['start_turn']
                })
        
        # Display the main text
        st.markdown(''.join(display_parts))
        
        # Add expandable section for citations
        if citation_info:
            with st.expander("📌 Citation Details", expanded=False):
                for i, info in enumerate(citation_info):
                    col1, col2 = st.columns([1, 5])
                    with col1:
                        if st.button(f"View {info['citation']}", key=f"view_{info['citation']}_{i}"):
                            st.session_state['view_interview'] = {
                                'interview_id': info['interview_id'],
                                'turn': info['turn']
                            }
                            st.rerun()
                    with col2:
                        st.caption(info['preview'])
                        
    def _get_preview(self, interview_id: str, turn_num: int, max_length: int = 150) -> str:
        """Get a preview of a turn"""
        try:
            turn_key = f"{interview_id}:{turn_num}"
            turn_data = self.corpus_data.get('turns', {}).get(turn_key)
            
            if turn_data:
                turn = turn_data['turn']
                speaker = turn.get('speaker', 'Unknown')
                text = turn.get('text', '')[:max_length]
                if len(turn.get('text', '')) > max_length:
                    text += "..."
                return f"{speaker}: {text}"
            else:
                return f"Turn {turn_num} from interview {interview_id}"
        except:
            return f"Citation: {interview_id}:{turn_num}"