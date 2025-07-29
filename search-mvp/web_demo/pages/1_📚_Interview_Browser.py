"""
Interview Browser - Explore all citizen consultation interviews
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
    page_title="Interview Browser",
    page_icon="📚",
    layout="wide"
)

def main():
    st.title("📚 Interview Browser")
    st.markdown("Explore all 35 citizen consultation interviews from Uruguay")
    
    # Load corpus
    with st.spinner("Loading interview corpus..."):
        corpus_data = load_enriched_corpus()
    
    if not corpus_data['interviews']:
        st.error("No interview data found. Please ensure the enriched corpus has been generated.")
        return
    
    # Sidebar filters
    with st.sidebar:
        st.header("🔍 Filters")
        
        # Get theme consolidation for hierarchical filtering
        theme_consolidation = corpus_data.get('theme_consolidation', {})
        issue_tags = theme_consolidation.get('metadata', {}).get('issue_tags', {})
        
        # Issue tag filter
        selected_issue_tags = []
        if issue_tags:
            selected_issue_tags = st.multiselect(
                "Filter by issue area:",
                options=list(issue_tags.keys()),
                format_func=lambda x: issue_tags[x]['name'],
                default=[]
            )
        
        # Get all unique themes across interviews
        all_themes = set()
        all_meta_themes = set()
        for interview_id, interview in corpus_data['interviews'].items():
            # Extract themes from the annotation.summary.key_themes structure
            annotation = interview.get('annotation', {})
            summary = annotation.get('summary', {})
            key_themes = summary.get('key_themes', [])
            
            # Extract theme names from the theme objects
            for theme_obj in key_themes:
                if isinstance(theme_obj, dict) and 'theme' in theme_obj:
                    all_themes.add(theme_obj['theme'])
                    if theme_obj.get('meta_theme'):
                        all_meta_themes.add(theme_obj['meta_theme'])
                elif isinstance(theme_obj, str):
                    all_themes.add(theme_obj)
        
        # Meta-theme filter
        selected_meta_themes = []
        if all_meta_themes:
            selected_meta_themes = st.multiselect(
                "Filter by meta-themes:",
                sorted(all_meta_themes),
                default=[]
            )
        
        # Theme filter
        selected_themes = st.multiselect(
            "Filter by specific themes:",
            sorted(all_themes),
            default=[]
        )
        
        # Search box
        search_query = st.text_input(
            "Search in interviews:",
            placeholder="Enter keywords..."
        )
        
        # Stats
        st.header("📊 Corpus Statistics")
        st.metric("Total Interviews", len(corpus_data['interviews']))
        st.metric("Total Turns", corpus_data['metadata']['total_turns'])
        st.metric("Unique Themes", len(all_themes))
        if issue_tags:
            st.metric("Issue Areas", len(issue_tags))
        if all_meta_themes:
            st.metric("Meta-themes", len(all_meta_themes))
    
    # Main content area
    # Filter interviews based on criteria
    filtered_interviews = []
    for interview_id, interview in corpus_data['interviews'].items():
        # Extract theme data from annotation structure
        annotation = interview.get('annotation', {})
        summary = annotation.get('summary', {})
        key_themes = summary.get('key_themes', [])
        
        # Extract theme data for filtering
        interview_theme_names = []
        interview_meta_themes = []
        interview_issue_tags = []
        
        for theme_obj in key_themes:
            if isinstance(theme_obj, dict) and 'theme' in theme_obj:
                interview_theme_names.append(theme_obj['theme'])
                if theme_obj.get('meta_theme'):
                    interview_meta_themes.append(theme_obj['meta_theme'])
                if theme_obj.get('issue_tags'):
                    interview_issue_tags.extend(theme_obj['issue_tags'])
            elif isinstance(theme_obj, str):
                interview_theme_names.append(theme_obj)
        
        # Apply issue tag filter
        if selected_issue_tags:
            if not any(tag in interview_issue_tags for tag in selected_issue_tags):
                continue
        
        # Apply meta-theme filter
        if selected_meta_themes:
            if not any(meta_theme in interview_meta_themes for meta_theme in selected_meta_themes):
                continue
        
        # Apply theme filter
        if selected_themes:
            if not any(theme in interview_theme_names for theme in selected_themes):
                continue
        
        # Apply search filter
        if search_query:
            search_text = search_query.lower()
            # Search in annotation/summary
            annotation = interview.get('annotation', {})
            summary_obj = annotation.get('summary', {})
            summary_text = str(summary_obj).lower() if summary_obj else ""
            
            # Also search in the overview specifically
            overview_text = summary_obj.get('overview', '').lower() if isinstance(summary_obj, dict) else ""
            
            # Search in turns
            turns_text = ' '.join([turn.get('text', '').lower() for turn in interview.get('turns', [])])
            
            if search_text not in summary_text and search_text not in overview_text and search_text not in turns_text:
                continue
        
        filtered_interviews.append((interview_id, interview))
    
    # Display results
    st.markdown(f"### Showing {len(filtered_interviews)} interviews")
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["📋 List View", "🗂️ Card View"])
    
    with tab1:
        # List view with expandable details
        for interview_id, interview in sorted(filtered_interviews):
            metadata = interview.get('metadata', {})
            annotation = interview.get('annotation', {})
            
            with st.expander(f"**Interview {interview_id}** - {metadata.get('date', 'Unknown date')}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Summary
                    st.markdown("**Overview:**")
                    summary_obj = annotation.get('summary', {})
                    if isinstance(summary_obj, dict):
                        summary_text = summary_obj.get('overview', 'No summary available')
                    else:
                        summary_text = str(summary_obj) if summary_obj else 'No summary available'
                    st.write(summary_text[:500] + "..." if len(summary_text) > 500 else summary_text)
                    
                    # Key themes
                    key_themes = summary_obj.get('key_themes', []) if isinstance(summary_obj, dict) else []
                    theme_names = []
                    for theme_item in key_themes:
                        if isinstance(theme_item, dict) and 'theme' in theme_item:
                            theme_names.append(theme_item['theme'])
                        elif isinstance(theme_item, str):
                            theme_names.append(theme_item)
                    
                    if theme_names:
                        st.markdown("**Key Themes:**")
                        theme_tags = " ".join([f"`{theme}`" for theme in theme_names[:5]])
                        st.markdown(theme_tags)
                    
                    # Key quotes - check both in annotation and in summary
                    quotes = annotation.get('notable_quotes', [])
                    if not quotes and isinstance(summary_obj, dict):
                        # Check if quotes are in the key_themes structure
                        for theme_obj in key_themes:
                            if isinstance(theme_obj, dict) and 'primary_evidence' in theme_obj:
                                for evidence in theme_obj['primary_evidence']:
                                    if 'quote' in evidence:
                                        quotes.append({
                                            'quote': evidence['quote'],
                                            'turn': evidence.get('turn', '')
                                        })
                                if quotes:
                                    break
                    
                    if quotes:
                        st.markdown("**Key Quote:**")
                        quote = quotes[0]
                        if isinstance(quote, dict):
                            quote_text = quote.get("quote", quote.get("text", ""))
                            turn_ref = quote.get("turn", "")
                            if turn_ref:
                                st.info(f'"{quote_text[:200]}..." - Turn {turn_ref}')
                            else:
                                st.info(f'"{quote_text[:200]}..."')
                        else:
                            st.info(f'"{quotes[0][:200]}..."')
                
                with col2:
                    # Metadata
                    st.markdown("**Details:**")
                    
                    # Extract location from annotation tags
                    location_tags = annotation.get('tags', {}).get('location', [])
                    location = location_tags[0] if location_tags else 'Unknown'
                    
                    # Count unique speakers from turns
                    speakers = set()
                    for turn in interview.get('turns', []):
                        if 'speaker' in turn:
                            speakers.add(turn['speaker'])
                    
                    st.write(f"📅 Date: {metadata.get('date', 'Unknown')}")
                    st.write(f"⏱️ Duration: {metadata.get('duration', 'Unknown')}")
                    st.write(f"📍 Location: {location}")
                    st.write(f"👥 Speakers: {len(speakers)}")
                    st.write(f"💬 Turns: {len(interview.get('turns', []))}")
                    
                    # Action buttons
                    if st.button(f"View Full Interview", key=f"view_{interview_id}"):
                        st.session_state['view_interview'] = {
                            'interview_id': interview_id,
                            'interview_data': interview
                        }
                        st.switch_page("pages/2_📄_Interview_Viewer.py")
    
    with tab2:
        # Card view
        cols_per_row = 3
        for i in range(0, len(filtered_interviews), cols_per_row):
            cols = st.columns(cols_per_row)
            
            for j, col in enumerate(cols):
                if i + j < len(filtered_interviews):
                    interview_id, interview = filtered_interviews[i + j]
                    metadata = interview.get('metadata', {})
                    summary = interview.get('enriched_summary', {})
                    
                    with col:
                        with st.container():
                            st.markdown(f"### Interview {interview_id}")
                            st.caption(f"{metadata.get('date', 'Unknown date')}")
                            
                            # Mini summary
                            annotation = interview.get('annotation', {})
                            summary_obj = annotation.get('summary', {})
                            overview = summary_obj.get('overview', 'No summary available') if isinstance(summary_obj, dict) else 'No summary available'
                            st.write(overview[:150] + "..." if len(overview) > 150 else overview)
                            
                            # Stats - count speakers from turns
                            speakers = set()
                            for turn in interview.get('turns', []):
                                if 'speaker' in turn:
                                    speakers.add(turn['speaker'])
                            
                            st.markdown(f"👥 {len(speakers)} speakers | 💬 {len(interview.get('turns', []))} turns")
                            
                            # Top themes
                            key_themes = summary_obj.get('key_themes', []) if isinstance(summary_obj, dict) else []
                            theme_names = []
                            for theme_item in key_themes[:2]:  # Show only 2 themes to have more space
                                if isinstance(theme_item, dict) and 'theme' in theme_item:
                                    theme_names.append(theme_item['theme'])
                                elif isinstance(theme_item, str):
                                    theme_names.append(theme_item)
                            
                            if theme_names:
                                # Show full theme names on separate lines
                                st.markdown("**Themes:**")
                                for theme in theme_names:
                                    # Truncate at word boundary if too long
                                    if len(theme) > 50:
                                        # Find last space before 50 chars
                                        truncate_at = theme[:50].rfind(' ')
                                        if truncate_at > 0:
                                            theme_display = theme[:truncate_at] + "..."
                                        else:
                                            theme_display = theme[:50] + "..."
                                    else:
                                        theme_display = theme
                                    st.caption(f"• {theme_display}")
                            
                            if st.button("Open", key=f"open_card_{interview_id}"):
                                st.session_state['view_interview'] = {
                                    'interview_id': interview_id,
                                    'interview_data': interview
                                }
                                st.switch_page("pages/2_📄_Interview_Viewer.py")

if __name__ == "__main__":
    main()
