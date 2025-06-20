"""
Interactive Chat Interface with Inline Expandable Annotations
Click on speech bubbles to see AI analysis inline
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
    page_title="Uruguay Interactive Chat Analysis",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "Interactive Qualitative Research Platform"
    }
)

# Interactive Chat CSS with Inline Annotations
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global styling */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .main > div {
        padding: 2rem 1rem;
        max-width: 1200px;
        margin: 0 auto;
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        min-height: 100vh;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    
    /* Interactive message bubbles */
    .chat-message {
        margin: 16px 0;
        padding: 20px 24px;
        border-radius: 20px;
        max-width: 75%;
        clear: both;
        word-wrap: break-word;
        line-height: 1.6;
        font-size: 16px;
        position: relative;
        box-shadow: 
            0 4px 6px -1px rgba(0, 0, 0, 0.1),
            0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
    }
    
    .chat-message:hover {
        transform: translateY(-2px);
        box-shadow: 
            0 10px 15px -3px rgba(0, 0, 0, 0.1),
            0 4px 6px -2px rgba(0, 0, 0, 0.05);
    }
    
    /* Expanded state */
    .chat-message.expanded {
        max-width: 85%;
        box-shadow: 
            0 20px 25px -5px rgba(0, 0, 0, 0.1),
            0 10px 10px -5px rgba(0, 0, 0, 0.04);
    }
    
    /* Speaker styles */
    .interviewer {
        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
        color: #1e40af;
        float: left;
        border-bottom-left-radius: 6px;
        margin-right: 25%;
        border: 1px solid #93c5fd;
    }
    
    .participant {
        background: linear-gradient(135deg, #ede9fe 0%, #ddd6fe 100%);
        color: #5b21b6;
        float: right;
        border-bottom-right-radius: 6px;
        margin-left: 25%;
        border: 1px solid #c4b5fd;
    }
    
    /* Message content */
    .message-content {
        margin-bottom: 8px;
    }
    
    /* Inline annotation overlay */
    .annotation-overlay {
        margin-top: 20px;
        padding-top: 20px;
        border-top: 1px solid rgba(255, 255, 255, 0.4);
        animation: fadeIn 0.3s ease-in-out;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Annotation sections */
    .annotation-section {
        margin: 12px 0;
        padding: 14px 16px;
        background: rgba(255, 255, 255, 0.2);
        border-radius: 10px;
        border-left: 4px solid rgba(255, 255, 255, 0.5);
        backdrop-filter: blur(5px);
    }
    
    .annotation-title {
        font-weight: 600;
        font-size: 12px;
        margin-bottom: 8px;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }
    
    .annotation-content {
        font-size: 14px;
        line-height: 1.5;
        opacity: 0.95;
    }
    
    /* Professional header */
    .interview-header {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        color: white;
        padding: 48px 32px;
        border-radius: 20px;
        margin-bottom: 32px;
        text-align: center;
        box-shadow: 
            0 20px 25px -5px rgba(0, 0, 0, 0.1),
            0 10px 10px -5px rgba(0, 0, 0, 0.04);
    }
    
    .interview-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        letter-spacing: -0.025em;
    }
    
    /* Confidence indicators */
    .confidence-indicator {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .confidence-high { 
        background: rgba(220, 252, 231, 0.8); 
        color: #166534; 
    }
    
    .confidence-medium { 
        background: rgba(254, 243, 199, 0.8); 
        color: #92400e; 
    }
    
    .confidence-low { 
        background: rgba(254, 226, 226, 0.8); 
        color: #991b1b; 
    }
    
    /* Click indicator */
    .click-indicator {
        position: absolute;
        top: 8px;
        right: 12px;
        font-size: 12px;
        opacity: 0.6;
        transition: opacity 0.3s ease;
    }
    
    .chat-message:hover .click-indicator {
        opacity: 1;
    }
    
    /* Clear floats */
    .clearfix::after {
        content: "";
        display: table;
        clear: both;
    }
    
    /* Professional buttons */
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
</style>
""", unsafe_allow_html=True)


class InteractiveChatInterface:
    """Interactive chat interface with inline expandable annotations."""
    
    def __init__(self):
        self.db = get_db()
        self.setup_session_state()
    
    def setup_session_state(self):
        """Initialize session state."""
        if 'selected_interview' not in st.session_state:
            st.session_state.selected_interview = None
        if 'expanded_messages' not in st.session_state:
            st.session_state.expanded_messages = set()
    
    @st.cache_data(ttl=300)
    def get_interview_list(_self):
        """Get interviews with conversation data."""
        with _self.db.get_session() as session:
            interviews = session.query(Interview).all()
            
            options = []
            for interview in interviews:
                # Count actual conversation turns
                text_turns = sum(1 for turn in interview.turns if turn.text and turn.text.strip())
                
                if text_turns > 0:  # Only include interviews with conversation
                    options.append({
                        'id': interview.interview_id,
                        'location': interview.location,
                        'date': interview.date,
                        'text_turns': text_turns,
                        'frame': interview.narrative_features.dominant_frame if interview.narrative_features else None,
                        'age': interview.participant_profile.age_range if interview.participant_profile else None
                    })
            
            # Sort by conversation length
            return sorted(options, key=lambda x: x['text_turns'], reverse=True)
    
    @st.cache_data(ttl=300)
    def load_conversation_data(_self, interview_id: str):
        """Load conversation with full analysis."""
        with _self.db.get_session() as session:
            interview = session.query(Interview).filter_by(interview_id=interview_id).first()
            
            if not interview:
                return None, []
            
            metadata = {
                'id': interview.interview_id,
                'location': interview.location,
                'date': interview.date,
                'duration': interview.duration_minutes
            }
            
            # Load conversation with full analysis
            messages = []
            for turn in sorted(interview.turns, key=lambda x: x.turn_id):
                if turn.text and turn.text.strip():
                    messages.append({
                        'turn_id': turn.turn_id,
                        'speaker': turn.speaker,
                        'text': turn.text,
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
                            'content_confidence': turn.content_analysis.content_confidence if turn.content_analysis else None
                        } if turn.content_analysis else None,
                        'emotional_analysis': {
                            'emotional_valence': turn.emotional_analysis.emotional_valence if turn.emotional_analysis else None,
                            'emotional_intensity': turn.emotional_analysis.emotional_intensity if turn.emotional_analysis else None,
                            'specific_emotions': turn.emotional_analysis.specific_emotions if turn.emotional_analysis else [],
                            'certainty': turn.emotional_analysis.certainty if turn.emotional_analysis else None
                        } if turn.emotional_analysis else None,
                        'evidence_analysis': {
                            'evidence_type': turn.evidence_analysis.evidence_type if turn.evidence_analysis else None,
                            'specificity': turn.evidence_analysis.specificity if turn.evidence_analysis else None,
                            'evidence_confidence': turn.evidence_analysis.evidence_confidence if turn.evidence_analysis else None
                        } if turn.evidence_analysis else None
                    })
            
            return metadata, messages
    
    def show_interview_selector(self):
        """Show interview selection."""
        st.markdown("""
        <div class="interview-header">
            <h1>🏛️ Interactive Chat Analysis</h1>
            <p>Click on conversation bubbles to see AI annotations inline</p>
            <div style="margin-top: 16px; font-size: 14px; opacity: 0.8;">
                Professional Qualitative Research Platform
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        interviews = self.get_interview_list()
        
        if not interviews:
            st.error("No interviews with conversation data available")
            return
        
        st.markdown("### 📋 **Select an Interview**")
        st.markdown("*Choose an interview to explore as an interactive conversation*")
        
        # Show top interviews
        for interview in interviews[:6]:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    st.markdown(f"**Interview {interview['id']}**")
                    st.markdown(f"📍 {interview['location']}")
                
                with col2:
                    frame_emoji = {'decline': '📉', 'progress': '📈', 'stagnation': '➡️'}.get(interview['frame'], '❓')
                    st.markdown(f"{frame_emoji} {interview['frame'] or 'Unknown'}")
                    st.markdown(f"📅 {interview['date']}")
                
                with col3:
                    st.markdown(f"💬 **{interview['text_turns']} messages**")
                    st.markdown(f"👤 {interview['age'] or 'Unknown age'}")
                
                with col4:
                    if st.button("Open Chat", key=f"open_{interview['id']}", type="primary"):
                        st.session_state.selected_interview = interview['id']
                        st.session_state.expanded_messages = set()  # Reset expanded state
                        st.rerun()
                
                st.markdown("---")
    
    def show_interactive_chat(self, interview_id: str):
        """Show interactive chat interface."""
        metadata, messages = self.load_conversation_data(interview_id)
        
        if not metadata or not messages:
            st.error("Could not load conversation data")
            return
        
        # Header
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
        
        # Interactive conversation
        st.markdown("### 🎯 **Interactive Conversation**")
        st.markdown("*Click on any message bubble to see detailed AI analysis*")
        
        for i, message in enumerate(messages):
            self.show_interactive_bubble(message, i)
        
        st.markdown('<div class="clearfix"></div>', unsafe_allow_html=True)
    
    def show_interactive_bubble(self, message, index):
        """Show interactive message bubble with inline annotations."""
        speaker_class = message['speaker']
        speaker_label = "🎤 Interviewer" if message['speaker'] == 'interviewer' else "👤 Participant"
        
        # Significance indicator
        significance_emoji = "⭐" if message.get('significance') == 'high' else "📍" if message.get('significance') == 'medium' else ""
        
        # Check if expanded
        message_key = f"msg_{index}"
        is_expanded = message_key in st.session_state.expanded_messages
        
        # Toggle expansion on click
        if st.button(
            f"Toggle {speaker_label} - Turn {message['turn_id']}", 
            key=f"toggle_{index}",
            help="Click to see AI analysis",
            use_container_width=False
        ):
            if is_expanded:
                st.session_state.expanded_messages.discard(message_key)
            else:
                st.session_state.expanded_messages.add(message_key)
            st.rerun()
        
        # Generate bubble content
        expanded_class = "expanded" if is_expanded else ""
        
        bubble_html = f"""
        <div class="clearfix">
            <div class="chat-message {speaker_class} {expanded_class}">
                <div class="click-indicator">👆 click</div>
                <div style="font-weight: 600; font-size: 11px; opacity: 0.8; margin-bottom: 4px;">
                    {speaker_label} {significance_emoji}
                </div>
                <div class="message-content">{message['text']}</div>
        """
        
        # Add annotations if expanded
        if is_expanded:
            annotations = self.generate_annotations(message)
            bubble_html += f"""
                <div class="annotation-overlay">
                    {annotations}
                </div>
            """
        
        bubble_html += """
            </div>
        </div>
        """
        
        st.markdown(bubble_html, unsafe_allow_html=True)
    
    def generate_annotations(self, message):
        """Generate inline annotations for message."""
        annotations_html = ""
        
        # Functional Analysis
        if message['functional_analysis']:
            func = message['functional_analysis']
            content_parts = []
            
            if func['primary_function']:
                content_parts.append(f"<strong>Function:</strong> {func['primary_function'].replace('_', ' ').title()}")
            
            if func['function_confidence']:
                confidence_class = self.get_confidence_class(func['function_confidence'])
                content_parts.append(f"<strong>Confidence:</strong> <span class='confidence-indicator {confidence_class}'>{func['function_confidence']:.2f}</span>")
            
            if content_parts:
                annotations_html += f"""
                <div class="annotation-section">
                    <div class="annotation-title">🎯 Function Analysis</div>
                    <div class="annotation-content">{'<br>'.join(content_parts)}</div>
                </div>
                """
        
        # Content Analysis
        if message['content_analysis']:
            content = message['content_analysis']
            content_parts = []
            
            if content['topics']:
                content_parts.append(f"<strong>Topics:</strong> {', '.join(content['topics'])}")
            
            if content['geographic_scope']:
                content_parts.append(f"<strong>Geographic:</strong> {', '.join(content['geographic_scope'])}")
            
            if content['temporal_reference']:
                content_parts.append(f"<strong>Time:</strong> {content['temporal_reference'].replace('_', ' ').title()}")
            
            if content_parts:
                annotations_html += f"""
                <div class="annotation-section">
                    <div class="annotation-title">📝 Content Analysis</div>
                    <div class="annotation-content">{'<br>'.join(content_parts)}</div>
                </div>
                """
        
        # Emotional Analysis
        if message['emotional_analysis']:
            emotion = message['emotional_analysis']
            content_parts = []
            
            if emotion['emotional_valence']:
                valence_emoji = {'positive': '😊', 'negative': '😔', 'neutral': '😐', 'mixed': '🤔'}.get(emotion['emotional_valence'], '😐')
                content_parts.append(f"<strong>Emotion:</strong> {valence_emoji} {emotion['emotional_valence'].title()}")
            
            if emotion['emotional_intensity']:
                content_parts.append(f"<strong>Intensity:</strong> {emotion['emotional_intensity']:.2f}")
            
            if emotion['specific_emotions']:
                content_parts.append(f"<strong>Details:</strong> {', '.join(emotion['specific_emotions'])}")
            
            if content_parts:
                annotations_html += f"""
                <div class="annotation-section">
                    <div class="annotation-title">😊 Emotional Analysis</div>
                    <div class="annotation-content">{'<br>'.join(content_parts)}</div>
                </div>
                """
        
        # Evidence Analysis
        if message.get('evidence_analysis'):
            evidence = message['evidence_analysis']
            content_parts = []
            
            if evidence['evidence_type']:
                content_parts.append(f"<strong>Type:</strong> {evidence['evidence_type'].replace('_', ' ').title()}")
            
            if evidence['specificity']:
                content_parts.append(f"<strong>Specificity:</strong> {evidence['specificity'].replace('_', ' ').title()}")
            
            if content_parts:
                annotations_html += f"""
                <div class="annotation-section">
                    <div class="annotation-title">📊 Evidence Analysis</div>
                    <div class="annotation-content">{'<br>'.join(content_parts)}</div>
                </div>
                """
        
        return annotations_html if annotations_html else "<div style='font-style: italic; opacity: 0.7;'>No detailed analysis available</div>"
    
    def get_confidence_class(self, confidence):
        """Get CSS class for confidence score."""
        if confidence >= 0.8:
            return 'confidence-high'
        elif confidence >= 0.6:
            return 'confidence-medium'
        else:
            return 'confidence-low'


def main():
    """Main interactive chat interface."""
    interface = InteractiveChatInterface()
    
    try:
        if st.session_state.selected_interview:
            interface.show_interactive_chat(st.session_state.selected_interview)
        else:
            interface.show_interview_selector()
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        if st.button("🔄 Reset"):
            st.session_state.selected_interview = None
            st.session_state.expanded_messages = set()
            st.rerun()


if __name__ == "__main__":
    main()