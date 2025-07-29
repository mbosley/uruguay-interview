"""
Uruguay Interview Research Platform - Home
"""

import streamlit as st

st.set_page_config(
    page_title="Uruguay Interview Research Platform",
    page_icon="🇺🇾",
    layout="wide"
)

def main():
    st.title("🇺🇾 Uruguay Interview Research Platform")
    st.markdown("**Explore citizen consultation interviews with AI-powered tools**")
    
    st.divider()
    
    # Platform overview
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("""
        ### 📚 About the Dataset
        
        This platform provides access to **35 citizen consultation interviews** conducted in Uruguay 
        on May 28-29, 2025. The interviews capture diverse perspectives on national and local priorities,
        covering topics from healthcare and education to security and infrastructure.
        
        ### 🛠️ Available Tools
        
        **🔬 Research Agent** - AI-powered research assistant for exploring specific questions
        - Ask complex research questions
        - Get synthesized insights with citations
        - Explore themes across multiple interviews
        
        **📚 Interview Browser** - Browse and filter all interviews
        - Filter by themes, locations, and demographics
        - Search across all interview content
        - Access full transcripts and summaries
        
        **📄 Interview Viewer** - Read individual interviews
        - View complete transcripts with speaker turns
        - See AI-generated summaries and key themes
        - Navigate to specific citations
        
        **🏷️ Theme Explorer** - Navigate the hierarchical theme structure
        - Explore by issue area → meta-theme → specific theme
        - See theme relationships and prevalence
        - Find interviews by theme
        
        **📊 Analytics Dashboard** - Statistical analysis of the corpus
        - Theme distribution and co-occurrence patterns
        - Geographic and demographic insights
        - Cross-cutting theme analysis
        """)
    
    with col2:
        st.markdown("### 📊 Corpus Statistics")
        
        # Try to load corpus data for stats
        try:
            import sys
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            sys.path.insert(0, parent_dir)
            from corpus_loader import load_enriched_corpus
            
            corpus_data = load_enriched_corpus()
            metadata = corpus_data.get('metadata', {})
            theme_consolidation = corpus_data.get('theme_consolidation', {})
            
            st.metric("Total Interviews", metadata.get('total_interviews', 35))
            st.metric("Total Turns", f"{metadata.get('total_turns', 5510):,}")
            st.metric("Unique Themes", 121)
            st.metric("Meta-themes", len(theme_consolidation.get('meta_themes', {})))
            st.metric("Issue Areas", len(theme_consolidation.get('metadata', {}).get('issue_tags', {})))
            
        except:
            # Fallback to static stats
            st.info("""
            - **35** Interviews
            - **5,510** Turns
            - **121** Unique Themes
            - **13** Meta-themes
            - **12** Issue Areas
            """)
        
        st.markdown("### 🚀 Getting Started")
        st.info("""
        1. **New to the platform?** Start with the Interview Browser to get an overview
        2. **Have a specific question?** Use the Research Agent for AI-powered analysis
        3. **Want to explore themes?** Visit the Theme Explorer for hierarchical navigation
        4. **Need statistics?** Check the Analytics Dashboard for corpus-wide insights
        """)
        
        st.markdown("### 📅 Data Collection")
        st.caption("Interviews conducted: May 28-29, 2025")
        st.caption("Locations: Multiple sites across Uruguay")

if __name__ == "__main__":
    main()