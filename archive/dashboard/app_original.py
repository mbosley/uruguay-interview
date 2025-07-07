"""
Uruguay Interview Analysis Dashboard
Interactive exploration of citizen consultation data
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.database.repository import InterviewRepository
from src.database.connection import DatabaseConnection
from src.database.models import Interview
from src.config.config_loader import get_config
from src.dashboard.conversation_view import show_conversation_flow

# Configure page
st.set_page_config(
    page_title="Uruguay Interview Analysis",
    page_icon="🇺🇾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 18px;
    }
    .priority-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_database_connection():
    """Get database connection (cached)."""
    config = get_config()
    return DatabaseConnection(config.database.url)


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_interview_data():
    """Load all interview data from database."""
    db = get_database_connection()
    repo = InterviewRepository(db)
    
    with db.get_session() as session:
        interviews = repo.get_all(session)
        
        # Extract interview basic info for selection (not ORM objects)
        interview_list = []
        for interview in interviews:
            interview_list.append({
                'id': interview.id,
                'interview_id': interview.interview_id,
                'date': interview.date,
                'time': interview.time,
                'location': interview.location,
                'department': interview.department,
                'participant_count': interview.participant_count,
                'has_annotations': len(interview.annotations) > 0,
                'has_turns': len(interview.turns) > 0 if hasattr(interview, 'turns') else False
            })
        
        # Convert to dataframe for easier manipulation
        data = []
        if interviews:
            for interview in interviews:
                if interview.annotations:
                    for annotation in interview.annotations:
                        base_data = {
                            'interview_id': interview.id,
                            'date': interview.date,
                            'location': interview.location,
                            'department': interview.department,
                            'participant_count': interview.participant_count,
                            'overall_sentiment': annotation.overall_sentiment,
                            'dominant_emotion': annotation.dominant_emotion,
                            'confidence_score': annotation.confidence_score,
                            'model_used': f"{annotation.model_provider}/{annotation.model_name}"
                        }
                        data.append(base_data)
                else:
                    # Add interview without annotation
                    base_data = {
                        'interview_id': interview.id,
                        'date': interview.date,
                        'location': interview.location,
                        'department': interview.department,
                        'participant_count': interview.participant_count,
                        'overall_sentiment': None,
                        'dominant_emotion': None,
                        'confidence_score': 0.0,
                        'model_used': None
                    }
                    data.append(base_data)
        
        # Load priorities
        priorities = []
        if interviews:
            for interview in interviews:
                for priority in interview.priorities:
                    priorities.append({
                        'interview_id': interview.id,
                        'location': interview.location,
                        'department': interview.department,
                        'date': interview.date,
                        'scope': priority.scope,
                        'rank': priority.rank,
                        'category': priority.category,
                        'description': priority.description
                    })
        
        # Load themes
        themes = []
        if interviews:
            for interview in interviews:
                for theme in interview.themes:
                    themes.append({
                        'interview_id': interview.id,
                        'location': interview.location,
                        'department': interview.department,
                        'theme': theme.theme,
                        'frequency': theme.frequency
                    })
    
    return pd.DataFrame(data), pd.DataFrame(priorities), pd.DataFrame(themes), interview_list


def show_overview_dashboard(df_interviews, df_priorities, df_themes):
    """Display overview dashboard with key metrics."""
    st.title("🇺🇾 Uruguay Citizen Consultation Analysis")
    st.markdown("### Overview Dashboard")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Interviews",
            len(df_interviews),
            delta=None,
            help="Number of citizen interviews conducted"
        )
    
    with col2:
        avg_confidence = df_interviews['confidence_score'].mean()
        st.metric(
            "Avg Confidence",
            f"{avg_confidence:.2f}",
            delta=None,
            help="Average AI annotation confidence score"
        )
    
    with col3:
        total_priorities = len(df_priorities)
        st.metric(
            "Priorities Identified",
            total_priorities,
            delta=None,
            help="Total number of priorities across all interviews"
        )
    
    with col4:
        unique_themes = df_themes['theme'].nunique() if not df_themes.empty else 0
        st.metric(
            "Unique Themes",
            unique_themes,
            delta=None,
            help="Number of distinct themes identified"
        )
    
    # Sentiment distribution
    st.markdown("### Sentiment Analysis")
    col1, col2 = st.columns(2)
    
    with col1:
        if not df_interviews.empty:
            sentiment_counts = df_interviews['overall_sentiment'].value_counts()
            fig_sentiment = px.pie(
                values=sentiment_counts.values,
                names=sentiment_counts.index,
                title="Overall Sentiment Distribution",
                color_discrete_map={
                    'positive': '#2ecc71',
                    'negative': '#e74c3c',
                    'neutral': '#95a5a6',
                    'mixed': '#3498db'
                }
            )
            st.plotly_chart(fig_sentiment, use_container_width=True)
    
    with col2:
        if not df_interviews.empty and 'dominant_emotion' in df_interviews.columns:
            emotion_counts = df_interviews['dominant_emotion'].value_counts().head(10)
            fig_emotion = px.bar(
                x=emotion_counts.values,
                y=emotion_counts.index,
                orientation='h',
                title="Top Emotional Themes",
                labels={'x': 'Count', 'y': 'Emotion'}
            )
            st.plotly_chart(fig_emotion, use_container_width=True)
    
    # Geographic distribution
    st.markdown("### Geographic Distribution")
    if not df_interviews.empty:
        location_counts = df_interviews.groupby(['department', 'location']).size().reset_index(name='count')
        fig_geo = px.treemap(
            location_counts,
            path=['department', 'location'],
            values='count',
            title="Interviews by Location"
        )
        st.plotly_chart(fig_geo, use_container_width=True)


def show_priorities_analysis(df_priorities):
    """Display priorities analysis dashboard."""
    st.title("📊 Priorities Analysis")
    
    if df_priorities.empty:
        st.warning("No priorities data available")
        return
    
    # Filter by scope
    scope_filter = st.selectbox(
        "Select Priority Scope",
        ["All", "National", "Local"],
        key="priority_scope"
    )
    
    if scope_filter != "All":
        filtered_priorities = df_priorities[df_priorities['scope'] == scope_filter.lower()]
    else:
        filtered_priorities = df_priorities
    
    # Top categories
    col1, col2 = st.columns(2)
    
    with col1:
        category_counts = filtered_priorities['category'].value_counts().head(10)
        fig_categories = px.bar(
            x=category_counts.index,
            y=category_counts.values,
            title=f"Top {scope_filter} Priority Categories",
            labels={'x': 'Category', 'y': 'Count'}
        )
        st.plotly_chart(fig_categories, use_container_width=True)
    
    with col2:
        # Priority ranking distribution
        rank_counts = filtered_priorities['rank'].value_counts().sort_index()
        fig_ranks = px.line(
            x=rank_counts.index,
            y=rank_counts.values,
            title="Priority Rank Distribution",
            labels={'x': 'Rank', 'y': 'Count'},
            markers=True
        )
        st.plotly_chart(fig_ranks, use_container_width=True)
    
    # Detailed priority view
    st.markdown("### Priority Details")
    
    # Group by category and show top priorities
    for category in category_counts.index[:5]:
        with st.expander(f"{category.title()} Priorities"):
            cat_priorities = filtered_priorities[filtered_priorities['category'] == category].sort_values('rank')
            for _, priority in cat_priorities.head(5).iterrows():
                st.markdown(f"**Rank {priority['rank']}** ({priority['scope']}): {priority['description']}")
                st.markdown(f"*Location: {priority['location']}*")
                st.divider()


def show_themes_exploration(df_themes):
    """Display themes exploration dashboard."""
    st.title("🏷️ Themes Exploration")
    
    if df_themes.empty:
        st.warning("No themes data available")
        return
    
    # Theme frequency
    theme_freq = df_themes.groupby('theme')['frequency'].sum().sort_values(ascending=False).head(20)
    
    fig_themes = px.bar(
        x=theme_freq.values,
        y=theme_freq.index,
        orientation='h',
        title="Most Frequent Themes",
        labels={'x': 'Total Frequency', 'y': 'Theme'}
    )
    fig_themes.update_layout(height=600)
    st.plotly_chart(fig_themes, use_container_width=True)
    
    # Theme co-occurrence network (simplified)
    st.markdown("### Theme Distribution by Location")
    
    # Theme heatmap by department
    theme_dept = df_themes.groupby(['department', 'theme'])['frequency'].sum().reset_index()
    theme_pivot = theme_dept.pivot(index='theme', columns='department', values='frequency').fillna(0)
    
    # Select top themes for better visualization
    top_themes = theme_freq.head(15).index
    theme_pivot_top = theme_pivot.loc[theme_pivot.index.isin(top_themes)]
    
    fig_heatmap = px.imshow(
        theme_pivot_top,
        labels=dict(x="Department", y="Theme", color="Frequency"),
        title="Theme Frequency Heatmap by Department",
        aspect="auto"
    )
    fig_heatmap.update_layout(height=600)
    st.plotly_chart(fig_heatmap, use_container_width=True)


def show_interview_detail(interviews):
    """Display detailed interview viewer."""
    st.title("📄 Interview Detail Viewer")
    
    if not interviews:
        st.warning("No interviews available")
        return
    
    # Get database connection for this view
    db = get_database_connection()
    
    # Interview selector  
    interview_options = {f"{i['id']} - {i['location']} ({i['date']})": i['id'] for i in interviews}
    selected_key = st.selectbox(
        "Select an interview to view",
        options=list(interview_options.keys())
    )
    
    if selected_key:
        interview_id = interview_options[selected_key]
        
        # Load the specific interview with all relationships in a new session
        with db.get_session() as session:
            from sqlalchemy.orm import joinedload
            interview = session.query(Interview).options(
                joinedload(Interview.annotations),
                joinedload(Interview.priorities),
                joinedload(Interview.themes),
                joinedload(Interview.emotions)
            ).filter(Interview.id == interview_id).first()
            
            if not interview:
                st.error("Interview not found")
                return
            
            # Extract all data while session is active
            interview_data = {
                'date': interview.date,
                'time': interview.time,
                'location': interview.location,
                'department': interview.department,
                'participant_count': interview.participant_count,
                'word_count': interview.word_count,
                'raw_text': interview.raw_text,
                'annotations': [{
                    'overall_sentiment': ann.overall_sentiment,
                    'dominant_emotion': ann.dominant_emotion
                } for ann in interview.annotations],
                'priorities': [{
                    'scope': p.scope,
                    'rank': p.rank,
                    'category': p.category,
                    'description': p.description
                } for p in interview.priorities],
                'themes': [{
                    'theme': t.theme,
                    'frequency': t.frequency
                } for t in interview.themes],
                'emotions': [{
                    'type': e.type,
                    'intensity': e.intensity,
                    'context': e.context
                } for e in interview.emotions]
            }
        
        # Now display the data outside the session
        # Interview metadata
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**Date:** {interview_data['date']}")
            st.markdown(f"**Time:** {interview_data['time']}")
        with col2:
            st.markdown(f"**Location:** {interview_data['location']}")
            st.markdown(f"**Department:** {interview_data['department']}")
        with col3:
            st.markdown(f"**Participants:** {interview_data['participant_count']}")
            if interview_data['word_count']:
                st.markdown(f"**Word Count:** {interview_data['word_count']:,}")
        
        st.divider()
        
        # Annotation details
        if interview_data['annotations']:
            annotation = interview_data['annotations'][0]  # Use first annotation
            
            # Tabs for different aspects
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["Priorities", "Themes", "Emotions", "Conversation Flow", "Raw Text"])
            
            with tab1:
                st.markdown("### National Priorities")
                nat_priorities = [p for p in interview_data['priorities'] if p['scope'] == 'national']
                for priority in sorted(nat_priorities, key=lambda x: x['rank']):
                    st.markdown(f"**Rank {priority['rank']}:** {priority['category']}")
                    st.markdown(f"{priority['description']}")
                    st.divider()
                
                st.markdown("### Local Priorities")
                local_priorities = [p for p in interview_data['priorities'] if p['scope'] == 'local']
                for priority in sorted(local_priorities, key=lambda x: x['rank']):
                    st.markdown(f"**Rank {priority['rank']}:** {priority['category']}")
                    st.markdown(f"{priority['description']}")
                    st.divider()
            
            with tab2:
                st.markdown("### Identified Themes")
                for theme in interview_data['themes']:
                    st.markdown(f"- **{theme['theme']}** (frequency: {theme['frequency']})")
            
            with tab3:
                st.markdown("### Emotional Analysis")
                st.markdown(f"**Overall Sentiment:** {annotation['overall_sentiment']}")
                st.markdown(f"**Dominant Emotion:** {annotation['dominant_emotion']}")
                
                if interview_data['emotions']:
                    st.markdown("### Emotional Expressions")
                    for emotion in interview_data['emotions']:
                        st.markdown(f"- **{emotion['type']}** (intensity: {emotion['intensity']})")
                        if emotion.get('context'):
                            st.markdown(f"  Context: {emotion['context']}")
            
            with tab4:
                # Show conversation flow
                try:
                    db = get_database_connection()
                    with db.get_session() as conv_session:
                        # Check if interview has turns
                        from src.database.models import Turn
                        
                        turn_count = conv_session.query(Turn).filter_by(interview_id=interview_id).count()
                        
                        if turn_count > 0:
                            show_conversation_flow(interview_id, conv_session)
                        else:
                            st.info("No conversation turns available for this interview")
                except ImportError as e:
                    st.error(f"Import error: {e}")
                    st.info("Conversation flow feature requires the latest database models")
                except Exception as e:
                    st.error(f"Error loading conversation flow: {str(e)}")
                    st.info("Conversation flow feature requires turn-level data")
            
            with tab5:
                st.markdown("### Interview Text")
                if interview_data['raw_text']:
                    st.text_area(
                        "Full Interview Transcript",
                        value=interview_data['raw_text'],
                        height=400,
                        disabled=True
                    )
                else:
                    st.info("Raw text not available in database")


def main():
    """Main dashboard application."""
    # Sidebar navigation
    st.sidebar.title("Navigation")
    
    page = st.sidebar.radio(
        "Select Dashboard",
        ["Overview", "Priorities", "Themes", "Interview Detail"]
    )
    
    # Load data
    try:
        df_interviews, df_priorities, df_themes, interviews = load_interview_data()
        
        # Add filters in sidebar
        st.sidebar.markdown("### Filters")
        
        # Date range filter
        if not df_interviews.empty and 'date' in df_interviews.columns:
            date_range = st.sidebar.date_input(
                "Date Range",
                value=(df_interviews['date'].min(), df_interviews['date'].max()),
                key="date_range"
            )
        
        # Department filter
        if not df_interviews.empty:
            departments = ["All"] + sorted(df_interviews['department'].unique().tolist())
            selected_dept = st.sidebar.selectbox("Department", departments)
            
            if selected_dept != "All":
                df_interviews = df_interviews[df_interviews['department'] == selected_dept]
                df_priorities = df_priorities[df_priorities['department'] == selected_dept]
                df_themes = df_themes[df_themes['department'] == selected_dept]
                interviews = [i for i in interviews if i.department == selected_dept]
        
        # Display selected page
        if page == "Overview":
            show_overview_dashboard(df_interviews, df_priorities, df_themes)
        elif page == "Priorities":
            show_priorities_analysis(df_priorities)
        elif page == "Themes":
            show_themes_exploration(df_themes)
        elif page == "Interview Detail":
            show_interview_detail(interviews)
            
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.info("Make sure the database is populated with interview data.")


if __name__ == "__main__":
    main()