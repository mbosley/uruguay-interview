"""
Chat-Style Interview Interface
Focus on actual conversation text with expandable annotations
"""
import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.database.connection import get_db
from src.database.models_enhanced import Interview, Turn

# Configure page
st.set_page_config(
    page_title="Uruguay Conversations",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Chat-focused CSS
st.markdown("""
<style>
    /* Clean chat interface */
    .main > div {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 800px;
        margin: 0 auto;
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stSelectbox > label {display: none;}
    
    /* Chat message styles */
    .chat-message {
        margin: 8px 0;
        padding: 12px 16px;
        border-radius: 18px;
        max-width: 75%;
        clear: both;
        word-wrap: break-word;
        line-height: 1.4;
        font-size: 15px;
    }
    
    /* Interviewer messages (left, blue) */
    .interviewer {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        color: #0d47a1;
        float: left;
        border-bottom-left-radius: 4px;
        margin-right: 25%;
    }
    
    /* Participant messages (right, purple) */
    .participant {
        background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%);
        color: #4a148c;
        float: right;
        border-bottom-right-radius: 4px;
        margin-left: 25%;
        text-align: left;
    }
    
    /* Speaker labels */
    .speaker-label {
        font-size: 11px;
        font-weight: 600;
        opacity: 0.8;
        margin-bottom: 4px;
    }
    
    /* Message text */
    .message-text {
        font-size: 15px;
        line-height: 1.4;
    }
    
    /* Interview header */
    .interview-header {
        background: linear-gradient(135deg, #1565c0 0%, #1976d2 100%);
        color: white;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 24px;
        text-align: center;
    }
    
    /* Navigation */
    .nav-section {
        background: #f8f9fa;
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 20px;
    }
    
    /* Clear floats */
    .clearfix::after {
        content: "";
        display: table;
        clear: both;
    }
    
    /* Annotation panel */
    .annotation-panel {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 16px;
        margin: 8px 0;
        border-left: 4px solid #2196f3;
        font-size: 14px;
    }
    
    /* Interview stats */
    .stat-box {
        background: white;
        padding: 12px;
        border-radius: 8px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .stat-number {
        font-size: 20px;
        font-weight: bold;
        color: #1565c0;
    }
    
    .stat-label {
        font-size: 11px;
        color: #666;
        margin-top: 4px;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #1565c0 0%, #1976d2 100%);
        color: white;
        border: none;
        border-radius: 20px;
        padding: 8px 16px;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)


class ChatInterface:
    """Clean chat-focused interview interface."""
    
    def __init__(self):
        self.db = get_db()
        self.setup_session_state()
    
    def setup_session_state(self):
        """Initialize session state."""
        if 'selected_interview' not in st.session_state:
            st.session_state.selected_interview = None
    
    @st.cache_data(ttl=300)
    def get_interview_list(_self):
        """Get list of interviews with conversation text."""
        with _self.db.get_session() as session:
            interviews = session.query(Interview).all()
            
            interview_options = []
            for interview in interviews:
                # Count turns with actual text
                text_turns = sum(1 for turn in interview.turns if turn.text and turn.text.strip())
                
                interview_options.append({
                    'id': interview.interview_id,
                    'display': f"Interview {interview.interview_id} - {interview.location} ({text_turns} messages)",
                    'location': interview.location,
                    'date': interview.date,
                    'text_turns': text_turns,
                    'total_turns': len(interview.turns),
                    'frame': interview.narrative_features.dominant_frame if interview.narrative_features else None,
                    'age': interview.participant_profile.age_range if interview.participant_profile else None
                })
            
            # Sort by most conversation text
            return sorted(interview_options, key=lambda x: x['text_turns'], reverse=True)
    
    @st.cache_data(ttl=300) 
    def load_conversation(_self, interview_id: str):
        """Load conversation data for chat display."""
        with _self.db.get_session() as session:
            interview = session.query(Interview).filter_by(interview_id=interview_id).first()
            
            if not interview:
                return None, []
            
            # Interview metadata
            metadata = {
                'id': interview.interview_id,
                'location': interview.location,
                'date': interview.date,
                'duration': interview.duration_minutes,
                'participant_age': interview.participant_profile.age_range if interview.participant_profile else None,
                'participant_gender': interview.participant_profile.gender if interview.participant_profile else None,
                'narrative_frame': interview.narrative_features.dominant_frame if interview.narrative_features else None,
                'government_responsibility': interview.narrative_features.government_responsibility if interview.narrative_features else None,
                'individual_responsibility': interview.narrative_features.individual_responsibility if interview.narrative_features else None
            }
            
            # Conversation turns
            messages = []
            for turn in sorted(interview.turns, key=lambda x: x.turn_id):
                if turn.text and turn.text.strip():  # Only include turns with actual text
                    messages.append({
                        'turn_id': turn.turn_id,
                        'speaker': turn.speaker,
                        'text': turn.text,
                        'function': turn.functional_analysis.primary_function if turn.functional_analysis else None,
                        'topics': turn.content_analysis.topics if turn.content_analysis else [],
                        'emotion': turn.emotional_analysis.emotional_valence if turn.emotional_analysis else None,
                        'emotion_intensity': turn.emotional_analysis.emotional_intensity if turn.emotional_analysis else None,
                        'geographic_scope': turn.content_analysis.geographic_scope if turn.content_analysis else [],
                        'reasoning': turn.functional_analysis.reasoning if turn.functional_analysis else None
                    })
            
            return metadata, messages
    
    def show_interview_selector(self):
        """Show interview selection."""
        st.markdown("""
        <div class="interview-header">
            <h1>💬 Uruguay Conversations</h1>
            <p>Real citizen consultation interviews</p>
        </div>
        """, unsafe_allow_html=True)
        
        interviews = self.get_interview_list()
        
        # Filter to interviews with actual conversation text
        text_interviews = [i for i in interviews if i['text_turns'] > 0]
        
        if not text_interviews:
            st.error("No interviews with conversation text available")
            return
        
        st.markdown(f"**{len(text_interviews)} interviews with conversation text available**")
        
        # Simple selection
        selected = st.selectbox(
            "Choose an interview to view as a conversation:",
            options=[i['id'] for i in text_interviews],
            format_func=lambda x: next(i['display'] for i in text_interviews if i['id'] == x),
            key="interview_selector"
        )
        
        if selected:
            # Show preview info
            interview_info = next(i for i in text_interviews if i['id'] == selected)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"""
                <div class="stat-box">
                    <div class="stat-number">{interview_info['text_turns']}</div>
                    <div class="stat-label">Messages</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="stat-box">
                    <div class="stat-number">{interview_info['location']}</div>
                    <div class="stat-label">Location</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                frame_emoji = {'decline': '📉', 'progress': '📈', 'stagnation': '➡️'}.get(interview_info['frame'], '❓')
                st.markdown(f"""
                <div class="stat-box">
                    <div class="stat-number">{frame_emoji}</div>
                    <div class="stat-label">{interview_info['frame'] or 'Unknown'}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                <div class="stat-box">
                    <div class="stat-number">{interview_info['age'] or 'N/A'}</div>
                    <div class="stat-label">Age Range</div>
                </div>
                """, unsafe_allow_html=True)
            
            if st.button("📱 Open Chat Conversation", type="primary", use_container_width=True):
                st.session_state.selected_interview = selected
                st.rerun()
    
    def show_chat_interface(self, interview_id: str):
        """Show the main chat interface."""
        metadata, messages = self.load_conversation(interview_id)
        
        if not metadata or not messages:
            st.error("Could not load conversation")
            return
        
        # Header with interview info and back button
        col1, col2 = st.columns([1, 4])
        
        with col1:
            if st.button("← Back"):
                st.session_state.selected_interview = None
                st.rerun()
        
        with col2:
            st.markdown(f"""
            <div class="interview-header">
                <h2>💬 Interview {metadata['id']}</h2>
                <p>{metadata['location']} • {metadata['date']} • {len(messages)} messages</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Interview-level annotations (expandable)
        with st.expander("📊 Interview Analysis", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Participant Profile:**")
                st.write(f"Age: {metadata['participant_age'] or 'Unknown'}")
                st.write(f"Gender: {metadata['participant_gender'] or 'Unknown'}")
                st.write(f"Duration: {metadata['duration']} minutes")
            
            with col2:
                st.markdown("**Narrative Analysis:**")
                st.write(f"Dominant Frame: {metadata['narrative_frame'] or 'Unknown'}")
                if metadata['government_responsibility']:
                    st.write(f"Government Responsibility: {metadata['government_responsibility']:.2f}")
                if metadata['individual_responsibility']:
                    st.write(f"Individual Responsibility: {metadata['individual_responsibility']:.2f}")
        
        # Chat conversation
        st.markdown("### 💬 Conversation")
        
        # Display messages as a scrollable chat
        for message in messages:
            self.show_chat_message(message, interview_id)
        
        # Clear floats at the end
        st.markdown('<div class="clearfix"></div>', unsafe_allow_html=True)
    
    def show_chat_message(self, message, interview_id):
        """Show a single chat message with optional annotations."""
        speaker_class = message['speaker']
        speaker_label = "🎤 Interviewer" if message['speaker'] == 'interviewer' else "👤 Participant"
        
        # Main message bubble
        message_html = f"""
        <div class="clearfix">
            <div class="chat-message {speaker_class}">
                <div class="speaker-label">{speaker_label}</div>
                <div class="message-text">{message['text']}</div>
            </div>
        </div>
        """
        
        st.markdown(message_html, unsafe_allow_html=True)
        
        # Expandable turn-level annotations
        with st.expander(f"🔍 Turn {message['turn_id']} Analysis", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                if message['function']:
                    st.markdown("**🎯 Function:**")
                    st.write(message['function'].replace('_', ' ').title())
                
                if message['topics']:
                    st.markdown("**📝 Topics:**")
                    st.write(", ".join(message['topics']))
                
                if message['geographic_scope']:
                    st.markdown("**🗺️ Geographic Scope:**")
                    st.write(", ".join(message['geographic_scope']))
            
            with col2:
                if message['emotion']:
                    st.markdown("**😊 Emotion:**")
                    emotion_display = message['emotion'].title()
                    if message['emotion_intensity']:
                        emotion_display += f" (intensity: {message['emotion_intensity']:.2f})"
                    st.write(emotion_display)
                
                if message['reasoning']:
                    st.markdown("**💭 Analysis Reasoning:**")
                    st.write(message['reasoning'])


def main():
    """Main chat interface application."""
    chat = ChatInterface()
    
    try:
        if st.session_state.selected_interview:
            chat.show_chat_interface(st.session_state.selected_interview)
        else:
            chat.show_interview_selector()
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        if st.button("🔄 Reset"):
            st.session_state.selected_interview = None
            st.rerun()


if __name__ == "__main__":
    main()