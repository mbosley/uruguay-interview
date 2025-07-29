"""
Interview Viewer - Display full interview with enriched annotations
"""

import streamlit as st
import os
import sys
from datetime import datetime

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
web_demo_dir = os.path.dirname(current_dir)
parent_dir = os.path.dirname(web_demo_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, web_demo_dir)

from corpus_loader import load_enriched_corpus

st.set_page_config(
    page_title="Interview Viewer",
    page_icon="📄",
    layout="wide"
)

def highlight_turn(turn_number, target_turn):
    """Check if this turn should be highlighted"""
    return turn_number == target_turn

def main():
    st.title("📄 Interview Viewer")
    
    # Check if we have an interview to view
    if 'view_interview' not in st.session_state:
        st.warning("No interview selected. Please go to the Interview Browser to select an interview.")
        if st.button("Go to Interview Browser"):
            st.switch_page("pages/1_📚_Interview_Browser.py")
        return
    
    interview_id = st.session_state['view_interview'].get('interview_id')
    target_turn = st.session_state['view_interview'].get('turn')
    
    # Load corpus
    corpus_data = load_enriched_corpus()
    
    # Get interview data
    if interview_id in corpus_data['interviews']:
        interview = corpus_data['interviews'][interview_id]
    else:
        st.error(f"Interview {interview_id} not found in corpus")
        return
    
    # Header with metadata
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        st.markdown(f"## Interview {interview_id}")
        metadata = interview.get('metadata', {})
        st.caption(f"📅 {metadata.get('date', 'Unknown date')} | 📍 {metadata.get('location', 'Unknown location')} | ⏱️ {metadata.get('duration', 'Unknown duration')}")
    
    with col2:
        if st.button("← Back to Browser"):
            st.switch_page("pages/1_📚_Interview_Browser.py")
    
    with col3:
        if st.button("🏠 Back to Research"):
            st.switch_page("app.py")
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Transcript", "📊 Summary", "🏷️ Themes & Analysis", "🔍 Search"])
    
    with tab1:
        # Transcript view
        st.markdown("### Interview Transcript")
        
        # If we have a target turn, show navigation
        if target_turn:
            st.info(f"📍 Navigated to turn {target_turn}")
            if st.button(f"Jump to Turn {target_turn}"):
                st.write(f"<div id='turn_{target_turn}'></div>", unsafe_allow_html=True)
        
        # Display options
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            show_themes = st.checkbox("Show themes", value=True)
        with col2:
            show_timestamps = st.checkbox("Show timestamps", value=False)
        with col3:
            speaker_filter = st.selectbox(
                "Filter by speaker:",
                ["All"] + list(metadata.get('speakers', {}).keys())
            )
        
        # Display turns
        turns = interview.get('turns', [])
        
        for turn in turns:
            turn_num = turn.get('turn_number', 0)
            speaker = turn.get('speaker', 'Unknown')
            text = turn.get('text', '')
            
            # Skip if filtering by speaker
            if speaker_filter != "All" and speaker != speaker_filter:
                continue
            
            # Highlight if this is the target turn
            is_target = target_turn and turn_num == target_turn
            
            # Create container for turn
            with st.container():
                if is_target:
                    st.markdown(f"<div style='background-color: #fff3cd; padding: 10px; border-radius: 5px;'>", unsafe_allow_html=True)
                
                # Turn header
                header_cols = st.columns([3, 1])
                with header_cols[0]:
                    st.markdown(f"**Turn {turn_num} - {speaker}**")
                with header_cols[1]:
                    if show_timestamps and 'timestamp' in turn:
                        st.caption(turn['timestamp'])
                
                # Turn text
                st.write(text)
                
                # Themes and tags
                if show_themes:
                    themes = turn.get('themes', [])
                    tags = turn.get('tags', [])
                    
                    if themes or tags:
                        theme_str = " ".join([f"`{theme}`" for theme in themes])
                        tag_str = " ".join([f"🏷️ {tag}" for tag in tags])
                        st.caption(f"{theme_str} {tag_str}")
                
                if is_target:
                    st.markdown("</div>", unsafe_allow_html=True)
                
                st.divider()
    
    with tab2:
        # Summary view
        st.markdown("### Interview Summary")
        
        annotation = interview.get('annotation', {})
        summary = annotation.get('summary', {})
        
        # Overview
        if isinstance(summary, dict) and 'overview' in summary:
            st.markdown("#### Overview")
            st.write(summary['overview'])
        
        # Key themes
        if isinstance(summary, dict) and 'key_themes' in summary:
            st.markdown("#### Key Themes")
            theme_cols = st.columns(3)
            theme_names = []
            for theme_obj in summary['key_themes']:
                if isinstance(theme_obj, dict) and 'theme' in theme_obj:
                    theme_names.append(theme_obj['theme'])
                elif isinstance(theme_obj, str):
                    theme_names.append(theme_obj)
            
            for i, theme in enumerate(theme_names):
                with theme_cols[i % 3]:
                    st.info(theme)
        
        # Key quotes
        if 'key_quotes' in summary:
            st.markdown("#### Key Quotes")
            for quote in summary['key_quotes']:
                if isinstance(quote, dict):
                    speaker = quote.get('speaker', 'Unknown')
                    text = quote.get('text', '')
                    turn = quote.get('turn_number', '')
                    
                    with st.container():
                        st.markdown(f'> "{text}"')
                        st.caption(f"— {speaker} (Turn {turn})")
                else:
                    st.markdown(f'> "{quote}"')
    
    with tab3:
        # Themes and Analysis
        st.markdown("### Thematic Analysis")
        
        # Get themes from annotation
        annotation = interview.get('annotation', {})
        summary = annotation.get('summary', {})
        key_themes = summary.get('key_themes', [])
        
        if key_themes:
            st.markdown("#### Key Themes")
            
            for theme_obj in key_themes:
                if isinstance(theme_obj, dict):
                    theme_name = theme_obj.get('theme', 'Unknown theme')
                    description = theme_obj.get('description', '')
                    intensity = theme_obj.get('intensity', '')
                    primary_evidence = theme_obj.get('primary_evidence', [])
                    elaboration_turns = theme_obj.get('elaboration_turns', [])
                    
                    # Count total occurrences
                    all_turn_refs = set()
                    for evidence in primary_evidence:
                        if 'turn' in evidence:
                            all_turn_refs.add(evidence['turn'])
                    all_turn_refs.update(elaboration_turns)
                    
                    with st.expander(f"**{theme_name}** ({len(all_turn_refs)} turns) - {intensity} intensity"):
                        # Description
                        if description:
                            st.write(description)
                            st.divider()
                        
                        # Primary evidence
                        if primary_evidence:
                            st.markdown("**Primary Evidence:**")
                            for evidence in primary_evidence:
                                turn_ref = evidence.get('turn', '')
                                quote = evidence.get('quote', '')
                                if turn_ref and quote:
                                    # Extract turn number from reference (e.g., "068:12" -> 12)
                                    try:
                                        turn_num = int(turn_ref.split(':')[1])
                                        # Find the actual turn
                                        for turn in turns:
                                            if turn['turn_number'] == turn_num:
                                                st.write(f"**Turn {turn_num}** ({turn['speaker']}):")
                                                st.info(f'"{quote}"')
                                                break
                                    except:
                                        st.write(f"**{turn_ref}**:")
                                        st.info(f'"{quote}"')
                        
                        # Elaboration turns
                        if elaboration_turns:
                            st.markdown("**Related Discussions:**")
                            turn_refs_str = ", ".join(elaboration_turns)
                            st.write(f"See also turns: {turn_refs_str}")
                            
                            # Show first few elaboration excerpts
                            for turn_ref in elaboration_turns[:3]:
                                try:
                                    turn_num = int(turn_ref.split(':')[1])
                                    for turn in turns:
                                        if turn['turn_number'] == turn_num:
                                            st.caption(f"Turn {turn_num} ({turn['speaker']}): {turn['text'][:150]}...")
                                            break
                                except:
                                    pass
        else:
            st.info("No thematic analysis available for this interview.")
        
        # Tags analysis from annotation
        tags = annotation.get('tags', {})
        if tags:
            st.markdown("#### Interview Tags")
            for category, tag_list in tags.items():
                if tag_list:
                    st.markdown(f"**{category.replace('_', ' ').title()}:**")
                    tag_str = " ".join([f"`{tag}`" for tag in tag_list])
                    st.write(tag_str)
    
    with tab4:
        # Search within interview
        st.markdown("### Search in Interview")
        
        search_term = st.text_input("Search for text:", placeholder="Enter search term...")
        
        if search_term:
            search_lower = search_term.lower()
            matching_turns = []
            
            for turn in turns:
                if search_lower in turn.get('text', '').lower():
                    matching_turns.append(turn)
            
            if matching_turns:
                st.success(f"Found {len(matching_turns)} matches")
                
                for turn in matching_turns:
                    with st.container():
                        st.markdown(f"**Turn {turn['turn_number']} - {turn['speaker']}**")
                        
                        # Highlight search term
                        text = turn['text']
                        highlighted = text.replace(
                            search_term, 
                            f"**{search_term}**"
                        )
                        st.write(highlighted[:300] + "..." if len(highlighted) > 300 else highlighted)
                        
                        if st.button(f"View Turn {turn['turn_number']}", key=f"search_view_{turn['turn_number']}"):
                            st.session_state['view_interview']['turn'] = turn['turn_number']
                            st.rerun()
                        
                        st.divider()
            else:
                st.warning(f"No matches found for '{search_term}'")
    
    # Sidebar with navigation
    with st.sidebar:
        st.header("📍 Navigation")
        
        # Quick jump to turn
        turn_to_jump = st.number_input(
            "Jump to turn:",
            min_value=1,
            max_value=len(turns),
            value=target_turn if target_turn else 1
        )
        
        if st.button("Jump"):
            st.session_state['view_interview']['turn'] = turn_to_jump
            st.rerun()
        
        # Speaker breakdown
        st.header("👥 Speakers")
        speaker_counts = {}
        for turn in turns:
            speaker = turn.get('speaker', 'Unknown')
            speaker_counts[speaker] = speaker_counts.get(speaker, 0) + 1
        
        for speaker, count in speaker_counts.items():
            st.write(f"**{speaker}**: {count} turns")
        
        # Interview stats
        st.header("📊 Statistics")
        st.metric("Total Turns", len(turns))
        
        # Count themes from annotation
        annotation = interview.get('annotation', {})
        summary = annotation.get('summary', {})
        key_themes = summary.get('key_themes', [])
        st.metric("Total Themes", len(key_themes))
        
        # Count unique tags
        all_tags = []
        tags = annotation.get('tags', {})
        for tag_list in tags.values():
            all_tags.extend(tag_list)
        st.metric("Unique Tags", len(set(all_tags)))

if __name__ == "__main__":
    main()