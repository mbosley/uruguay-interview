"""
Interview Viewer - Display full interview with enriched annotations
"""

import streamlit as st
import sys
import os

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
web_demo_dir = os.path.dirname(current_dir)
parent_dir = os.path.dirname(web_demo_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, web_demo_dir)

from corpus_loader import load_enriched_corpus, get_interview_context

st.set_page_config(
    page_title="Interview Viewer",
    page_icon="📄",
    layout="wide"
)

def display_turn(turn, turn_number):
    """Display a single turn with formatting"""
    speaker = turn.get('speaker', 'Unknown')
    text = turn.get('text', '')
    themes = turn.get('themes', [])
    tags = turn.get('tags', [])
    
    # Create columns for turn display
    col1, col2 = st.columns([1, 4])
    
    with col1:
        st.markdown(f"**Turn {turn_number}**")
        st.markdown(f"*{speaker}*")
        
        if themes:
            st.markdown("**Themes:**")
            for theme in themes:
                st.caption(f"• {theme}")
    
    with col2:
        # Highlight if this is the target turn
        if turn_number == st.session_state.get('target_turn'):
            st.markdown(f'<div style="background-color: #ffffcc; padding: 10px; border-radius: 5px;">{text}</div>', 
                       unsafe_allow_html=True)
        else:
            st.markdown(text)
        
        if tags:
            tag_html = " ".join([f'<span style="background-color: #e3f2fd; padding: 2px 8px; border-radius: 12px; margin-right: 5px; font-size: 0.8em;">{tag}</span>' for tag in tags])
            st.markdown(tag_html, unsafe_allow_html=True)
    
    st.divider()

def main():
    # Get interview ID from URL params
    params = st.query_params
    interview_id = params.get('id', '')
    target_turn = params.get('turn', None)
    
    if target_turn:
        st.session_state.target_turn = int(target_turn)
    
    if not interview_id:
        st.error("No interview ID provided")
        st.stop()
    
    # Load corpus
    with st.spinner("Loading interview data..."):
        corpus_data = load_enriched_corpus()
    
    if not corpus_data:
        st.error("Failed to load corpus data")
        st.stop()
    
    # Get interview context
    interview = get_interview_context(interview_id, corpus_data)
    
    if not interview:
        st.error(f"Interview {interview_id} not found")
        st.stop()
    
    # Header
    st.title(f"Interview {interview_id}")
    
    # Metadata
    metadata = interview['metadata']
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Date", metadata.get('date', 'Unknown'))
    with col2:
        st.metric("Duration", metadata.get('duration', 'Unknown'))
    with col3:
        st.metric("Speakers", metadata.get('num_speakers', 0))
    with col4:
        st.metric("Turns", len(interview['turns']))
    
    # Summary section
    if 'summary' in interview and interview['summary']:
        with st.expander("📋 Interview Summary", expanded=True):
            summary = interview['summary']
            
            if 'overview' in summary:
                st.markdown("### Overview")
                st.markdown(summary['overview'])
            
            if 'key_themes' in summary:
                st.markdown("### Key Themes")
                for theme in summary['key_themes']:
                    st.markdown(f"- **{theme['theme']}**: {theme['description']}")
            
            if 'participant_concerns' in summary:
                st.markdown("### Main Concerns")
                st.markdown(summary['participant_concerns'])
    
    # Navigation
    st.markdown("### Interview Transcript")
    
    if target_turn:
        if st.button(f"⬆️ Jump to Turn {target_turn}"):
            # This would scroll to the turn if we had JavaScript
            pass
    
    # Display all turns
    for turn in interview['turns']:
        turn_num = turn.get('turn_number', 0)
        display_turn(turn, turn_num)

if __name__ == "__main__":
    main()