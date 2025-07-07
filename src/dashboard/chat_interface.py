"""
Holistic Chat Interface
Prominently features comprehensive interview-level qualitative analysis
"""
import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.database.connection import get_db
from src.database.models import Interview, Turn

# Configure page
st.set_page_config(
    page_title="Uruguay Citizen Consultation Analysis Platform",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "Professional Qualitative Research Platform"
    }
)

# Professional Research Platform CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    /* Global Typography */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        font-feature-settings: "cv02", "cv03", "cv04", "cv11";
    }
    
    /* Clean professional interface */
    .main > div {
        padding: 2rem 1rem;
        max-width: 1400px;
        margin: 0 auto;
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        min-height: 100vh;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    
    /* Research-grade analysis sections */
    .analysis-section {
        background: linear-gradient(135deg, #ffffff 0%, #fefefe 100%);
        border-radius: 16px;
        padding: 32px;
        margin: 24px 0;
        box-shadow: 
            0 4px 6px -1px rgba(0, 0, 0, 0.1),
            0 2px 4px -1px rgba(0, 0, 0, 0.06),
            0 0 0 1px rgba(0, 0, 0, 0.05);
        border-left: 6px solid #2563eb;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .analysis-section:hover {
        transform: translateY(-2px);
        box-shadow: 
            0 10px 15px -3px rgba(0, 0, 0, 0.1),
            0 4px 6px -2px rgba(0, 0, 0, 0.05),
            0 0 0 1px rgba(0, 0, 0, 0.05);
    }
    
    /* Semantic section colors */
    .narrative-section {
        border-left-color: #7c3aed;
        background: linear-gradient(135deg, #faf5ff 0%, #ffffff 100%);
    }
    
    .synthesis-section {
        border-left-color: #dc2626;
        background: linear-gradient(135deg, #fef2f2 0%, #ffffff 100%);
    }
    
    .dynamics-section {
        border-left-color: #059669;
        background: linear-gradient(135deg, #f0fdf4 0%, #ffffff 100%);
    }
    
    .methodology-section {
        border-left-color: #ea580c;
        background: linear-gradient(135deg, #fff7ed 0%, #ffffff 100%);
    }
    
    /* Professional conversation interface */
    .chat-message {
        margin: 16px 0;
        padding: 20px 24px;
        border-radius: 20px;
        max-width: 78%;
        clear: both;
        word-wrap: break-word;
        line-height: 1.6;
        font-size: 16px;
        font-weight: 400;
        position: relative;
        box-shadow: 
            0 4px 6px -1px rgba(0, 0, 0, 0.1),
            0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .chat-message:hover {
        transform: translateY(-1px);
        box-shadow: 
            0 10px 15px -3px rgba(0, 0, 0, 0.1),
            0 4px 6px -2px rgba(0, 0, 0, 0.05);
    }
    
    .interviewer {
        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
        color: #1e40af;
        float: left;
        border-bottom-left-radius: 6px;
        margin-right: 22%;
        border: 1px solid #93c5fd;
    }
    
    .participant {
        background: linear-gradient(135deg, #ede9fe 0%, #ddd6fe 100%);
        color: #5b21b6;
        float: right;
        border-bottom-right-radius: 6px;
        margin-left: 22%;
        border: 1px solid #c4b5fd;
    }
    
    /* Professional header */
    .interview-header {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        color: white;
        padding: 48px 32px;
        border-radius: 20px;
        margin-bottom: 32px;
        text-align: center;
        position: relative;
        overflow: hidden;
        box-shadow: 
            0 20px 25px -5px rgba(0, 0, 0, 0.1),
            0 10px 10px -5px rgba(0, 0, 0, 0.04);
    }
    
    .interview-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="%23ffffff" opacity="0.1"/><circle cx="75" cy="75" r="1" fill="%23ffffff" opacity="0.1"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
        opacity: 0.1;
    }
    
    .interview-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        letter-spacing: -0.025em;
    }
    
    .interview-header p {
        font-size: 1.1rem;
        opacity: 0.9;
        font-weight: 400;
    }
    
    /* Professional metrics dashboard */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 20px;
        margin: 24px 0;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #fefefe 100%);
        padding: 24px 20px;
        border-radius: 16px;
        text-align: center;
        box-shadow: 
            0 4px 6px -1px rgba(0, 0, 0, 0.1),
            0 2px 4px -1px rgba(0, 0, 0, 0.06),
            0 0 0 1px rgba(0, 0, 0, 0.05);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid #f1f5f9;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 
            0 10px 15px -3px rgba(0, 0, 0, 0.1),
            0 4px 6px -2px rgba(0, 0, 0, 0.05);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1e40af;
        margin-bottom: 8px;
        font-feature-settings: "tnum";
    }
    
    .metric-label {
        font-size: 13px;
        color: #64748b;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Professional quote styling */
    .memorable-quote {
        background: linear-gradient(135deg, #fffbeb 0%, #ffffff 100%);
        border-left: 6px solid #f59e0b;
        padding: 24px 28px;
        margin: 20px 0;
        border-radius: 12px;
        font-style: italic;
        font-size: 1.1rem;
        line-height: 1.7;
        position: relative;
        box-shadow: 
            0 4px 6px -1px rgba(0, 0, 0, 0.1),
            0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    
    .memorable-quote::before {
        content: '"';
        position: absolute;
        top: 8px;
        left: 12px;
        font-size: 3rem;
        color: #f59e0b;
        opacity: 0.3;
        font-family: serif;
    }
    
    /* Clear floats */
    .clearfix::after {
        content: "";
        display: table;
        clear: both;
    }
    
    /* Professional tab interface */
    .tab-content {
        background: linear-gradient(135deg, #ffffff 0%, #fefefe 100%);
        padding: 32px;
        border-radius: 16px;
        margin-top: 24px;
        box-shadow: 
            0 4px 6px -1px rgba(0, 0, 0, 0.1),
            0 2px 4px -1px rgba(0, 0, 0, 0.06),
            0 0 0 1px rgba(0, 0, 0, 0.05);
        border: 1px solid #f1f5f9;
    }
    
    /* Enhanced typography */
    h1, h2, h3 {
        font-weight: 700;
        letter-spacing: -0.025em;
    }
    
    h1 { font-size: 2.25rem; }
    h2 { font-size: 1.875rem; }
    h3 { font-size: 1.5rem; }
    
    /* Professional form elements */
    .stSelectbox > div > div {
        border-radius: 12px;
        border: 2px solid #e2e8f0;
        font-weight: 500;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 24px;
        font-weight: 600;
        font-size: 15px;
        letter-spacing: 0.025em;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 
            0 4px 6px -1px rgba(0, 0, 0, 0.1),
            0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 
            0 10px 15px -3px rgba(0, 0, 0, 0.1),
            0 4px 6px -2px rgba(0, 0, 0, 0.05);
    }
    
    /* Research methodology indicators */
    .confidence-indicator {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .confidence-high { 
        background: #dcfce7; 
        color: #166534; 
        border: 1px solid #bbf7d0;
    }
    
    .confidence-medium { 
        background: #fef3c7; 
        color: #92400e; 
        border: 1px solid #fde68a;
    }
    
    .confidence-low { 
        background: #fee2e2; 
        color: #991b1b; 
        border: 1px solid #fecaca;
    }
</style>
""", unsafe_allow_html=True)


class HolisticChatInterface:
    """Chat interface with comprehensive interview-level analysis."""
    
    def __init__(self):
        self.db = get_db()
        self.setup_session_state()
    
    def setup_session_state(self):
        """Initialize session state."""
        if 'selected_interview' not in st.session_state:
            st.session_state.selected_interview = None
        if 'active_tab' not in st.session_state:
            st.session_state.active_tab = 'overview'
    
    @st.cache_data(ttl=300)
    def get_interview_list(_self):
        """Get interviews with holistic analysis."""
        with _self.db.get_session() as session:
            interviews = session.query(Interview).all()
            
            options = []
            for interview in interviews:
                # Check analysis completeness
                has_narrative = interview.narrative_features is not None
                has_key_narratives = interview.key_narratives is not None
                has_synthesis = interview.analytical_synthesis is not None
                has_dynamics = interview.interview_dynamics is not None
                
                analysis_score = sum([has_narrative, has_key_narratives, has_synthesis, has_dynamics])
                
                options.append({
                    'id': interview.interview_id,
                    'location': interview.location,
                    'date': interview.date,
                    'frame': interview.narrative_features.dominant_frame if has_narrative else None,
                    'analysis_completeness': analysis_score,
                    'text_turns': sum(1 for turn in interview.turns if turn.text and turn.text.strip())
                })
            
            # Sort by analysis completeness and conversation text
            return sorted(options, key=lambda x: (x['analysis_completeness'], x['text_turns']), reverse=True)
    
    @st.cache_data(ttl=300)
    def load_holistic_analysis(_self, interview_id: str):
        """Load comprehensive interview analysis."""
        with _self.db.get_session() as session:
            interview = session.query(Interview).filter_by(interview_id=interview_id).first()
            
            if not interview:
                return None
            
            # Comprehensive interview data
            data = {
                'metadata': {
                    'id': interview.interview_id,
                    'location': interview.location,
                    'date': interview.date,
                    'duration': interview.duration_minutes,
                    'municipality': interview.municipality,
                    'department': interview.department
                },
                'participant': {
                    'age_range': interview.participant_profile.age_range if interview.participant_profile else None,
                    'gender': interview.participant_profile.gender if interview.participant_profile else None,
                    'occupation': interview.participant_profile.occupation_sector if interview.participant_profile else None,
                    'affiliation': interview.participant_profile.organizational_affiliation if interview.participant_profile else None,
                    'confidence': interview.participant_profile.profile_confidence if interview.participant_profile else None
                },
                'narrative_features': {
                    'dominant_frame': interview.narrative_features.dominant_frame if interview.narrative_features else None,
                    'frame_narrative': interview.narrative_features.frame_narrative if interview.narrative_features else None,
                    'temporal_orientation': interview.narrative_features.temporal_orientation if interview.narrative_features else None,
                    'temporal_narrative': interview.narrative_features.temporal_narrative if interview.narrative_features else None,
                    'government_responsibility': interview.narrative_features.government_responsibility if interview.narrative_features else None,
                    'individual_responsibility': interview.narrative_features.individual_responsibility if interview.narrative_features else None,
                    'structural_factors': interview.narrative_features.structural_factors if interview.narrative_features else None,
                    'agency_narrative': interview.narrative_features.agency_narrative if interview.narrative_features else None,
                    'solution_orientation': interview.narrative_features.solution_orientation if interview.narrative_features else None,
                    'solution_narrative': interview.narrative_features.solution_narrative if interview.narrative_features else None,
                    'cultural_patterns': interview.narrative_features.cultural_patterns_identified if interview.narrative_features else []
                } if interview.narrative_features else None,
                'key_narratives': {
                    'identity_narrative': interview.key_narratives.identity_narrative if interview.key_narratives else None,
                    'problem_narrative': interview.key_narratives.problem_narrative if interview.key_narratives else None,
                    'hope_narrative': interview.key_narratives.hope_narrative if interview.key_narratives else None,
                    'memorable_quotes': interview.key_narratives.memorable_quotes if interview.key_narratives else [],
                    'rhetorical_strategies': interview.key_narratives.rhetorical_strategies if interview.key_narratives else []
                } if interview.key_narratives else None,
                'analytical_synthesis': {
                    'tensions_contradictions': interview.analytical_synthesis.tensions_contradictions if interview.analytical_synthesis else None,
                    'silences_omissions': interview.analytical_synthesis.silences_omissions if interview.analytical_synthesis else None,
                    'cultural_context': interview.analytical_synthesis.cultural_context_notes if interview.analytical_synthesis else None,
                    'broader_themes': interview.analytical_synthesis.connections_to_broader_themes if interview.analytical_synthesis else None
                } if interview.analytical_synthesis else None,
                'interview_dynamics': {
                    'rapport': interview.interview_dynamics.rapport if interview.interview_dynamics else None,
                    'rapport_narrative': interview.interview_dynamics.rapport_narrative if interview.interview_dynamics else None,
                    'engagement': interview.interview_dynamics.participant_engagement if interview.interview_dynamics else None,
                    'engagement_narrative': interview.interview_dynamics.engagement_narrative if interview.interview_dynamics else None,
                    'coherence': interview.interview_dynamics.coherence if interview.interview_dynamics else None,
                    'coherence_narrative': interview.interview_dynamics.coherence_narrative if interview.interview_dynamics else None,
                    'interviewer_effects': interview.interview_dynamics.interviewer_effects if interview.interview_dynamics else None
                } if interview.interview_dynamics else None,
                'conversation': []
            }
            
            # Add conversation turns with complete analysis
            for turn in sorted(interview.turns, key=lambda x: x.turn_id):
                if turn.text and turn.text.strip():
                    data['conversation'].append({
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
                            'topic_narrative': turn.content_analysis.topic_narrative if turn.content_analysis else None,
                            'content_confidence': turn.content_analysis.content_confidence if turn.content_analysis else None,
                            'reasoning': turn.content_analysis.reasoning if turn.content_analysis else None
                        } if turn.content_analysis else None,
                        'emotional_analysis': {
                            'emotional_valence': turn.emotional_analysis.emotional_valence if turn.emotional_analysis else None,
                            'emotional_intensity': turn.emotional_analysis.emotional_intensity if turn.emotional_analysis else None,
                            'specific_emotions': turn.emotional_analysis.specific_emotions if turn.emotional_analysis else [],
                            'emotional_narrative': turn.emotional_analysis.emotional_narrative if turn.emotional_analysis else None,
                            'certainty': turn.emotional_analysis.certainty if turn.emotional_analysis else None,
                            'rhetorical_features': turn.emotional_analysis.rhetorical_features if turn.emotional_analysis else None,
                            'reasoning': turn.emotional_analysis.reasoning if turn.emotional_analysis else None
                        } if turn.emotional_analysis else None,
                        'evidence_analysis': {
                            'evidence_type': turn.evidence_analysis.evidence_type if turn.evidence_analysis else None,
                            'evidence_narrative': turn.evidence_analysis.evidence_narrative if turn.evidence_analysis else None,
                            'specificity': turn.evidence_analysis.specificity if turn.evidence_analysis else None,
                            'evidence_confidence': turn.evidence_analysis.evidence_confidence if turn.evidence_analysis else None,
                            'reasoning': turn.evidence_analysis.reasoning if turn.evidence_analysis else None
                        } if turn.evidence_analysis else None,
                        'uncertainty_tracking': {
                            'coding_confidence': turn.uncertainty_tracking.coding_confidence if turn.uncertainty_tracking else None,
                            'ambiguous_aspects': turn.uncertainty_tracking.ambiguous_aspects if turn.uncertainty_tracking else [],
                            'edge_case_flag': turn.uncertainty_tracking.edge_case_flag if turn.uncertainty_tracking else False,
                            'alternative_interpretations': turn.uncertainty_tracking.alternative_interpretations if turn.uncertainty_tracking else [],
                            'resolution_strategy': turn.uncertainty_tracking.resolution_strategy if turn.uncertainty_tracking else None,
                            'annotator_notes': turn.uncertainty_tracking.annotator_notes if turn.uncertainty_tracking else None
                        } if turn.uncertainty_tracking else None
                    })
            
            return data
    
    def show_interview_selector(self):
        """Show interview selection with analysis preview."""
        st.markdown("""
        <div class="interview-header">
            <h1>🏛️ Uruguay Citizen Consultation Analysis</h1>
            <p>Professional Qualitative Research Platform • Advanced AI-Powered Interview Analysis</p>
            <div style="margin-top: 16px; font-size: 14px; opacity: 0.8;">
                Research-Grade Methodology • Multi-Dimensional Analysis • Narrative Intelligence
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        interviews = self.get_interview_list()
        
        st.markdown("**Select an interview for comprehensive analysis:**")
        
        # Show available interviews with analysis completeness
        for interview in interviews[:10]:  # Show top 10 most complete
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    st.write(f"**Interview {interview['id']}**")
                    st.write(f"📍 {interview['location']}")
                
                with col2:
                    frame_emoji = {'decline': '📉', 'progress': '📈', 'stagnation': '➡️'}.get(interview['frame'], '❓')
                    st.write(f"{frame_emoji} {interview['frame'] or 'Unknown'}")
                    st.write(f"📅 {interview['date']}")
                
                with col3:
                    st.write(f"📊 Analysis: {interview['analysis_completeness']}/4 sections")
                    st.write(f"💬 {interview['text_turns']} messages")
                
                with col4:
                    if st.button("Analyze", key=f"select_{interview['id']}"):
                        st.session_state.selected_interview = interview['id']
                        st.rerun()
                
                st.markdown("---")
    
    def show_holistic_interface(self, interview_id: str):
        """Show comprehensive interview analysis interface."""
        data = self.load_holistic_analysis(interview_id)
        
        if not data:
            st.error("Could not load interview analysis")
            return
        
        # Header and navigation
        col1, col2 = st.columns([1, 5])
        
        with col1:
            if st.button("← Back"):
                st.session_state.selected_interview = None
                st.rerun()
        
        with col2:
            st.markdown(f"""
            <div class="interview-header">
                <h2>🏛️ Interview {data['metadata']['id']} Analysis</h2>
                <p>{data['metadata']['location']} • {data['metadata']['date']} • {data['metadata']['duration']} minutes</p>
                <div style="margin-top: 12px; font-size: 13px; opacity: 0.8;">
                    Professional Qualitative Research Analysis
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Key metrics
        self.show_key_metrics(data)
        
        # Tabbed interface for different analysis views
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Overview", 
            "📚 Narrative Analysis", 
            "🔬 Analytical Synthesis",
            "🎭 Interview Dynamics",
            "💬 Conversation"
        ])
        
        with tab1:
            self.show_overview_analysis(data)
        
        with tab2:
            self.show_narrative_analysis(data)
        
        with tab3:
            self.show_analytical_synthesis(data)
        
        with tab4:
            self.show_interview_dynamics(data)
        
        with tab5:
            self.show_conversation_view(data)
    
    def show_key_metrics(self, data):
        """Show key metrics overview."""
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            frame = data['narrative_features']['dominant_frame'] if data['narrative_features'] else 'Unknown'
            frame_emoji = {'decline': '📉', 'progress': '📈', 'stagnation': '➡️'}.get(frame, '❓')
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{frame_emoji}</div>
                <div class="metric-label">{frame}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            age = data['participant']['age_range'] or 'Unknown'
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{age}</div>
                <div class="metric-label">Age Range</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            gov_resp = data['narrative_features']['government_responsibility'] if data['narrative_features'] else None
            gov_display = f"{gov_resp:.1f}" if gov_resp else "N/A"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{gov_display}</div>
                <div class="metric-label">Gov Responsibility</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            rapport = data['interview_dynamics']['rapport'] if data['interview_dynamics'] else 'Unknown'
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{rapport}</div>
                <div class="metric-label">Rapport</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            messages = len(data['conversation'])
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{messages}</div>
                <div class="metric-label">Messages</div>
            </div>
            """, unsafe_allow_html=True)
    
    def show_overview_analysis(self, data):
        """Show comprehensive overview."""
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 👤 Participant Profile")
            
            if data['participant']['age_range']:
                st.write(f"**Age:** {data['participant']['age_range']}")
            if data['participant']['gender']:
                st.write(f"**Gender:** {data['participant']['gender']}")
            if data['participant']['occupation']:
                st.write(f"**Occupation:** {data['participant']['occupation']}")
            if data['participant']['affiliation']:
                st.write(f"**Affiliation:** {data['participant']['affiliation']}")
            if data['participant']['confidence']:
                st.write(f"**Profile Confidence:** {data['participant']['confidence']:.2f}")
        
        with col2:
            st.markdown("### 🗺️ Context")
            st.write(f"**Location:** {data['metadata']['location']}")
            st.write(f"**Municipality:** {data['metadata']['municipality']}")
            st.write(f"**Department:** {data['metadata']['department']}")
            st.write(f"**Date:** {data['metadata']['date']}")
            st.write(f"**Duration:** {data['metadata']['duration']} minutes")
        
        # Key narratives overview
        if data['key_narratives']:
            st.markdown("### 🗝️ Key Narratives")
            
            if data['key_narratives']['identity_narrative']:
                st.markdown("**Identity Narrative:**")
                st.write(data['key_narratives']['identity_narrative'])
            
            if data['key_narratives']['problem_narrative']:
                st.markdown("**Problem Narrative:**")
                st.write(data['key_narratives']['problem_narrative'])
            
            if data['key_narratives']['hope_narrative']:
                st.markdown("**Hope Narrative:**")
                st.write(data['key_narratives']['hope_narrative'])
    
    def show_narrative_analysis(self, data):
        """Show detailed narrative analysis."""
        if not data['narrative_features']:
            st.warning("No narrative analysis available")
            return
        
        nf = data['narrative_features']
        
        # Dominant frame analysis
        st.markdown("### 📖 Narrative Frame Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if nf['dominant_frame']:
                st.markdown(f"**Dominant Frame:** {nf['dominant_frame'].title()}")
            
            if nf['frame_narrative']:
                st.markdown("**Frame Narrative:**")
                st.write(nf['frame_narrative'])
            
            if nf['temporal_orientation']:
                st.markdown(f"**Temporal Orientation:** {nf['temporal_orientation'].replace('_', ' ').title()}")
            
            if nf['temporal_narrative']:
                st.markdown("**Temporal Narrative:**")
                st.write(nf['temporal_narrative'])
        
        with col2:
            # Agency attribution
            st.markdown("**🎯 Agency Attribution**")
            
            if nf['government_responsibility']:
                st.metric("Government Responsibility", f"{nf['government_responsibility']:.2f}")
            
            if nf['individual_responsibility']:
                st.metric("Individual Responsibility", f"{nf['individual_responsibility']:.2f}")
            
            if nf['structural_factors']:
                st.metric("Structural Factors", f"{nf['structural_factors']:.2f}")
        
        # Agency narrative
        if nf['agency_narrative']:
            st.markdown("**Agency Narrative:**")
            st.write(nf['agency_narrative'])
        
        # Solution orientation
        if nf['solution_orientation']:
            st.markdown(f"**Solution Orientation:** {nf['solution_orientation'].replace('_', ' ').title()}")
        
        if nf['solution_narrative']:
            st.markdown("**Solution Narrative:**")
            st.write(nf['solution_narrative'])
        
        # Cultural patterns
        if nf['cultural_patterns']:
            st.markdown("**🎭 Cultural Patterns:**")
            for pattern in nf['cultural_patterns']:
                st.write(f"• {pattern.replace('_', ' ').title()}")
        
        # Memorable quotes
        if data['key_narratives'] and data['key_narratives']['memorable_quotes']:
            st.markdown("### 💬 Memorable Quotes")
            for quote in data['key_narratives']['memorable_quotes']:
                st.markdown(f'<div class="memorable-quote">"{quote}"</div>', unsafe_allow_html=True)
        
        # Rhetorical strategies
        if data['key_narratives'] and data['key_narratives']['rhetorical_strategies']:
            st.markdown("**🎭 Rhetorical Strategies:**")
            for strategy in data['key_narratives']['rhetorical_strategies']:
                st.write(f"• {strategy}")
    
    def show_analytical_synthesis(self, data):
        """Show analytical synthesis."""
        if not data['analytical_synthesis']:
            st.warning("No analytical synthesis available")
            return
        
        syn = data['analytical_synthesis']
        
        if syn['tensions_contradictions']:
            st.markdown("### ⚖️ Tensions & Contradictions")
            st.write(syn['tensions_contradictions'])
        
        if syn['silences_omissions']:
            st.markdown("### 🤫 Silences & Omissions")
            st.write(syn['silences_omissions'])
        
        if syn['cultural_context']:
            st.markdown("### 🏛️ Cultural Context")
            st.write(syn['cultural_context'])
        
        if syn['broader_themes']:
            st.markdown("### 🌐 Connections to Broader Themes")
            st.write(syn['broader_themes'])
    
    def show_interview_dynamics(self, data):
        """Show interview dynamics analysis."""
        if not data['interview_dynamics']:
            st.warning("No interview dynamics available")
            return
        
        dyn = data['interview_dynamics']
        
        col1, col2 = st.columns(2)
        
        with col1:
            if dyn['rapport']:
                st.markdown(f"**Rapport:** {dyn['rapport'].title()}")
            
            if dyn['rapport_narrative']:
                st.markdown("**Rapport Analysis:**")
                st.write(dyn['rapport_narrative'])
            
            if dyn['engagement']:
                st.markdown(f"**Participant Engagement:** {dyn['engagement'].replace('_', ' ').title()}")
            
            if dyn['engagement_narrative']:
                st.markdown("**Engagement Analysis:**")
                st.write(dyn['engagement_narrative'])
        
        with col2:
            if dyn['coherence']:
                st.markdown(f"**Coherence:** {dyn['coherence'].title()}")
            
            if dyn['coherence_narrative']:
                st.markdown("**Coherence Analysis:**")
                st.write(dyn['coherence_narrative'])
            
            if dyn['interviewer_effects']:
                st.markdown("**Interviewer Effects:**")
                st.write(dyn['interviewer_effects'])
    
    def show_conversation_view(self, data):
        """Show conversation with comprehensive analysis."""
        st.markdown("### 💬 Conversation Flow")
        
        for message in data['conversation']:
            # Chat message
            speaker_class = message['speaker']
            speaker_label = "🎤 Interviewer" if message['speaker'] == 'interviewer' else "👤 Participant"
            
            # Add significance indicator
            significance_emoji = "⭐" if message.get('significance') == 'high' else "📍" if message.get('significance') == 'medium' else ""
            
            message_html = f"""
            <div class="clearfix">
                <div class="chat-message {speaker_class}">
                    <div style="font-weight: 600; font-size: 11px; opacity: 0.8; margin-bottom: 4px;">
                        {speaker_label} {significance_emoji}
                    </div>
                    <div>{message['text']}</div>
                </div>
            </div>
            """
            
            st.markdown(message_html, unsafe_allow_html=True)
            
            # Comprehensive turn analysis
            with st.expander(f"🔍 Complete Analysis - Turn {message['turn_id']}", expanded=False):
                self.show_complete_turn_analysis(message)
        
        st.markdown('<div class="clearfix"></div>', unsafe_allow_html=True)
    
    def show_complete_turn_analysis(self, message):
        """Show all 5 dimensions of turn analysis with elegant presentation."""
        
        # Create clean sections for each analysis dimension
        analysis_sections = []
        
        # 1. Functional Analysis
        if message['functional_analysis']:
            func = message['functional_analysis']
            sections = []
            sections.append(f"**Function:** {func['primary_function'].replace('_', ' ').title()}")
            
            if func['secondary_functions']:
                sections.append(f"**Additional:** {', '.join(func['secondary_functions'])}")
            
            if func['function_confidence']:
                confidence_class = self.get_confidence_class(func['function_confidence'])
                sections.append(f"**Confidence:** <span class='{confidence_class}'>{func['function_confidence']:.2f}</span>")
            
            if func['reasoning']:
                sections.append(f"**Analysis:** {func['reasoning']}")
            
            analysis_sections.append({
                'title': '🎯 Functional Analysis',
                'content': sections,
                'class': 'function-analysis'
            })
        
        # 2. Content Analysis  
        if message['content_analysis']:
            content = message['content_analysis']
            sections = []
            
            if content['topics']:
                sections.append(f"**Topics:** {', '.join(content['topics'])}")
            
            if content['geographic_scope']:
                sections.append(f"**Geographic Scope:** {', '.join(content['geographic_scope'])}")
            
            if content['temporal_reference']:
                sections.append(f"**Time Reference:** {content['temporal_reference'].replace('_', ' ').title()}")
            
            if content['topic_narrative']:
                sections.append(f"**Context:** {content['topic_narrative']}")
            
            if content['content_confidence']:
                confidence_class = self.get_confidence_class(content['content_confidence'])
                sections.append(f"**Confidence:** <span class='{confidence_class}'>{content['content_confidence']:.2f}</span>")
            
            analysis_sections.append({
                'title': '📝 Content Analysis',
                'content': sections,
                'class': 'content-analysis'
            })
        
        # 3. Evidence Analysis
        if message['evidence_analysis']:
            evidence = message['evidence_analysis']
            sections = []
            
            if evidence['evidence_type']:
                sections.append(f"**Type:** {evidence['evidence_type'].replace('_', ' ').title()}")
            
            if evidence['specificity']:
                sections.append(f"**Specificity:** {evidence['specificity'].replace('_', ' ').title()}")
            
            if evidence['evidence_narrative']:
                sections.append(f"**Details:** {evidence['evidence_narrative']}")
            
            if evidence['evidence_confidence']:
                confidence_class = self.get_confidence_class(evidence['evidence_confidence'])
                sections.append(f"**Confidence:** <span class='{confidence_class}'>{evidence['evidence_confidence']:.2f}</span>")
            
            analysis_sections.append({
                'title': '📊 Evidence Analysis',
                'content': sections,
                'class': 'evidence-analysis'
            })
        
        # 4. Emotional Analysis
        if message['emotional_analysis']:
            emotion = message['emotional_analysis']
            sections = []
            
            if emotion['emotional_valence']:
                valence_emoji = {'positive': '😊', 'negative': '😔', 'neutral': '😐', 'mixed': '🤔'}.get(emotion['emotional_valence'], '😐')
                sections.append(f"**Valence:** {valence_emoji} {emotion['emotional_valence'].title()}")
            
            if emotion['emotional_intensity']:
                sections.append(f"**Intensity:** {emotion['emotional_intensity']:.2f}")
            
            if emotion['specific_emotions']:
                sections.append(f"**Emotions:** {', '.join(emotion['specific_emotions'])}")
            
            if emotion['certainty']:
                sections.append(f"**Certainty:** {emotion['certainty'].replace('_', ' ').title()}")
            
            if emotion['rhetorical_features']:
                sections.append(f"**Rhetoric:** {emotion['rhetorical_features']}")
            
            if emotion['emotional_narrative']:
                sections.append(f"**Context:** {emotion['emotional_narrative']}")
            
            analysis_sections.append({
                'title': '😊 Emotional Analysis',
                'content': sections,
                'class': 'emotional-analysis'
            })
        
        # 5. Uncertainty Tracking
        if message['uncertainty_tracking']:
            uncertainty = message['uncertainty_tracking']
            sections = []
            
            if uncertainty['coding_confidence']:
                confidence_class = self.get_confidence_class(uncertainty['coding_confidence'])
                sections.append(f"**Coding Confidence:** <span class='{confidence_class}'>{uncertainty['coding_confidence']:.2f}</span>")
            
            if uncertainty['edge_case_flag']:
                sections.append("🚩 **Edge Case Identified**")
            
            if uncertainty['ambiguous_aspects']:
                sections.append(f"**Ambiguities:** {', '.join(uncertainty['ambiguous_aspects'])}")
            
            if uncertainty['alternative_interpretations']:
                alt_text = ' | '.join(uncertainty['alternative_interpretations'])
                sections.append(f"**Alternative Views:** {alt_text}")
            
            if uncertainty['resolution_strategy']:
                sections.append(f"**Resolution:** {uncertainty['resolution_strategy']}")
            
            if uncertainty['annotator_notes']:
                sections.append(f"**Notes:** {uncertainty['annotator_notes']}")
            
            analysis_sections.append({
                'title': '⚠️ Uncertainty Analysis',
                'content': sections,
                'class': 'uncertainty-analysis'
            })
        
        # Render analysis sections in a clean, organized way
        self.render_analysis_sections(analysis_sections)
    
    def get_confidence_class(self, confidence):
        """Get CSS class for confidence score."""
        if confidence >= 0.8:
            return 'confidence-high'
        elif confidence >= 0.6:
            return 'confidence-medium'
        else:
            return 'confidence-low'
    
    def render_analysis_sections(self, sections):
        """Render analysis sections with professional styling."""
        if not sections:
            st.write("*No detailed analysis available for this turn*")
            return
        
        # Use columns for better layout
        if len(sections) <= 2:
            cols = st.columns(len(sections))
        else:
            cols = st.columns(2)
        
        for i, section in enumerate(sections):
            col_idx = i % len(cols)
            
            with cols[col_idx]:
                st.markdown(f"""
                <div class="analysis-section {section['class']}">
                    <h4 style="margin-bottom: 16px; color: #1e40af; font-weight: 600;">{section['title']}</h4>
                    {'<br>'.join(section['content'])}
                </div>
                """, unsafe_allow_html=True)


def main():
    """Main holistic chat interface."""
    interface = HolisticChatInterface()
    
    try:
        if st.session_state.selected_interview:
            interface.show_holistic_interface(st.session_state.selected_interview)
        else:
            interface.show_interview_selector()
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        if st.button("🔄 Reset"):
            st.session_state.selected_interview = None
            st.rerun()


if __name__ == "__main__":
    main()