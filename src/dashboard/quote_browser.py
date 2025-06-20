"""
Advanced Quote Browser and Narrative Analysis Tools
Comprehensive qualitative research features for the enhanced dashboard
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys
import re
from typing import List, Dict, Any, Optional
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.database.connection import get_db
from src.database.models_enhanced import Interview, Priority, Turn, KeyNarratives

class QuoteBrowser:
    """Advanced quote browsing and narrative analysis."""
    
    def __init__(self):
        self.db = get_db()
    
    @st.cache_data(ttl=300)
    def load_quotes_and_narratives(_self):
        """Load all quotes and narrative content."""
        with _self.db.get_session() as session:
            quotes_data = []
            
            # Load priority quotes
            interviews = session.query(Interview).all()
            
            for interview in interviews:
                for priority in interview.priorities:
                    if priority.supporting_quotes:
                        for quote in priority.supporting_quotes:
                            quotes_data.append({
                                'interview_id': interview.interview_id,
                                'source': 'priority',
                                'theme': priority.theme,
                                'scope': priority.scope,
                                'rank': priority.rank,
                                'quote': quote,
                                'emotional_intensity': priority.emotional_intensity,
                                'confidence': priority.confidence,
                                'department': interview.department,
                                'municipality': interview.municipality,
                                'age_range': interview.participant_profile.age_range if interview.participant_profile else None,
                                'gender': interview.participant_profile.gender if interview.participant_profile else None,
                                'dominant_frame': interview.narrative_features.dominant_frame if interview.narrative_features else None,
                                'narrative_elaboration': priority.narrative_elaboration
                            })
                
                # Load memorable quotes from key narratives
                if interview.key_narratives and interview.key_narratives.memorable_quotes:
                    for quote in interview.key_narratives.memorable_quotes:
                        quotes_data.append({
                            'interview_id': interview.interview_id,
                            'source': 'memorable',
                            'theme': 'Key Narrative',
                            'scope': 'narrative',
                            'rank': None,
                            'quote': quote,
                            'emotional_intensity': None,
                            'confidence': interview.key_narratives.narrative_confidence,
                            'department': interview.department,
                            'municipality': interview.municipality,
                            'age_range': interview.participant_profile.age_range if interview.participant_profile else None,
                            'gender': interview.participant_profile.gender if interview.participant_profile else None,
                            'dominant_frame': interview.narrative_features.dominant_frame if interview.narrative_features else None,
                            'narrative_elaboration': None
                        })
            
            # Load narrative content
            narrative_data = []
            for interview in interviews:
                if interview.key_narratives:
                    narrative_data.append({
                        'interview_id': interview.interview_id,
                        'identity_narrative': interview.key_narratives.identity_narrative,
                        'problem_narrative': interview.key_narratives.problem_narrative,
                        'hope_narrative': interview.key_narratives.hope_narrative,
                        'rhetorical_strategies': interview.key_narratives.rhetorical_strategies,
                        'department': interview.department,
                        'municipality': interview.municipality,
                        'age_range': interview.participant_profile.age_range if interview.participant_profile else None,
                        'gender': interview.participant_profile.gender if interview.participant_profile else None,
                        'dominant_frame': interview.narrative_features.dominant_frame if interview.narrative_features else None,
                        'temporal_orientation': interview.narrative_features.temporal_orientation if interview.narrative_features else None,
                        'cultural_patterns': interview.narrative_features.cultural_patterns_identified if interview.narrative_features else []
                    })
            
            return pd.DataFrame(quotes_data), pd.DataFrame(narrative_data)
    
    def create_quote_search_interface(self, quotes_df: pd.DataFrame):
        """Advanced quote search and filtering interface."""
        st.subheader("🔍 Advanced Quote Browser")
        st.markdown("*Search and explore quotes with multiple filters and context*")
        
        # Search and filter interface
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            search_text = st.text_input(
                "🔎 Search in quotes",
                placeholder="Enter keywords to search...",
                help="Search within quote text (case-insensitive)"
            )
        
        with col2:
            source_filter = st.multiselect(
                "Quote Source",
                options=['priority', 'memorable'],
                default=[],
                help="Filter by quote source type"
            )
        
        with col3:
            theme_filter = st.multiselect(
                "Priority Theme",
                options=sorted(quotes_df['theme'].dropna().unique()),
                default=[],
                help="Filter by priority theme"
            )
        
        # Additional filters
        col4, col5, col6 = st.columns(3)
        
        with col4:
            dept_filter = st.multiselect(
                "Department",
                options=sorted(quotes_df['department'].dropna().unique()),
                default=[]
            )
        
        with col5:
            frame_filter = st.multiselect(
                "Narrative Frame",
                options=sorted(quotes_df['dominant_frame'].dropna().unique()),
                default=[]
            )
        
        with col6:
            confidence_threshold = st.slider(
                "Min Confidence",
                min_value=0.0,
                max_value=1.0,
                value=0.0,
                step=0.1,
                help="Minimum annotation confidence"
            )
        
        # Apply filters
        filtered_quotes = self.apply_quote_filters(
            quotes_df, search_text, source_filter, theme_filter,
            dept_filter, frame_filter, confidence_threshold
        )
        
        return filtered_quotes
    
    def apply_quote_filters(self, df: pd.DataFrame, search_text: str, 
                           source_filter: List[str], theme_filter: List[str],
                           dept_filter: List[str], frame_filter: List[str],
                           confidence_threshold: float) -> pd.DataFrame:
        """Apply all quote filters."""
        filtered_df = df.copy()
        
        # Text search
        if search_text:
            mask = filtered_df['quote'].str.contains(search_text, case=False, na=False)
            filtered_df = filtered_df[mask]
        
        # Source filter
        if source_filter:
            filtered_df = filtered_df[filtered_df['source'].isin(source_filter)]
        
        # Theme filter
        if theme_filter:
            filtered_df = filtered_df[filtered_df['theme'].isin(theme_filter)]
        
        # Department filter
        if dept_filter:
            filtered_df = filtered_df[filtered_df['department'].isin(dept_filter)]
        
        # Frame filter
        if frame_filter:
            filtered_df = filtered_df[filtered_df['dominant_frame'].isin(frame_filter)]
        
        # Confidence filter
        if confidence_threshold > 0:
            filtered_df = filtered_df[
                (filtered_df['confidence'] >= confidence_threshold) |
                (filtered_df['confidence'].isna())
            ]
        
        return filtered_df
    
    def display_quote_results(self, quotes_df: pd.DataFrame):
        """Display filtered quote results with rich formatting."""
        if len(quotes_df) == 0:
            st.warning("No quotes match the current filters")
            return
        
        st.markdown(f"**Found {len(quotes_df)} quotes matching your criteria**")
        
        # Sorting options
        col1, col2 = st.columns([1, 3])
        with col1:
            sort_by = st.selectbox(
                "Sort by",
                options=['interview_id', 'emotional_intensity', 'confidence', 'theme'],
                index=0
            )
        
        # Sort quotes
        if sort_by in quotes_df.columns:
            quotes_df = quotes_df.sort_values(sort_by, ascending=False, na_position='last')
        
        # Display quotes
        for idx, quote_row in quotes_df.iterrows():
            self.display_single_quote(quote_row)
    
    def display_single_quote(self, quote_row):
        """Display a single quote with context and metadata."""
        # Determine confidence color
        confidence = quote_row.get('confidence')
        if pd.notna(confidence):
            if confidence >= 0.8:
                conf_class = "confidence-high"
                conf_icon = "🟢"
            elif confidence >= 0.6:
                conf_class = "confidence-medium"
                conf_icon = "🟡"
            else:
                conf_class = "confidence-low"
                conf_icon = "🔴"
        else:
            conf_class = "confidence-medium"
            conf_icon = "⚪"
        
        # Quote container
        confidence_display = f"{confidence:.2f}" if pd.notna(confidence) else "N/A"
        
        with st.container():
            st.markdown(f'''
            <div class="quote-card {conf_class}">
                <div style="font-size: 16px; margin-bottom: 8px;">
                    "{quote_row['quote']}"
                </div>
                <div style="font-size: 12px; color: #666;">
                    <strong>Interview {quote_row['interview_id']}</strong> • 
                    {quote_row['source'].title()} Quote • 
                    {quote_row['theme']} •
                    {quote_row['department']}, {quote_row['municipality']} •
                    {conf_icon} Confidence: {confidence_display}
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            # Expandable context
            with st.expander(f"📋 Context for Interview {quote_row['interview_id']}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Participant Profile:**")
                    st.write(f"Age: {quote_row['age_range']}")
                    st.write(f"Gender: {quote_row['gender']}")
                    st.write(f"Location: {quote_row['department']}")
                    
                    if quote_row['source'] == 'priority':
                        st.write(f"**Priority Context:**")
                        st.write(f"Scope: {quote_row['scope']}")
                        st.write(f"Rank: #{quote_row['rank']}")
                        if pd.notna(quote_row['emotional_intensity']):
                            emotional_display = f"{quote_row['emotional_intensity']:.2f}"
                            st.write(f"Emotional Intensity: {emotional_display}")
                
                with col2:
                    st.write(f"**Narrative Context:**")
                    st.write(f"Dominant Frame: {quote_row['dominant_frame']}")
                    
                    if quote_row['narrative_elaboration']:
                        st.write(f"**Context:**")
                        st.write(quote_row['narrative_elaboration'])
            
            st.markdown("---")
    
    def create_narrative_analysis_interface(self, narratives_df: pd.DataFrame):
        """Advanced narrative analysis interface."""
        st.subheader("📚 Narrative Analysis Explorer")
        st.markdown("*Explore identity, problem, and hope narratives across interviews*")
        
        if len(narratives_df) == 0:
            st.warning("No narrative data available")
            return
        
        # Narrative type selection
        narrative_types = {
            'identity_narrative': '👤 Identity Narratives',
            'problem_narrative': '🚨 Problem Narratives', 
            'hope_narrative': '🌟 Hope Narratives'
        }
        
        selected_type = st.selectbox(
            "Narrative Type",
            options=list(narrative_types.keys()),
            format_func=lambda x: narrative_types[x],
            help="Select type of narrative to explore"
        )
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            dept_filter = st.multiselect(
                "Department",
                options=sorted(narratives_df['department'].dropna().unique()),
                default=[]
            )
        
        with col2:
            frame_filter = st.multiselect(
                "Narrative Frame",
                options=sorted(narratives_df['dominant_frame'].dropna().unique()),
                default=[]
            )
        
        with col3:
            temporal_filter = st.multiselect(
                "Temporal Orientation",
                options=sorted(narratives_df['temporal_orientation'].dropna().unique()),
                default=[]
            )
        
        # Apply filters
        filtered_narratives = narratives_df.copy()
        if dept_filter:
            filtered_narratives = filtered_narratives[filtered_narratives['department'].isin(dept_filter)]
        if frame_filter:
            filtered_narratives = filtered_narratives[filtered_narratives['dominant_frame'].isin(frame_filter)]
        if temporal_filter:
            filtered_narratives = filtered_narratives[filtered_narratives['temporal_orientation'].isin(temporal_filter)]
        
        # Display narratives
        self.display_narrative_results(filtered_narratives, selected_type)
    
    def display_narrative_results(self, narratives_df: pd.DataFrame, narrative_type: str):
        """Display narrative analysis results."""
        if len(narratives_df) == 0:
            st.warning("No narratives match the current filters")
            return
        
        st.markdown(f"**Found {len(narratives_df)} narratives matching your criteria**")
        
        # Display each narrative
        for idx, narrative_row in narratives_df.iterrows():
            narrative_text = narrative_row.get(narrative_type)
            
            if pd.notna(narrative_text) and narrative_text.strip():
                with st.container():
                    # Narrative header
                    st.markdown(f"### Interview {narrative_row['interview_id']}")
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        # Main narrative text
                        st.markdown(f'<div class="quote-card" style="margin: 10px 0;">{narrative_text}</div>', 
                                   unsafe_allow_html=True)
                    
                    with col2:
                        # Context information
                        st.markdown("**Context:**")
                        st.write(f"📍 {narrative_row['department']}")
                        st.write(f"👥 {narrative_row['age_range']}")
                        st.write(f"⚧ {narrative_row['gender']}")
                        st.write(f"📖 {narrative_row['dominant_frame']}")
                        st.write(f"⏰ {narrative_row['temporal_orientation']}")
                        
                        # Cultural patterns
                        if narrative_row['cultural_patterns']:
                            st.write(f"🎭 Cultural patterns:")
                            for pattern in narrative_row['cultural_patterns']:
                                st.write(f"• {pattern}")
                    
                    # Rhetorical strategies
                    if narrative_row['rhetorical_strategies']:
                        with st.expander("🎭 Rhetorical Strategies"):
                            for strategy in narrative_row['rhetorical_strategies']:
                                st.write(f"• {strategy}")
                    
                    st.markdown("---")
    
    def create_cultural_patterns_analysis(self, narratives_df: pd.DataFrame):
        """Analyze cultural patterns across interviews."""
        st.subheader("🎭 Cultural Patterns Analysis")
        st.markdown("*Explore recurring cultural themes and patterns*")
        
        # Extract all cultural patterns
        all_patterns = []
        pattern_contexts = {}
        
        for idx, row in narratives_df.iterrows():
            if row['cultural_patterns']:
                for pattern in row['cultural_patterns']:
                    all_patterns.append(pattern)
                    if pattern not in pattern_contexts:
                        pattern_contexts[pattern] = []
                    pattern_contexts[pattern].append({
                        'interview_id': row['interview_id'],
                        'department': row['department'],
                        'dominant_frame': row['dominant_frame'],
                        'age_range': row['age_range']
                    })
        
        if not all_patterns:
            st.warning("No cultural patterns found in the data")
            return
        
        # Pattern frequency analysis
        pattern_counts = pd.Series(all_patterns).value_counts()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Pattern frequency chart
            fig = px.bar(
                x=pattern_counts.values,
                y=pattern_counts.index,
                orientation='h',
                title="Cultural Pattern Frequency",
                labels={'x': 'Frequency', 'y': 'Cultural Pattern'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("**Most Common Patterns:**")
            for pattern, count in pattern_counts.head(10).items():
                st.write(f"• **{pattern}**: {count} interviews")
        
        # Pattern details
        st.markdown("### Pattern Context Analysis")
        
        selected_pattern = st.selectbox(
            "Select Pattern to Explore",
            options=list(pattern_counts.index),
            help="Choose a cultural pattern to see detailed context"
        )
        
        if selected_pattern and selected_pattern in pattern_contexts:
            contexts = pattern_contexts[selected_pattern]
            
            st.markdown(f"**Pattern: {selected_pattern}**")
            st.markdown(f"*Appears in {len(contexts)} interviews*")
            
            # Context breakdown
            context_df = pd.DataFrame(contexts)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                dept_dist = context_df['department'].value_counts()
                st.markdown("**By Department:**")
                for dept, count in dept_dist.items():
                    st.write(f"• {dept}: {count}")
            
            with col2:
                frame_dist = context_df['dominant_frame'].value_counts()
                st.markdown("**By Narrative Frame:**")
                for frame, count in frame_dist.items():
                    st.write(f"• {frame}: {count}")
            
            with col3:
                age_dist = context_df['age_range'].value_counts()
                st.markdown("**By Age Range:**")
                for age, count in age_dist.items():
                    st.write(f"• {age}: {count}")


def show_quote_browser_page():
    """Main function to display quote browser page."""
    st.title("💬 Quote Browser & Narrative Analysis")
    st.markdown("*Advanced qualitative research tools for exploring quotes and narratives*")
    
    browser = QuoteBrowser()
    
    try:
        # Load data
        quotes_df, narratives_df = browser.load_quotes_and_narratives()
        
        # Navigation tabs
        tab1, tab2, tab3 = st.tabs([
            "🔍 Quote Browser",
            "📚 Narrative Analysis", 
            "🎭 Cultural Patterns"
        ])
        
        with tab1:
            filtered_quotes = browser.create_quote_search_interface(quotes_df)
            browser.display_quote_results(filtered_quotes)
        
        with tab2:
            browser.create_narrative_analysis_interface(narratives_df)
        
        with tab3:
            browser.create_cultural_patterns_analysis(narratives_df)
            
    except Exception as e:
        st.error(f"Error loading quote browser: {str(e)}")
        st.exception(e)