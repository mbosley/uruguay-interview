"""
Enhanced Uruguay Interview Analysis Dashboard
Interactive exploration of comprehensive citizen consultation data
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.database.connection import get_db
from src.database.models_enhanced import (
    Interview, ParticipantProfile, NarrativeFeatures, Priority, Turn
)

# Configure page
st.set_page_config(
    page_title="Uruguay Interview Analysis - Enhanced",
    page_icon="🇺🇾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    .narrative-frame {
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
        font-weight: bold;
    }
    .frame-decline { background-color: #ffebee; color: #c62828; }
    .frame-progress { background-color: #e8f5e8; color: #2e7d32; }
    .frame-stagnation { background-color: #fff3e0; color: #ef6c00; }
    .frame-mixed { background-color: #f3e5f5; color: #7b1fa2; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_database_connection():
    """Get database connection (cached)."""
    return get_db()


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_enhanced_data():
    """Load comprehensive interview data."""
    db = get_database_connection()
    
    with db.get_session() as session:
        # Load all data
        interviews = session.query(Interview).all()
        profiles = session.query(ParticipantProfile).all()
        narratives = session.query(NarrativeFeatures).all()
        priorities = session.query(Priority).all()
        
        # Convert to DataFrames for analysis
        interview_data = []
        for interview in interviews:
            profile = interview.participant_profile
            narrative = interview.narrative_features
            
            interview_data.append({
                'interview_id': interview.interview_id,
                'date': interview.date,
                'location': interview.location,
                'department': interview.department,
                'municipality': interview.municipality,
                'locality_size': interview.locality_size,
                'duration_minutes': interview.duration_minutes,
                'age_range': profile.age_range if profile else None,
                'gender': profile.gender if profile else None,
                'occupation_sector': profile.occupation_sector if profile else None,
                'profile_confidence': profile.profile_confidence if profile else None,
                'dominant_frame': narrative.dominant_frame if narrative else None,
                'temporal_orientation': narrative.temporal_orientation if narrative else None,
                'government_responsibility': narrative.government_responsibility if narrative else None,
                'individual_responsibility': narrative.individual_responsibility if narrative else None,
                'structural_factors': narrative.structural_factors if narrative else None,
                'narrative_confidence': narrative.narrative_confidence if narrative else None,
            })
        
        # Priority data
        priority_data = []
        for priority in priorities:
            priority_data.append({
                'interview_id': priority.interview.interview_id,
                'scope': priority.scope,
                'rank': priority.rank,
                'theme': priority.theme,
                'emotional_intensity': priority.emotional_intensity,
                'confidence': priority.confidence
            })
        
        return pd.DataFrame(interview_data), pd.DataFrame(priority_data)


def show_overview_metrics(df):
    """Show overview metrics."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Interviews", len(df))
        
    with col2:
        participants = df['age_range'].notna().sum()
        st.metric("Participant Profiles", participants)
        
    with col3:
        narratives = df['dominant_frame'].notna().sum()
        st.metric("Narrative Features", narratives)
        
    with col4:
        avg_confidence = df['narrative_confidence'].mean()
        st.metric("Avg Confidence", f"{avg_confidence:.2f}" if pd.notna(avg_confidence) else "N/A")


def show_narrative_analysis(df):
    """Show narrative frame analysis."""
    st.subheader("📚 Narrative Frame Analysis")
    
    # Dominant frames distribution
    frames = df['dominant_frame'].value_counts().fillna(0)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if not frames.empty:
            fig = px.pie(
                values=frames.values,
                names=frames.index,
                title="Distribution of Dominant Narrative Frames",
                color_discrete_map={
                    'decline': '#ffcdd2',
                    'progress': '#c8e6c9', 
                    'stagnation': '#ffe0b2',
                    'mixed': '#e1bee7'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.write("**Frame Summary:**")
        for frame, count in frames.items():
            frame_class = f"frame-{frame.replace(' ', '-').lower()}"
            st.markdown(f'<div class="narrative-frame {frame_class}">{frame.title()}: {count}</div>', 
                       unsafe_allow_html=True)


def show_agency_attribution(df):
    """Show agency attribution analysis."""
    st.subheader("🎭 Agency Attribution Analysis")
    
    # Filter out null values
    agency_df = df[['government_responsibility', 'individual_responsibility', 'structural_factors']].dropna()
    
    if not agency_df.empty:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Box plot of agency attribution
            fig = go.Figure()
            
            fig.add_trace(go.Box(
                y=agency_df['government_responsibility'],
                name='Government',
                marker_color='lightblue'
            ))
            
            fig.add_trace(go.Box(
                y=agency_df['individual_responsibility'], 
                name='Individual',
                marker_color='lightgreen'
            ))
            
            fig.add_trace(go.Box(
                y=agency_df['structural_factors'],
                name='Structural',
                marker_color='lightcoral'
            ))
            
            fig.update_layout(
                title="Agency Attribution Distribution",
                yaxis_title="Responsibility Score (0-1)",
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.write("**Average Scores:**")
            st.metric("Government", f"{agency_df['government_responsibility'].mean():.2f}")
            st.metric("Individual", f"{agency_df['individual_responsibility'].mean():.2f}")  
            st.metric("Structural", f"{agency_df['structural_factors'].mean():.2f}")


def show_geographic_analysis(df):
    """Show geographic distribution."""
    st.subheader("🗺️ Geographic Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Department distribution
        dept_counts = df['department'].value_counts()
        if not dept_counts.empty:
            fig = px.bar(
                x=dept_counts.values,
                y=dept_counts.index,
                orientation='h',
                title="Interviews by Department",
                labels={'x': 'Count', 'y': 'Department'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Locality size distribution
        locality_counts = df['locality_size'].value_counts()
        if not locality_counts.empty:
            fig = px.pie(
                values=locality_counts.values,
                names=locality_counts.index,
                title="Distribution by Locality Size"
            )
            st.plotly_chart(fig, use_container_width=True)


def show_demographic_analysis(df):
    """Show demographic analysis."""
    st.subheader("👥 Demographic Analysis") 
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Age distribution
        age_counts = df['age_range'].value_counts()
        if not age_counts.empty:
            fig = px.bar(
                x=age_counts.index,
                y=age_counts.values,
                title="Age Range Distribution",
                labels={'x': 'Age Range', 'y': 'Count'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Gender distribution
        gender_counts = df['gender'].value_counts()
        if not gender_counts.empty:
            fig = px.pie(
                values=gender_counts.values,
                names=gender_counts.index,
                title="Gender Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)


def show_priority_analysis(priority_df):
    """Show priority theme analysis."""
    st.subheader("🎯 Priority Analysis")
    
    if not priority_df.empty:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Top themes
            theme_counts = priority_df['theme'].value_counts().head(10)
            fig = px.bar(
                x=theme_counts.values,
                y=theme_counts.index,
                orientation='h',
                title="Top 10 Priority Themes",
                labels={'x': 'Frequency', 'y': 'Theme'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.write("**Priority Scope:**")
            scope_counts = priority_df['scope'].value_counts()
            for scope, count in scope_counts.items():
                st.metric(scope.title(), count)
            
            st.write("**Average Emotional Intensity:**")
            avg_intensity = priority_df['emotional_intensity'].mean()
            st.metric("Intensity", f"{avg_intensity:.2f}" if pd.notna(avg_intensity) else "N/A")


def show_interview_detail(df, interview_id):
    """Show detailed view of specific interview."""
    interview_data = df[df['interview_id'] == interview_id].iloc[0]
    
    st.subheader(f"📄 Interview {interview_id} Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Basic Information:**")
        st.write(f"Date: {interview_data['date']}")
        st.write(f"Location: {interview_data['location']}")
        st.write(f"Department: {interview_data['department']}")
        st.write(f"Municipality: {interview_data['municipality']}")
        st.write(f"Duration: {interview_data['duration_minutes']} minutes")
        
        st.write("**Participant Profile:**")
        st.write(f"Age range: {interview_data['age_range']}")
        st.write(f"Gender: {interview_data['gender']}")
        st.write(f"Occupation: {interview_data['occupation_sector']}")
        st.write(f"Profile confidence: {interview_data['profile_confidence']}")
    
    with col2:
        st.write("**Narrative Features:**")
        st.write(f"Dominant frame: {interview_data['dominant_frame']}")
        st.write(f"Temporal orientation: {interview_data['temporal_orientation']}")
        st.write(f"Government responsibility: {interview_data['government_responsibility']}")
        st.write(f"Individual responsibility: {interview_data['individual_responsibility']}")
        st.write(f"Structural factors: {interview_data['structural_factors']}")
        st.write(f"Narrative confidence: {interview_data['narrative_confidence']}")


def main():
    """Main dashboard function."""
    st.title("🇺🇾 Uruguay Interview Analysis - Enhanced Dashboard")
    st.markdown("*Comprehensive analysis of citizen consultation data with enhanced schema*")
    
    # Load data
    try:
        interview_df, priority_df = load_enhanced_data()
        
        # Sidebar
        st.sidebar.title("Navigation")
        
        pages = {
            "Overview": "📊",
            "Narrative Analysis": "📚", 
            "Demographics": "👥",
            "Geographic Analysis": "🗺️",
            "Priority Analysis": "🎯",
            "Interview Details": "📄"
        }
        
        selected_page = st.sidebar.selectbox(
            "Select Analysis View",
            list(pages.keys()),
            format_func=lambda x: f"{pages[x]} {x}"
        )
        
        # Main content
        if selected_page == "Overview":
            show_overview_metrics(interview_df)
            st.markdown("---")
            show_narrative_analysis(interview_df)
            
        elif selected_page == "Narrative Analysis":
            show_narrative_analysis(interview_df)
            st.markdown("---")
            show_agency_attribution(interview_df)
            
        elif selected_page == "Demographics":
            show_demographic_analysis(interview_df)
            
        elif selected_page == "Geographic Analysis":
            show_geographic_analysis(interview_df)
            
        elif selected_page == "Priority Analysis":
            show_priority_analysis(priority_df)
            
        elif selected_page == "Interview Details":
            interview_ids = interview_df['interview_id'].unique()
            selected_interview = st.selectbox("Select Interview", interview_ids)
            if selected_interview:
                show_interview_detail(interview_df, selected_interview)
        
        # Footer
        st.markdown("---")
        st.markdown("*Enhanced dashboard powered by comprehensive annotation schema*")
        
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.write("Please ensure the enhanced database is properly loaded.")


if __name__ == "__main__":
    main()