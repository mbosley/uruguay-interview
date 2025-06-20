"""
Interactive Enhanced Uruguay Interview Analysis Dashboard
Advanced research platform with dynamic filtering and linked visualizations
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path
import sys
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.database.connection import get_db
from src.database.models_enhanced import (
    Interview, ParticipantProfile, NarrativeFeatures, Priority, Turn,
    TurnFunctionalAnalysis, TurnContentAnalysis, TurnEmotionalAnalysis
)

# Configure page
st.set_page_config(
    page_title="Uruguay Interview Analysis - Interactive Research Platform",
    page_icon="🇺🇾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    .filter-section {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    .narrative-frame {
        padding: 8px;
        border-radius: 5px;
        margin: 3px 0;
        font-weight: bold;
        text-align: center;
    }
    .frame-decline { background-color: #ffebee; color: #c62828; }
    .frame-progress { background-color: #e8f5e8; color: #2e7d32; }
    .frame-stagnation { background-color: #fff3e0; color: #ef6c00; }
    .frame-mixed { background-color: #f3e5f5; color: #7b1fa2; }
    .quote-card {
        background-color: #f5f5f5;
        padding: 12px;
        border-left: 4px solid #2196f3;
        margin: 8px 0;
        border-radius: 0 8px 8px 0;
    }
    .confidence-high { border-left-color: #4caf50; }
    .confidence-medium { border-left-color: #ff9800; }
    .confidence-low { border-left-color: #f44336; }
    .stSelectbox > div > div { background-color: white; }
</style>
""", unsafe_allow_html=True)


class InteractiveDashboard:
    """Enhanced interactive dashboard with filtering and linked visualizations."""
    
    def __init__(self):
        self.db = get_db()
        self.setup_session_state()
    
    def setup_session_state(self):
        """Initialize session state for filters and selections."""
        if 'filters' not in st.session_state:
            st.session_state.filters = {
                'departments': [],
                'age_ranges': [],
                'narrative_frames': [],
                'locality_sizes': [],
                'confidence_threshold': 0.0,
                'gender': [],
                'selected_interviews': []
            }
        
        if 'selected_interview' not in st.session_state:
            st.session_state.selected_interview = None
    
    @st.cache_data(ttl=300)
    def load_comprehensive_data(_self):
        """Load all data with relationships."""
        with _self.db.get_session() as session:
            # Load interviews with relationships
            interviews = session.query(Interview).all()
            
            # Build comprehensive dataset
            data = []
            for interview in interviews:
                profile = interview.participant_profile
                narrative = interview.narrative_features
                priorities = interview.priorities
                
                # Count priorities by scope
                national_priorities = len([p for p in priorities if p.scope == 'national'])
                local_priorities = len([p for p in priorities if p.scope == 'local'])
                
                # Average emotional intensity
                avg_emotional_intensity = np.mean([p.emotional_intensity for p in priorities if p.emotional_intensity]) if priorities else None
                
                # Top priority themes
                priority_themes = [p.theme for p in priorities] if priorities else []
                
                data.append({
                    'interview_id': interview.interview_id,
                    'date': interview.date,
                    'location': interview.location,
                    'department': interview.department,
                    'municipality': interview.municipality,
                    'locality_size': interview.locality_size,
                    'duration_minutes': interview.duration_minutes,
                    'interviewer_ids': interview.interviewer_ids,
                    
                    # Participant profile
                    'age_range': profile.age_range if profile else None,
                    'gender': profile.gender if profile else None,
                    'occupation_sector': profile.occupation_sector if profile else None,
                    'organizational_affiliation': profile.organizational_affiliation if profile else None,
                    'profile_confidence': profile.profile_confidence if profile else None,
                    
                    # Narrative features
                    'dominant_frame': narrative.dominant_frame if narrative else None,
                    'temporal_orientation': narrative.temporal_orientation if narrative else None,
                    'government_responsibility': narrative.government_responsibility if narrative else None,
                    'individual_responsibility': narrative.individual_responsibility if narrative else None,
                    'structural_factors': narrative.structural_factors if narrative else None,
                    'solution_orientation': narrative.solution_orientation if narrative else None,
                    'cultural_patterns': narrative.cultural_patterns_identified if narrative else [],
                    'narrative_confidence': narrative.narrative_confidence if narrative else None,
                    
                    # Priority aggregates
                    'national_priorities': national_priorities,
                    'local_priorities': local_priorities,
                    'total_priorities': len(priorities),
                    'avg_emotional_intensity': avg_emotional_intensity,
                    'priority_themes': priority_themes,
                })
            
            # Load priority details
            priorities_data = []
            for interview in interviews:
                for priority in interview.priorities:
                    priorities_data.append({
                        'interview_id': interview.interview_id,
                        'scope': priority.scope,
                        'rank': priority.rank,
                        'theme': priority.theme,
                        'specific_issues': priority.specific_issues,
                        'narrative_elaboration': priority.narrative_elaboration,
                        'emotional_intensity': priority.emotional_intensity,
                        'supporting_quotes': priority.supporting_quotes,
                        'confidence': priority.confidence,
                        'reasoning': priority.reasoning
                    })
            
            return pd.DataFrame(data), pd.DataFrame(priorities_data)
    
    def create_filter_sidebar(self, df):
        """Create interactive filter sidebar."""
        st.sidebar.title("🔍 Interactive Filters")
        st.sidebar.markdown("Filter the data to explore patterns")
        
        # Reset filters button
        if st.sidebar.button("🔄 Reset All Filters"):
            for key in st.session_state.filters:
                if isinstance(st.session_state.filters[key], list):
                    st.session_state.filters[key] = []
                else:
                    st.session_state.filters[key] = 0.0
        
        # Department filter
        departments = df['department'].dropna().unique()
        st.session_state.filters['departments'] = st.sidebar.multiselect(
            "🗺️ Departments",
            options=sorted(departments),
            default=st.session_state.filters['departments'],
            help="Select one or more departments"
        )
        
        # Age range filter
        age_ranges = df['age_range'].dropna().unique()
        st.session_state.filters['age_ranges'] = st.sidebar.multiselect(
            "👥 Age Ranges", 
            options=sorted(age_ranges),
            default=st.session_state.filters['age_ranges']
        )
        
        # Gender filter
        genders = df['gender'].dropna().unique()
        st.session_state.filters['gender'] = st.sidebar.multiselect(
            "⚧ Gender",
            options=sorted(genders),
            default=st.session_state.filters['gender']
        )
        
        # Narrative frame filter
        frames = df['dominant_frame'].dropna().unique()
        st.session_state.filters['narrative_frames'] = st.sidebar.multiselect(
            "📚 Narrative Frames",
            options=sorted(frames),
            default=st.session_state.filters['narrative_frames']
        )
        
        # Locality size filter
        localities = df['locality_size'].dropna().unique()
        st.session_state.filters['locality_sizes'] = st.sidebar.multiselect(
            "🏘️ Locality Size",
            options=sorted(localities),
            default=st.session_state.filters['locality_sizes']
        )
        
        # Confidence threshold
        st.session_state.filters['confidence_threshold'] = st.sidebar.slider(
            "🎯 Minimum Confidence",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.filters['confidence_threshold'],
            step=0.1,
            help="Filter by annotation confidence level"
        )
        
        # Show filter summary
        active_filters = sum(1 for f in st.session_state.filters.values() if f)
        if active_filters > 0:
            st.sidebar.success(f"✅ {active_filters} filters active")
        else:
            st.sidebar.info("ℹ️ No filters applied")
    
    def apply_filters(self, df):
        """Apply active filters to dataframe."""
        filtered_df = df.copy()
        
        filters = st.session_state.filters
        
        # Apply department filter
        if filters['departments']:
            filtered_df = filtered_df[filtered_df['department'].isin(filters['departments'])]
        
        # Apply age range filter
        if filters['age_ranges']:
            filtered_df = filtered_df[filtered_df['age_range'].isin(filters['age_ranges'])]
        
        # Apply gender filter
        if filters['gender']:
            filtered_df = filtered_df[filtered_df['gender'].isin(filters['gender'])]
        
        # Apply narrative frame filter
        if filters['narrative_frames']:
            filtered_df = filtered_df[filtered_df['dominant_frame'].isin(filters['narrative_frames'])]
        
        # Apply locality size filter
        if filters['locality_sizes']:
            filtered_df = filtered_df[filtered_df['locality_size'].isin(filters['locality_sizes'])]
        
        # Apply confidence threshold
        if filters['confidence_threshold'] > 0:
            filtered_df = filtered_df[
                (filtered_df['narrative_confidence'] >= filters['confidence_threshold']) |
                (filtered_df['narrative_confidence'].isna())
            ]
        
        return filtered_df
    
    def show_overview_metrics(self, df, filtered_df):
        """Enhanced overview metrics with filtering impact."""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total = len(df)
            filtered = len(filtered_df)
            st.metric(
                "Interviews", 
                filtered,
                delta=f"{filtered-total}" if filtered != total else None,
                help=f"Filtered from {total} total interviews"
            )
        
        with col2:
            profiles = filtered_df['profile_confidence'].notna().sum()
            st.metric("Participant Profiles", profiles)
        
        with col3:
            narratives = filtered_df['narrative_confidence'].notna().sum()
            st.metric("Narrative Features", narratives)
        
        with col4:
            avg_conf = filtered_df['narrative_confidence'].mean()
            st.metric(
                "Avg Confidence", 
                f"{avg_conf:.2f}" if pd.notna(avg_conf) else "N/A"
            )
        
        # Show filter impact
        if len(filtered_df) != len(df):
            filter_pct = (len(filtered_df) / len(df)) * 100
            st.info(f"📊 Showing {filter_pct:.1f}% of data ({len(filtered_df)}/{len(df)} interviews) based on active filters")
    
    def create_linked_narrative_analysis(self, filtered_df):
        """Interactive narrative analysis with click-to-filter."""
        st.subheader("📚 Interactive Narrative Frame Analysis")
        
        frames = filtered_df['dominant_frame'].value_counts()
        
        if not frames.empty:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Interactive pie chart
                fig = px.pie(
                    values=frames.values,
                    names=frames.index,
                    title="Narrative Frames Distribution (Click to Filter)",
                    color_discrete_map={
                        'decline': '#ffcdd2',
                        'progress': '#c8e6c9',
                        'stagnation': '#ffe0b2', 
                        'mixed': '#e1bee7',
                        'progress and decline': '#d1c4e9'
                    }
                )
                
                # Add click event handling hint
                fig.update_layout(
                    title_text="Narrative Frames Distribution<br><sub>Click slice to filter dashboard</sub>"
                )
                
                selected_points = st.plotly_chart(fig, use_container_width=True, key="narrative_frames_pie")
            
            with col2:
                st.markdown("**Frame Details:**")
                for frame, count in frames.items():
                    frame_class = f"frame-{frame.replace(' ', '-').replace('and', '').strip().lower()}"
                    pct = (count / len(filtered_df)) * 100
                    
                    # Make frames clickable to update filters
                    if st.button(f"{frame.title()}: {count} ({pct:.1f}%)", key=f"frame_{frame}"):
                        st.session_state.filters['narrative_frames'] = [frame]
                        st.rerun()
                    
                    st.markdown(f'<div class="narrative-frame {frame_class}">{frame.title()}: {count}</div>', 
                               unsafe_allow_html=True)
    
    def create_interactive_agency_analysis(self, filtered_df):
        """Interactive agency attribution with filtering."""
        st.subheader("🎭 Agency Attribution Analysis")
        
        # Filter out null values
        agency_df = filtered_df[['government_responsibility', 'individual_responsibility', 'structural_factors']].dropna()
        
        if not agency_df.empty:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Interactive box plot
                fig = go.Figure()
                
                fig.add_trace(go.Box(
                    y=agency_df['government_responsibility'],
                    name='Government',
                    marker_color='lightblue',
                    boxpoints='outliers'
                ))
                
                fig.add_trace(go.Box(
                    y=agency_df['individual_responsibility'],
                    name='Individual', 
                    marker_color='lightgreen',
                    boxpoints='outliers'
                ))
                
                fig.add_trace(go.Box(
                    y=agency_df['structural_factors'],
                    name='Structural',
                    marker_color='lightcoral',
                    boxpoints='outliers'
                ))
                
                fig.update_layout(
                    title="Agency Attribution Distribution",
                    yaxis_title="Responsibility Score (0-1)",
                    showlegend=True
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("**Average Scores:**")
                gov_avg = agency_df['government_responsibility'].mean()
                ind_avg = agency_df['individual_responsibility'].mean()
                str_avg = agency_df['structural_factors'].mean()
                
                st.metric("Government", f"{gov_avg:.2f}")
                st.metric("Individual", f"{ind_avg:.2f}")
                st.metric("Structural", f"{str_avg:.2f}")
                
                # Interpretation
                st.markdown("**Interpretation:**")
                if gov_avg > 0.7:
                    st.success("🏛️ High government responsibility")
                elif gov_avg > 0.5:
                    st.warning("🏛️ Moderate government responsibility")
                else:
                    st.info("🏛️ Low government responsibility")
    
    def create_interview_selector(self, filtered_df):
        """Interactive interview selection."""
        st.subheader("📄 Interview Explorer")
        
        # Interview selection
        interview_options = filtered_df['interview_id'].tolist()
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            selected_interview = st.selectbox(
                "Select Interview to Explore",
                options=interview_options,
                index=0 if interview_options else None,
                help="Choose an interview for detailed analysis"
            )
        
        with col2:
            if selected_interview:
                interview_data = filtered_df[filtered_df['interview_id'] == selected_interview].iloc[0]
                
                # Quick preview
                col2a, col2b, col2c = st.columns(3)
                with col2a:
                    st.metric("Location", interview_data['location'])
                with col2b:
                    st.metric("Frame", interview_data['dominant_frame'])
                with col2c:
                    st.metric("Priorities", interview_data['total_priorities'])
        
        return selected_interview
    
    def show_detailed_interview_analysis(self, interview_id, df):
        """Enhanced interview detail view."""
        interview_data = df[df['interview_id'] == interview_id].iloc[0]
        
        st.markdown(f"### 🔍 Interview {interview_id} - Detailed Analysis")
        
        # Tabbed interface for different aspects
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Overview", "👤 Participant", "📚 Narrative", "🎯 Priorities"])
        
        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Interview Metadata:**")
                st.write(f"📅 Date: {interview_data['date']}")
                st.write(f"📍 Location: {interview_data['location']}")
                st.write(f"🗺️ Department: {interview_data['department']}")
                st.write(f"🏘️ Municipality: {interview_data['municipality']}")
                st.write(f"⏱️ Duration: {interview_data['duration_minutes']} minutes")
                
                if interview_data['interviewer_ids']:
                    st.write(f"🎤 Interviewers: {', '.join(interview_data['interviewer_ids'])}")
            
            with col2:
                st.markdown("**Analysis Summary:**")
                st.write(f"🎯 Total Priorities: {interview_data['total_priorities']}")
                st.write(f"🏛️ National Priorities: {interview_data['national_priorities']}")
                st.write(f"🏠 Local Priorities: {interview_data['local_priorities']}")
                
                if interview_data['avg_emotional_intensity']:
                    st.write(f"😊 Avg Emotional Intensity: {interview_data['avg_emotional_intensity']:.2f}")
        
        with tab2:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Demographics:**")
                st.write(f"👥 Age Range: {interview_data['age_range']}")
                st.write(f"⚧ Gender: {interview_data['gender']}")
                st.write(f"💼 Occupation: {interview_data['occupation_sector']}")
                
                if interview_data['organizational_affiliation']:
                    st.write(f"🏢 Affiliation: {interview_data['organizational_affiliation']}")
            
            with col2:
                st.markdown("**Profile Quality:**")
                if interview_data['profile_confidence']:
                    confidence = interview_data['profile_confidence']
                    st.metric("Profile Confidence", f"{confidence:.2f}")
                    
                    if confidence >= 0.8:
                        st.success("🟢 High confidence profile")
                    elif confidence >= 0.6:
                        st.warning("🟡 Medium confidence profile") 
                    else:
                        st.error("🔴 Low confidence profile")
        
        with tab3:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Narrative Characteristics:**")
                st.write(f"📖 Dominant Frame: {interview_data['dominant_frame']}")
                st.write(f"⏰ Temporal Orientation: {interview_data['temporal_orientation']}")
                st.write(f"🎯 Solution Orientation: {interview_data['solution_orientation']}")
            
            with col2:
                st.markdown("**Agency Attribution:**")
                if interview_data['government_responsibility']:
                    st.metric("Government", f"{interview_data['government_responsibility']:.2f}")
                if interview_data['individual_responsibility']:
                    st.metric("Individual", f"{interview_data['individual_responsibility']:.2f}")
                if interview_data['structural_factors']:
                    st.metric("Structural", f"{interview_data['structural_factors']:.2f}")
            
            # Cultural patterns
            if interview_data['cultural_patterns']:
                st.markdown("**Cultural Patterns:**")
                for pattern in interview_data['cultural_patterns']:
                    st.write(f"• {pattern}")
        
        with tab4:
            # Load priority details for this interview
            with self.db.get_session() as session:
                interview_obj = session.query(Interview).filter_by(interview_id=interview_id).first()
                if interview_obj and interview_obj.priorities:
                    for priority in interview_obj.priorities:
                        st.markdown(f"**{priority.scope.title()} Priority #{priority.rank}: {priority.theme}**")
                        
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            if priority.narrative_elaboration:
                                st.write(priority.narrative_elaboration)
                            
                            if priority.supporting_quotes:
                                st.markdown("*Supporting quotes:*")
                                for quote in priority.supporting_quotes:
                                    st.markdown(f'<div class="quote-card">"{quote}"</div>', 
                                               unsafe_allow_html=True)
                        
                        with col2:
                            if priority.emotional_intensity:
                                st.metric("Emotional Intensity", f"{priority.emotional_intensity:.2f}")
                            if priority.confidence:
                                st.metric("Confidence", f"{priority.confidence:.2f}")
                        
                        st.markdown("---")


def main():
    """Main interactive dashboard application."""
    # Title and description
    st.title("🇺🇾 Uruguay Interview Analysis")
    st.markdown("### 🎯 Interactive Research Platform")
    st.markdown("*Dynamic exploration of citizen consultation data with advanced filtering and linked visualizations*")
    
    # Initialize dashboard
    dashboard = InteractiveDashboard()
    
    try:
        # Load data
        interview_df, priority_df = dashboard.load_comprehensive_data()
        
        # Create filter sidebar
        dashboard.create_filter_sidebar(interview_df)
        
        # Apply filters
        filtered_df = dashboard.apply_filters(interview_df)
        
        # Main content area
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Overview metrics
            dashboard.show_overview_metrics(interview_df, filtered_df)
            
        with col2:
            # Quick stats
            st.markdown("**Quick Stats:**")
            st.metric("Unique Departments", filtered_df['department'].nunique())
            st.metric("Avg Age Range", "50-64" if not filtered_df.empty else "N/A")
        
        # Main analysis sections
        st.markdown("---")
        
        # Narrative analysis
        dashboard.create_linked_narrative_analysis(filtered_df)
        
        st.markdown("---")
        
        # Agency analysis
        dashboard.create_interactive_agency_analysis(filtered_df)
        
        st.markdown("---")
        
        # Interview explorer
        selected_interview = dashboard.create_interview_selector(filtered_df)
        
        if selected_interview:
            st.markdown("---")
            dashboard.show_detailed_interview_analysis(selected_interview, filtered_df)
        
        # Footer
        st.markdown("---")
        st.markdown("*🚀 Interactive Dashboard v2.0 - Enhanced Research Platform*")
        
    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")
        st.exception(e)


if __name__ == "__main__":
    main()