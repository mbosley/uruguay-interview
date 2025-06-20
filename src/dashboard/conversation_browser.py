"""
Conversation-Style Interview Browser
Polished, focused interface for browsing interviews as chat conversations
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import sys
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.database.connection import get_db
from src.database.models_enhanced import Interview, Turn, TurnFunctionalAnalysis, TurnContentAnalysis, TurnEmotionalAnalysis

# Configure page
st.set_page_config(
    page_title="Uruguay Conversations",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Enhanced CSS for chat-style interface
st.markdown("""
<style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main container */
    .main-container {
        max-width: 900px;
        margin: 0 auto;
        padding: 20px;
    }
    
    /* Chat message bubbles */
    .message-bubble {
        margin: 15px 0;
        padding: 15px 20px;
        border-radius: 18px;
        max-width: 70%;
        position: relative;
        cursor: pointer;
        transition: all 0.2s ease;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .message-bubble:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0,0,0,0.15);
    }
    
    /* Interviewer messages (left side) */
    .interviewer-message {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        color: #1565c0;
        margin-right: auto;
        border-bottom-left-radius: 4px;
    }
    
    /* Participant messages (right side) */
    .participant-message {
        background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%);
        color: #4a148c;
        margin-left: auto;
        border-bottom-right-radius: 4px;
        text-align: left;
    }
    
    /* Message metadata */
    .message-meta {
        font-size: 11px;
        opacity: 0.7;
        margin-top: 8px;
        font-weight: 500;
    }
    
    /* Turn analysis panel */
    .analysis-panel {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        border-left: 4px solid #2196f3;
        font-size: 14px;
    }
    
    .analysis-section {
        margin: 15px 0;
        padding: 12px;
        background: white;
        border-radius: 8px;
        border-left: 3px solid #4caf50;
    }
    
    /* Interview header */
    .interview-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        color: white;
        padding: 25px;
        border-radius: 16px;
        margin-bottom: 20px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(30, 58, 138, 0.2);
    }
    
    /* Navigation */
    .nav-button {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        color: white;
        padding: 12px 24px;
        border-radius: 25px;
        border: none;
        cursor: pointer;
        font-weight: 600;
        transition: all 0.2s ease;
        margin: 0 5px;
    }
    
    .nav-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(79, 70, 229, 0.3);
    }
    
    /* Statistics cards */
    .stat-card {
        background: white;
        padding: 15px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    
    .stat-number {
        font-size: 24px;
        font-weight: bold;
        color: #1565c0;
    }
    
    .stat-label {
        font-size: 12px;
        color: #666;
        margin-top: 5px;
    }
    
    /* Confidence indicators */
    .confidence-high { border-left-color: #4caf50; }
    .confidence-medium { border-left-color: #ff9800; }
    .confidence-low { border-left-color: #f44336; }
    
    /* Emotional indicators */
    .emotion-positive { background-color: #e8f5e8; }
    .emotion-negative { background-color: #ffebee; }
    .emotion-neutral { background-color: #f5f5f5; }
    
    /* Function indicators */
    .function-question { border-left-color: #2196f3; }
    .function-response { border-left-color: #4caf50; }
    .function-clarification { border-left-color: #ff9800; }
    .function-elaboration { border-left-color: #9c27b0; }
</style>
""", unsafe_allow_html=True)


class ConversationBrowser:
    """Polished conversation-style interview browser."""
    
    def __init__(self):
        self.db = get_db()
        self.setup_session_state()
    
    def setup_session_state(self):
        """Initialize session state."""
        if 'selected_interview' not in st.session_state:
            st.session_state.selected_interview = None
        if 'expanded_turns' not in st.session_state:
            st.session_state.expanded_turns = set()
    
    @st.cache_data(ttl=300)
    def load_interview_list(_self):
        """Load list of available interviews."""
        with _self.db.get_session() as session:
            interviews = session.query(Interview).all()
            
            interview_list = []
            for interview in interviews:
                # Get basic stats
                turn_count = len(interview.turns) if interview.turns else 0
                has_narrative = interview.narrative_features is not None
                
                interview_list.append({
                    'interview_id': interview.interview_id,
                    'date': interview.date,
                    'location': interview.location,
                    'department': interview.department,
                    'municipality': interview.municipality,
                    'duration_minutes': interview.duration_minutes,
                    'turn_count': turn_count,
                    'has_narrative': has_narrative,
                    'dominant_frame': interview.narrative_features.dominant_frame if has_narrative else None,
                    'age_range': interview.participant_profile.age_range if interview.participant_profile else None,
                    'gender': interview.participant_profile.gender if interview.participant_profile else None
                })
            
            return pd.DataFrame(interview_list)
    
    @st.cache_data(ttl=300)
    def load_conversation_data(_self, interview_id: str):
        """Load full conversation data for an interview."""
        with _self.db.get_session() as session:
            interview = session.query(Interview).filter_by(interview_id=interview_id).first()
            
            if not interview:
                return None, None
            
            # Interview metadata
            interview_data = {
                'interview_id': interview.interview_id,
                'date': interview.date,
                'location': interview.location,
                'department': interview.department,
                'municipality': interview.municipality,
                'duration_minutes': interview.duration_minutes,
                'participant_profile': {
                    'age_range': interview.participant_profile.age_range if interview.participant_profile else None,
                    'gender': interview.participant_profile.gender if interview.participant_profile else None,
                    'occupation_sector': interview.participant_profile.occupation_sector if interview.participant_profile else None,
                    'profile_confidence': interview.participant_profile.profile_confidence if interview.participant_profile else None
                },
                'narrative_features': {
                    'dominant_frame': interview.narrative_features.dominant_frame if interview.narrative_features else None,
                    'temporal_orientation': interview.narrative_features.temporal_orientation if interview.narrative_features else None,
                    'government_responsibility': interview.narrative_features.government_responsibility if interview.narrative_features else None,
                    'individual_responsibility': interview.narrative_features.individual_responsibility if interview.narrative_features else None
                } if interview.narrative_features else None
            }
            
            # Conversation turns
            turns_data = []
            for turn in sorted(interview.turns, key=lambda x: x.turn_id):
                turn_info = {
                    'turn_id': turn.turn_id,
                    'speaker': turn.speaker,
                    'text': turn.text or f"Turn {turn.turn_id}",
                    'significance': turn.turn_significance,
                    'functional_analysis': {
                        'primary_function': turn.functional_analysis.primary_function if turn.functional_analysis else None,
                        'secondary_functions': turn.functional_analysis.secondary_functions if turn.functional_analysis else [],
                        'function_confidence': turn.functional_analysis.function_confidence if turn.functional_analysis else None,
                        'reasoning': turn.functional_analysis.reasoning if turn.functional_analysis else None
                    } if turn.functional_analysis else None,
                    'content_analysis': {
                        'topics': turn.content_analysis.topics if turn.content_analysis else [],
                        'geographic_scope': turn.content_analysis.geographic_scope if turn.content_analysis else [],
                        'temporal_reference': turn.content_analysis.temporal_reference if turn.content_analysis else None,
                        'topic_narrative': turn.content_analysis.topic_narrative if turn.content_analysis else None,
                        'reasoning': turn.content_analysis.reasoning if turn.content_analysis else None
                    } if turn.content_analysis else None,
                    'emotional_analysis': {
                        'emotional_valence': turn.emotional_analysis.emotional_valence if turn.emotional_analysis else None,
                        'emotional_intensity': turn.emotional_analysis.emotional_intensity if turn.emotional_analysis else None,
                        'specific_emotions': turn.emotional_analysis.specific_emotions if turn.emotional_analysis else [],
                        'emotional_narrative': turn.emotional_analysis.emotional_narrative if turn.emotional_analysis else None,
                        'reasoning': turn.emotional_analysis.reasoning if turn.emotional_analysis else None
                    } if turn.emotional_analysis else None
                }
                turns_data.append(turn_info)
            
            return interview_data, turns_data
    
    def show_interview_selector(self):
        """Show polished interview selection interface."""
        st.markdown('<div class="main-container">', unsafe_allow_html=True)
        
        # Header
        st.markdown("""
        <div class="interview-header">
            <h1>💬 Uruguay Conversations</h1>
            <p>Explore citizen consultation interviews as natural conversations</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Load interview list
        interviews_df = self.load_interview_list()
        
        if len(interviews_df) == 0:
            st.error("No interviews available")
            return
        
        # Quick stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{len(interviews_df)}</div>
                <div class="stat-label">Total Interviews</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            departments = interviews_df['department'].nunique()
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{departments}</div>
                <div class="stat-label">Departments</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            total_turns = interviews_df['turn_count'].sum()
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{total_turns}</div>
                <div class="stat-label">Total Turns</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            avg_duration = interviews_df['duration_minutes'].mean()
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{avg_duration:.0f}min</div>
                <div class="stat-label">Avg Duration</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Interview selection
        st.markdown("### 📋 Select an Interview to Explore")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            dept_filter = st.selectbox(
                "Department",
                options=['All'] + sorted(interviews_df['department'].dropna().unique()),
                index=0
            )
        
        with col2:
            frame_filter = st.selectbox(
                "Narrative Frame", 
                options=['All'] + sorted(interviews_df['dominant_frame'].dropna().unique()),
                index=0
            )
        
        with col3:
            sort_by = st.selectbox(
                "Sort by",
                options=['Interview ID', 'Date', 'Turn Count', 'Duration'],
                index=0
            )
        
        # Apply filters
        filtered_df = interviews_df.copy()
        if dept_filter != 'All':
            filtered_df = filtered_df[filtered_df['department'] == dept_filter]
        if frame_filter != 'All':
            filtered_df = filtered_df[filtered_df['dominant_frame'] == frame_filter]
        
        # Sort
        sort_column_map = {
            'Interview ID': 'interview_id',
            'Date': 'date', 
            'Turn Count': 'turn_count',
            'Duration': 'duration_minutes'
        }
        sort_column = sort_column_map[sort_by]
        filtered_df = filtered_df.sort_values(sort_column, ascending=False)
        
        # Display interview cards
        st.markdown(f"**Found {len(filtered_df)} interviews**")
        
        for idx, interview in filtered_df.iterrows():
            self.show_interview_card(interview)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def show_interview_card(self, interview):
        """Show a polished interview card."""
        with st.container():
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.markdown(f"**Interview {interview['interview_id']}**")
                st.markdown(f"📍 {interview['location']}")
                st.markdown(f"📅 {interview['date']}")
            
            with col2:
                if interview['dominant_frame']:
                    frame_color = {
                        'decline': '🔴',
                        'progress': '🟢', 
                        'stagnation': '🟡',
                        'mixed': '🟣'
                    }.get(interview['dominant_frame'], '⚪')
                    st.markdown(f"{frame_color} {interview['dominant_frame'].title()}")
                
                if interview['age_range'] and interview['gender']:
                    st.markdown(f"👥 {interview['age_range']}, {interview['gender']}")
                
                st.markdown(f"💬 {interview['turn_count']} turns • ⏱️ {interview['duration_minutes']}min")
            
            with col3:
                if st.button(f"Open Chat", key=f"open_{interview['interview_id']}", use_container_width=True):
                    st.session_state.selected_interview = interview['interview_id']
                    st.rerun()
            
            st.markdown("---")
    
    def show_conversation_interface(self, interview_id: str):
        """Show the main conversation interface."""
        st.markdown('<div class="main-container">', unsafe_allow_html=True)
        
        # Load conversation data
        interview_data, turns_data = self.load_conversation_data(interview_id)
        
        if not interview_data or not turns_data:
            st.error("Could not load interview data")
            return
        
        # Header with interview info
        self.show_conversation_header(interview_data)
        
        # Back button
        if st.button("← Back to Interview List", key="back_button"):
            st.session_state.selected_interview = None
            st.rerun()
        
        # Conversation flow
        st.markdown("### 💬 Conversation")
        
        for turn in turns_data:
            self.show_message_bubble(turn, interview_id)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def show_conversation_header(self, interview_data):
        """Show conversation header with key info."""
        profile = interview_data['participant_profile']
        narrative = interview_data['narrative_features']
        
        st.markdown(f"""
        <div class="interview-header">
            <h2>💬 Interview {interview_data['interview_id']}</h2>
            <p>{interview_data['location']} • {interview_data['date']} • {interview_data['duration_minutes']} minutes</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Quick insights
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if profile and profile['age_range']:
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-number">{profile['age_range']}</div>
                    <div class="stat-label">Age Range</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            if narrative and narrative['dominant_frame']:
                frame_emoji = {
                    'decline': '📉',
                    'progress': '📈',
                    'stagnation': '➡️',
                    'mixed': '🔄'
                }.get(narrative['dominant_frame'], '❓')
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-number">{frame_emoji}</div>
                    <div class="stat-label">{narrative['dominant_frame'].title()}</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col3:
            if narrative and narrative['government_responsibility']:
                gov_resp = narrative['government_responsibility']
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-number">{gov_resp:.1f}</div>
                    <div class="stat-label">Gov Responsibility</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col4:
            if profile and profile['profile_confidence']:
                conf = profile['profile_confidence']
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-number">{conf:.1f}</div>
                    <div class="stat-label">Profile Confidence</div>
                </div>
                """, unsafe_allow_html=True)
    
    def show_message_bubble(self, turn, interview_id):
        """Show a chat-style message bubble."""
        # Determine speaker style
        is_participant = turn['speaker'] == 'participant'
        bubble_class = 'participant-message' if is_participant else 'interviewer-message'
        
        # Get function and emotion for styling
        function = turn['functional_analysis']['primary_function'] if turn['functional_analysis'] else 'unknown'
        emotion = turn['emotional_analysis']['emotional_valence'] if turn['emotional_analysis'] else 'neutral'
        
        # Speaker icon
        speaker_icon = "👤" if is_participant else "🎤"
        speaker_label = "Participant" if is_participant else "Interviewer"
        
        # Message content
        message_text = turn['text'] if turn['text'] else f"Turn {turn['turn_id']} - Click to see analysis"
        
        # Expandable state
        turn_key = f"{interview_id}_{turn['turn_id']}"
        is_expanded = turn_key in st.session_state.expanded_turns
        
        # Message bubble with clickable functionality
        with st.container():
            # Create expandable section
            with st.expander(f"{speaker_icon} {speaker_label} - Turn {turn['turn_id']}", expanded=False):
                # Message content
                st.markdown(f"""
                <div class="message-bubble {bubble_class} function-{function}">
                    <div style="line-height: 1.4; font-size: 16px;">
                        {message_text}
                    </div>
                    <div class="message-meta">
                        {function.replace('_', ' ').title()}
                        {f" • {emotion.title()}" if emotion != 'neutral' else ""}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Show detailed analysis
                self.show_turn_analysis(turn)
    
    def show_turn_analysis(self, turn):
        """Show detailed turn analysis in clean format."""
        # Functional analysis
        if turn['functional_analysis']:
            func = turn['functional_analysis']
            st.markdown("**🎯 Function Analysis**")
            st.write(f"**Primary Function:** {func['primary_function'].replace('_', ' ').title()}")
            
            if func['secondary_functions']:
                st.write(f"**Secondary Functions:** {', '.join(func['secondary_functions'])}")
            
            if func['function_confidence']:
                st.write(f"**Confidence:** {func['function_confidence']:.2f}")
            
            if func['reasoning']:
                st.write(f"**Reasoning:** {func['reasoning']}")
            
            st.markdown("---")
        
        # Content analysis
        if turn['content_analysis']:
            content = turn['content_analysis']
            st.markdown("**📝 Content Analysis**")
            
            if content['topics']:
                st.write(f"**Topics:** {', '.join(content['topics'])}")
            
            if content['geographic_scope']:
                st.write(f"**Geographic Scope:** {', '.join(content['geographic_scope'])}")
            
            if content['temporal_reference']:
                st.write(f"**Time Reference:** {content['temporal_reference']}")
            
            if content['topic_narrative']:
                st.write(f"**Narrative:** {content['topic_narrative']}")
            
            st.markdown("---")
        
        # Emotional analysis
        if turn['emotional_analysis']:
            emotion = turn['emotional_analysis']
            st.markdown("**😊 Emotional Analysis**")
            
            if emotion['emotional_valence']:
                st.write(f"**Valence:** {emotion['emotional_valence'].title()}")
            
            if emotion['emotional_intensity']:
                st.write(f"**Intensity:** {emotion['emotional_intensity']:.2f}")
            
            if emotion['specific_emotions']:
                st.write(f"**Emotions:** {', '.join(emotion['specific_emotions'])}")
            
            if emotion['emotional_narrative']:
                st.write(f"**Narrative:** {emotion['emotional_narrative']}")


def main():
    """Main conversation browser application."""
    browser = ConversationBrowser()
    
    try:
        # Check if interview is selected
        if st.session_state.selected_interview:
            browser.show_conversation_interface(st.session_state.selected_interview)
        else:
            browser.show_interview_selector()
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.exception(e)


if __name__ == "__main__":
    main()