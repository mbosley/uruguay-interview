"""
Theme Explorer - Hierarchical exploration of themes by issue tags
"""

import streamlit as st
import os
import sys
from collections import defaultdict

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
web_demo_dir = os.path.dirname(current_dir)
parent_dir = os.path.dirname(web_demo_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, web_demo_dir)

from corpus_loader import load_enriched_corpus

st.set_page_config(
    page_title="Theme Explorer",
    page_icon="🏷️",
    layout="wide"
)

def main():
    st.title("🏷️ Theme Explorer")
    st.markdown("Explore citizen concerns through hierarchical themes")
    
    # Load corpus
    with st.spinner("Loading corpus data..."):
        corpus_data = load_enriched_corpus()
    
    if not corpus_data['interviews']:
        st.error("No interview data found.")
        return
    
    # Check if theme consolidation is available
    theme_consolidation = corpus_data.get('theme_consolidation', {})
    if not theme_consolidation:
        st.warning("Theme consolidation not available. Run 'make consolidate' to enable hierarchical exploration.")
        return
    
    # Get consolidated data
    meta_themes = theme_consolidation.get('meta_themes', {})
    issue_tags = theme_consolidation.get('metadata', {}).get('issue_tags', {})
    
    # Build hierarchical structure: issue_tag -> meta_theme -> themes
    hierarchy = {}
    
    # Initialize hierarchy with issue tags
    for issue_tag_id, issue_tag_data in issue_tags.items():
        hierarchy[issue_tag_id] = {
            'name': issue_tag_data['name'],
            'description': issue_tag_data['description'],
            'meta_themes': {},
            'total_interviews': set(),
            'total_themes': 0
        }
    
    # Collect theme data and organize by hierarchy
    for interview_id, interview in corpus_data['interviews'].items():
        annotation = interview.get('annotation', {})
        summary = annotation.get('summary', {})
        key_themes = summary.get('key_themes', [])
        
        # Process each theme
        for theme_obj in key_themes:
            if isinstance(theme_obj, dict):
                theme_name = theme_obj.get('theme', '')
                meta_theme_id = theme_obj.get('meta_theme', '')
                theme_issue_tags = theme_obj.get('issue_tags', [])
                
                if not theme_name or not meta_theme_id:
                    continue
                
                # Add to each relevant issue tag
                for issue_tag in theme_issue_tags:
                    if issue_tag in hierarchy:
                        hierarchy[issue_tag]['total_interviews'].add(interview_id)
                        
                        # Initialize meta-theme if not exists
                        if meta_theme_id not in hierarchy[issue_tag]['meta_themes']:
                            hierarchy[issue_tag]['meta_themes'][meta_theme_id] = {
                                'name': meta_themes.get(meta_theme_id, {}).get('name', meta_theme_id),
                                'description': meta_themes.get(meta_theme_id, {}).get('description', ''),
                                'themes': {},
                                'interviews': set()
                            }
                        
                        # Add theme data
                        if theme_name not in hierarchy[issue_tag]['meta_themes'][meta_theme_id]['themes']:
                            hierarchy[issue_tag]['meta_themes'][meta_theme_id]['themes'][theme_name] = {
                                'description': theme_obj.get('description', ''),
                                'intensity': theme_obj.get('intensity', ''),
                                'interviews': set(),
                                'examples': []
                            }
                        
                        # Add interview to theme
                        hierarchy[issue_tag]['meta_themes'][meta_theme_id]['themes'][theme_name]['interviews'].add(interview_id)
                        hierarchy[issue_tag]['meta_themes'][meta_theme_id]['interviews'].add(interview_id)
                        
                        # Add examples from primary evidence
                        theme_data = hierarchy[issue_tag]['meta_themes'][meta_theme_id]['themes'][theme_name]
                        for evidence in theme_obj.get('primary_evidence', []):
                            if len(theme_data['examples']) < 3:
                                theme_data['examples'].append({
                                    'interview_id': interview_id,
                                    'turn': evidence.get('turn', ''),
                                    'quote': evidence.get('quote', '')
                                })
    
    # Convert sets to counts
    for issue_tag_data in hierarchy.values():
        issue_tag_data['total_interviews'] = len(issue_tag_data['total_interviews'])
        for meta_theme_data in issue_tag_data['meta_themes'].values():
            meta_theme_data['interviews'] = len(meta_theme_data['interviews'])
            issue_tag_data['total_themes'] += len(meta_theme_data['themes'])
            for theme_data in meta_theme_data['themes'].values():
                theme_data['interviews'] = len(theme_data['interviews'])
    
    # Sidebar
    with st.sidebar:
        st.header("🔍 Navigation")
        
        # Issue tag selector
        selected_issue_tag = st.selectbox(
            "Select Issue Area:",
            ["All"] + [f"{data['name']} ({data['total_interviews']} interviews)" 
                       for tag_id, data in sorted(hierarchy.items(), 
                                                key=lambda x: x[1]['total_interviews'], 
                                                reverse=True)]
        )
        
        # Extract issue tag ID
        if selected_issue_tag != "All":
            selected_issue_tag_id = None
            for tag_id, data in hierarchy.items():
                if selected_issue_tag.startswith(data['name']):
                    selected_issue_tag_id = tag_id
                    break
        else:
            selected_issue_tag_id = None
        
        # Statistics
        st.header("📊 Statistics")
        st.metric("Total Issue Areas", len(hierarchy))
        st.metric("Total Meta-themes", len(meta_themes))
        total_themes = sum(data['total_themes'] for data in hierarchy.values())
        st.metric("Total Themes", total_themes)
    
    # Main content
    if selected_issue_tag_id:
        # Show single issue tag
        display_issue_tag(selected_issue_tag_id, hierarchy[selected_issue_tag_id])
    else:
        # Show all issue tags
        display_all_issue_tags(hierarchy)

def display_all_issue_tags(hierarchy):
    """Display overview of all issue tags"""
    st.markdown("## 📋 All Issue Areas")
    
    # Get corpus data for drilling down
    corpus_data = load_enriched_corpus()
    
    # Sort by number of interviews
    sorted_tags = sorted(hierarchy.items(), key=lambda x: x[1]['total_interviews'], reverse=True)
    
    for issue_tag_id, data in sorted_tags:
        with st.expander(f"**{data['name']}** ({data['total_interviews']} interviews, {data['total_themes']} themes)"):
            st.markdown(f"*{data['description']}*")
            st.divider()
            
            # Show meta-themes with expandable themes
            if data['meta_themes']:
                st.markdown("### Meta-themes in this Issue Area:")
                
                sorted_meta_themes = sorted(
                    data['meta_themes'].items(),
                    key=lambda x: x[1]['interviews'],
                    reverse=True
                )
                
                for meta_theme_id, meta_data in sorted_meta_themes:
                    with st.expander(f"📁 **{meta_data['name']}** ({meta_data['interviews']} interviews, {len(meta_data['themes'])} themes)"):
                        st.markdown(f"*{meta_data['description']}*")
                        st.divider()
                        
                        # Show themes
                        if meta_data['themes']:
                            st.markdown(f"### Themes ({len(meta_data['themes'])} total):")
                            
                            sorted_themes = sorted(
                                meta_data['themes'].items(),
                                key=lambda x: x[1]['interviews'],
                                reverse=True
                            )
                            
                            for theme_name, theme_data in sorted_themes:
                                with st.container():
                                    st.markdown(f"#### 📌 {theme_name}")
                                    st.caption(f"*{theme_data['intensity']} intensity • {theme_data['interviews']} interviews*")
                                    
                                    # Make theme content expandable
                                    with st.expander(f"View details for: {theme_name}"):
                                        if theme_data['description']:
                                            st.write(theme_data['description'])
                                        
                                        # Show examples
                                        if theme_data['examples']:
                                            st.markdown("**Key Evidence:**")
                                            for i, example in enumerate(theme_data['examples']):
                                                if example['quote']:
                                                    st.info(f'"{example["quote"]}" - {example["turn"]}')
                                        
                                        # Show interview list
                                        if theme_data['interviews'] > 0:
                                            st.divider()
                                            st.markdown("### 📚 Interviews with this theme:")
                                            
                                            # Collect interviews
                                            theme_interviews = []
                                            for interview_id, interview in corpus_data['interviews'].items():
                                                for theme_obj in interview.get('annotation', {}).get('summary', {}).get('key_themes', []):
                                                    if (isinstance(theme_obj, dict) and 
                                                        theme_obj.get('theme') == theme_name and
                                                        theme_obj.get('meta_theme') == meta_theme_id and
                                                        issue_tag_id in theme_obj.get('issue_tags', [])):
                                                        
                                                        theme_interviews.append({
                                                            'id': interview_id,
                                                            'location': interview.get('annotation', {}).get('tags', {}).get('location', ['Unknown'])[0],
                                                            'date': interview.get('metadata', {}).get('date', 'Unknown')
                                                        })
                                                        break
                                            
                                            # Display interviews
                                            for idx, int_data in enumerate(sorted(theme_interviews, key=lambda x: x['id'])):
                                                col_a, col_b = st.columns([3, 1])
                                                with col_a:
                                                    st.write(f"**Interview {int_data['id']}** - {int_data['location']} • {int_data['date']}")
                                                with col_b:
                                                    if st.button("Open", key=f"all_open_{issue_tag_id}_{theme_name}_{int_data['id']}_{idx}"):
                                                        st.session_state['view_interview'] = {
                                                            'interview_id': int_data['id']
                                                        }
                                                        st.switch_page("pages/2_📄_Interview_Viewer.py")

def display_issue_tag(issue_tag_id, issue_data):
    """Display detailed view of a single issue tag"""
    # Get corpus data and theme consolidation
    corpus_data = load_enriched_corpus()
    theme_consolidation = corpus_data.get('theme_consolidation', {})
    meta_themes = theme_consolidation.get('meta_themes', {})
    
    st.markdown(f"## {issue_data['name']}")
    st.markdown(f"*{issue_data['description']}*")
    
    st.markdown(f"**Coverage**: {issue_data['total_interviews']} interviews, {len(issue_data['meta_themes'])} meta-themes, {issue_data['total_themes']} themes")
    
    # Store the selected issue tag ID for use in tabs
    selected_issue_tag_id = issue_tag_id
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["📋 Meta-themes", "🌐 Theme Network", "📊 Statistics"])
    
    with tab1:
        # Display meta-themes
        sorted_meta_themes = sorted(
            issue_data['meta_themes'].items(),
            key=lambda x: x[1]['interviews'],
            reverse=True
        )
        
        for meta_theme_id, meta_data in sorted_meta_themes:
            with st.expander(f"**{meta_data['name']}** ({meta_data['interviews']} interviews, {len(meta_data['themes'])} themes)"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**{meta_data['description']}**")
                    st.divider()
                    
                    # Show themes
                    sorted_themes = sorted(
                        meta_data['themes'].items(),
                        key=lambda x: x[1]['interviews'],
                        reverse=True
                    )
                    
                    # Debug: Check if themes exist
                    if not sorted_themes:
                        st.warning("No themes found in this meta-theme")
                    else:
                        st.markdown(f"### Themes in this meta-theme ({len(sorted_themes)} total):")
                    
                    for theme_name, theme_data in sorted_themes:
                        # Don't use nested expanders - use a container instead
                        with st.container():
                            st.markdown(f"#### 📌 {theme_name}")
                            st.caption(f"*{theme_data['intensity']} intensity • {theme_data['interviews']} interviews*")
                            
                            # Make theme content expandable
                            with st.expander(f"View details and interviews for: {theme_name}"):
                                if theme_data['description']:
                                    st.write(theme_data['description'])
                            
                                # Show examples
                                if theme_data['examples']:
                                    st.markdown("**Key Evidence:**")
                                    for i, example in enumerate(theme_data['examples']):
                                        if example['quote']:
                                            st.info(f'"{example["quote"]}" - {example["turn"]}')
                                            
                                            # Button to view in context
                                            if st.button(f"View in Context", key=f"view_{example['interview_id']}_{example['turn']}_{i}"):
                                                st.session_state['view_interview'] = {
                                                    'interview_id': example['interview_id'],
                                                    'turn': int(example['turn'].split(':')[1]) if ':' in example['turn'] else None
                                                }
                                                st.switch_page("pages/2_📄_Interview_Viewer.py")
                                
                                # Show interview list
                                if theme_data['interviews'] > 0:
                                    st.divider()
                                    st.markdown(f"### 📚 All Interviews with this Theme")
                                
                                    # Collect all interviews with this theme
                                    theme_interviews = []
                                    for interview_id, interview in corpus_data['interviews'].items():
                                        for theme_obj in interview.get('annotation', {}).get('summary', {}).get('key_themes', []):
                                            if (isinstance(theme_obj, dict) and 
                                                theme_obj.get('theme') == theme_name and
                                                theme_obj.get('meta_theme') == meta_theme_id):
                                                
                                                # Get a snippet of the summary
                                                summary = interview.get('annotation', {}).get('summary', {}).get('overview', '')
                                                summary_snippet = summary[:150] + "..." if len(summary) > 150 else summary
                                                
                                                theme_interviews.append({
                                                    'id': interview_id,
                                                    'location': interview.get('annotation', {}).get('tags', {}).get('location', ['Unknown'])[0],
                                                    'date': interview.get('metadata', {}).get('date', 'Unknown date'),
                                                    'summary': summary_snippet
                                                })
                                                break
                                    
                                    # Display interview list
                                    for idx, int_data in enumerate(sorted(theme_interviews, key=lambda x: x['id'])):
                                        with st.container():
                                            st.markdown(f"#### Interview {int_data['id']}")
                                            col_a, col_b = st.columns([4, 1])
                                            with col_a:
                                                st.write(f"📍 {int_data['location']} • 📅 {int_data['date']}")
                                                st.caption(int_data['summary'])
                                            with col_b:
                                                if st.button("Open Interview", key=f"open_int_{theme_name}_{int_data['id']}_{idx}"):
                                                    st.session_state['view_interview'] = {
                                                        'interview_id': int_data['id']
                                                    }
                                                    st.switch_page("pages/2_📄_Interview_Viewer.py")
                                        if idx < len(theme_interviews) - 1:
                                            st.markdown("")  # Add spacing between interviews
                
                with col2:
                    st.markdown("#### Meta-theme Stats:")
                    st.metric("Interviews", meta_data['interviews'])
                    st.metric("Themes", len(meta_data['themes']))
                    
                    # Theme distribution
                    st.markdown("#### Theme Distribution:")
                    for theme_name, theme_data in sorted_themes[:5]:
                        st.write(f"**{theme_name}**: {theme_data['interviews']}")
    
    with tab2:
        # Network view - show how themes connect
        st.markdown("### Theme Relationships")
        st.info("This shows how different themes within this issue area relate to each other")
        
        # Create a simple network display
        for meta_theme_id, meta_data in sorted_meta_themes:
            st.markdown(f"#### {meta_data['name']}")
            theme_names = list(meta_data['themes'].keys())
            if len(theme_names) > 1:
                st.markdown("**Related themes:**")
                for i, theme in enumerate(theme_names):
                    if i < len(theme_names) - 1:
                        st.write(f"• {theme} ↔ {theme_names[i+1]}")
            else:
                st.write(f"• {theme_names[0]} (standalone)")
    
    with tab3:
        # Statistics view
        st.markdown("### Detailed Statistics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Meta-theme Breakdown")
            for meta_theme_id, meta_data in sorted_meta_themes:
                st.write(f"**{meta_data['name']}**")
                st.progress(meta_data['interviews'] / issue_data['total_interviews'])
                st.caption(f"{meta_data['interviews']} interviews ({meta_data['interviews']/issue_data['total_interviews']*100:.1f}%)")
        
        with col2:
            st.markdown("#### Theme Intensity Distribution")
            intensity_counts = defaultdict(int)
            for meta_data in issue_data['meta_themes'].values():
                for theme_data in meta_data['themes'].values():
                    intensity_counts[theme_data['intensity']] += 1
            
            for intensity, count in sorted(intensity_counts.items(), key=lambda x: x[1], reverse=True):
                st.write(f"**{intensity}**: {count} themes")

if __name__ == "__main__":
    main()