"""
Streamlit page for viewing individual interviews with enriched data
"""

import streamlit as st
import json
import os
import sys
from datetime import datetime

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Load environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(parent_dir, '.env'))

from citation_utils import CitationParser

# Page config
st.set_page_config(
    page_title="Interview Viewer - Uruguay Research",
    page_icon="📄",
    layout="wide"
)

def load_interview_data(interview_id: str):
    """Load enriched interview data"""
    enriched_path = f"../data/processed/enriched/interview_{interview_id}_enriched.json"
    
    try:
        with open(enriched_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Could not load interview {interview_id}: {e}")
        return None

def display_interview_summary(summary_data: dict):
    """Display the AI-generated interview summary"""
    st.header("📊 Interview Summary")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if 'overview' in summary_data:
            st.markdown("### Overview")
            st.info(summary_data['overview'])
        
        if 'main_concerns' in summary_data:
            st.markdown("### Main Concerns")
            for i, concern in enumerate(summary_data['main_concerns'], 1):
                st.markdown(f"{i}. {concern}")
    
    with col2:
        if 'emotional_tone' in summary_data:
            st.markdown("### Emotional Tone")
            st.metric("Overall", summary_data['emotional_tone'])
        
        if 'notable_quotes' in summary_data:
            st.markdown("### Key Quotes")
            for quote in summary_data['notable_quotes'][:2]:
                st.caption(f'"{quote["text"]}" - Turn {quote["turn"]}')

def display_turn(turn: dict, turn_number: int, highlight: bool = False):
    """Display a single turn with enriched data"""
    # Container with highlight if needed
    container = st.container()
    
    if highlight:
        container = st.container(border=True)
        st.markdown("⭐ **Highlighted Turn**")
    
    with container:
        # Turn header
        col1, col2, col3 = st.columns([1, 2, 3])
        
        with col1:
            st.markdown(f"**Turn {turn_number}**")
            st.caption(turn.get('speaker', 'Unknown'))
        
        with col2:
            # Themes
            themes = turn.get('themes', [])
            if themes:
                theme_pills = ' '.join([f'`{t}`' for t in themes[:3]])
                st.markdown(f"🏷️ {theme_pills}")
        
        with col3:
            # Tags  
            tags = turn.get('tags', [])
            if tags:
                tag_pills = ' '.join([f'`{t}`' for t in tags[:3]])
                st.markdown(f"🔖 {tag_pills}")
        
        # Turn text
        st.markdown(turn.get('text', ''))
        
        # Expandable analysis if available
        if turn.get('analysis'):
            with st.expander("🔍 Analysis"):
                st.write(turn['analysis'])

def main():
    # Get interview ID from URL parameters
    query_params = st.query_params
    interview_id = query_params.get("id", None)
    highlight_turn = query_params.get("turn", None)
    
    if not interview_id:
        st.error("No interview ID provided. Please access this page through a citation link.")
        return
    
    # Load interview data
    interview_data = load_interview_data(interview_id)
    if not interview_data:
        return
    
    # Header
    st.title(f"📄 Interview {interview_id}")
    
    # Metadata
    metadata = interview_data.get('metadata', {})
    if metadata:
        cols = st.columns(4)
        with cols[0]:
            st.metric("Date", metadata.get('date', 'Unknown'))
        with cols[1]:
            st.metric("Duration", f"{metadata.get('duration_minutes', 0)} min")
        with cols[2]:
            st.metric("Speakers", metadata.get('num_speakers', 0))
        with cols[3]:
            st.metric("Total Turns", len(interview_data.get('turns', [])))
    
    # Display summary
    if 'interview_summary' in interview_data:
        display_interview_summary(interview_data['interview_summary'])
    
    st.divider()
    
    # Navigation
    st.header("💬 Conversation")
    
    # Search/filter
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_term = st.text_input("🔍 Search turns", placeholder="Search for keywords...")
    with col2:
        filter_theme = st.selectbox("Filter by theme", ["All"] + list(set(
            theme for turn in interview_data.get('turns', []) 
            for theme in turn.get('themes', [])
        )))
    with col3:
        show_analysis = st.checkbox("Show analysis", value=False)
    
    # Display turns
    turns = interview_data.get('turns', [])
    displayed_count = 0
    
    for i, turn in enumerate(turns):
        turn_num = i + 1
        
        # Apply filters
        if search_term and search_term.lower() not in turn.get('text', '').lower():
            continue
        
        if filter_theme != "All" and filter_theme not in turn.get('themes', []):
            continue
        
        # Check if this is the highlighted turn
        is_highlighted = highlight_turn and str(turn_num) == str(highlight_turn)
        
        # Display turn
        display_turn(turn, turn_num, highlight=is_highlighted)
        displayed_count += 1
        
        # Auto-scroll to highlighted turn
        if is_highlighted:
            st.markdown('<div id="highlighted-turn"></div>', unsafe_allow_html=True)
            st.markdown(
                '<script>document.getElementById("highlighted-turn").scrollIntoView();</script>',
                unsafe_allow_html=True
            )
    
    # Summary footer
    st.divider()
    st.caption(f"Displayed {displayed_count} of {len(turns)} turns")
    
    # Sidebar with themes summary
    with st.sidebar:
        st.header("📊 Interview Overview")
        
        # Theme distribution
        all_themes = {}
        for turn in turns:
            for theme in turn.get('themes', []):
                all_themes[theme] = all_themes.get(theme, 0) + 1
        
        if all_themes:
            st.subheader("Theme Distribution")
            for theme, count in sorted(all_themes.items(), key=lambda x: x[1], reverse=True)[:10]:
                st.metric(theme.replace('_', ' ').title(), count)
        
        # Key quotes
        if 'key_quotes' in interview_data:
            st.subheader("💬 Key Quotes")
            for quote in interview_data['key_quotes'][:5]:
                st.info(f'"{quote["text"][:100]}..." - Turn {quote["turn"]}')

if __name__ == "__main__":
    main()