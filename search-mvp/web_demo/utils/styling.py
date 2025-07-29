"""
Styling utilities for the Uruguay Interview Research Agent
"""

import streamlit as st
from datetime import datetime

def inject_css():
    """Inject custom CSS for ChatGPT-like minimal design"""
    st.markdown(
        """
        <style>
        /* Hide Streamlit chrome */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display: none;}
        
        /* Main layout */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 768px;
            margin: 0 auto;
        }
        
        /* Clean header */
        .main-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .main-title {
            font-size: 1.75rem;
            font-weight: 600;
            color: #2d3748;
            margin-bottom: 0.5rem;
        }
        
        .main-subtitle {
            font-size: 1rem;
            color: #718096;
            margin-bottom: 0;
        }
        
        /* Chat interface */
        .stChatMessage {
            padding: 1rem 1.5rem;
            margin-bottom: 1rem;
            border-radius: 1rem;
            max-width: 100%;
        }
        
        .stChatMessage[data-testid="user-message"] {
            background: #f7fafc;
            border: 1px solid #e2e8f0;
        }
        
        .stChatMessage[data-testid="assistant-message"] {
            background: #ffffff;
            border: 1px solid #e2e8f0;
        }
        
        /* Input styling */
        .stChatInput > div {
            border-radius: 1.5rem;
            border: 1px solid #d1d5db;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }
        
        /* Example prompts */
        .example-prompt {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 0.75rem;
            padding: 0.75rem 1rem;
            margin: 0.5rem 0;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 0.9rem;
            color: #4a5568;
        }
        
        .example-prompt:hover {
            background: #edf2f7;
            border-color: #cbd5e0;
        }
        
        /* Sidebar navigation */
        .sidebar-nav {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            padding: 1rem 0;
        }
        
        .nav-item {
            display: flex;
            align-items: center;
            padding: 0.75rem;
            border-radius: 0.5rem;
            text-decoration: none;
            color: #4a5568;
            transition: background 0.2s;
        }
        
        .nav-item:hover {
            background: #f7fafc;
        }
        
        .nav-icon {
            font-size: 1.25rem;
            margin-right: 0.75rem;
        }
        
        /* Metrics in footer */
        .metrics-footer {
            position: fixed;
            bottom: 0;
            right: 1rem;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 0.5rem 1rem;
            border-radius: 0.5rem 0.5rem 0 0;
            border: 1px solid #e2e8f0;
            border-bottom: none;
            font-size: 0.8rem;
            color: #718096;
        }
        
        /* Loading states */
        .research-status {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 1rem;
            background: #f0f9ff;
            border: 1px solid #bae6fd;
            border-radius: 0.75rem;
            margin: 1rem 0;
            font-size: 0.9rem;
            color: #0369a1;
        }
        
        .typing-indicator {
            opacity: 0.7;
            font-style: italic;
        }
        
        /* Animated cursor */
        @keyframes blink {
            0% { opacity: 1; }
            49% { opacity: 1; }
            50% { opacity: 0; }
            99% { opacity: 0; }
            100% { opacity: 1; }
        }
        
        .cursor::after {
            content: "▌";
            animation: blink 1s infinite;
        }
        
        /* Thinking box */
        .thinking-box {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 0.75rem;
            padding: 1rem;
            margin-bottom: 1rem;
            font-size: 0.9rem;
            color: #495057;
        }
        
        .thinking-header {
            font-weight: 600;
            color: #212529;
            margin-bottom: 0.5rem;
        }
        
        /* Progress bar */
        .stProgress > div > div > div {
            background: linear-gradient(90deg, #0ea5e9, #0284c7);
        }
        
        /* Example chips */
        button[kind="secondary"] {
            border: 1px solid #d1d5db;
            padding: 0.45rem 1rem !important;
            font-size: 0.875rem;
        }
        
        button[kind="secondary"]:hover {
            background: #f3f4f6;
        }
        
        /* Metrics card styling */
        .metric-value {
            font-size: 1.5rem;
            font-weight: 600;
            color: #1a202c;
        }
        
        .metric-label {
            font-size: 0.875rem;
            color: #718096;
        }
        
        /* 3:1 layout adjustment */
        @media (min-width: 768px) {
            .main-content {
                max-width: none;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def theme_metrics(stats_data):
    """Display research statistics as clean metric cards"""
    if not stats_data:
        st.info("No research statistics available yet")
        return
    
    # Duration
    duration = stats_data.get('duration', 0)
    if isinstance(duration, (int, float)):
        duration_str = f"{duration:.1f}s"
    else:
        duration_str = str(duration)
    
    # Cost
    cost = stats_data.get('total_cost', 0)
    cost_str = f"${cost:.3f}" if cost > 0 else "$0.00"
    
    # Tool calls
    tool_calls = stats_data.get('tool_calls', 0)
    
    # Iterations
    iterations = stats_data.get('iterations', 0)
    
    # Create metric cards
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("⏱ Duration", duration_str)
        st.metric("🔧 Tool calls", tool_calls)
    
    with col2:
        st.metric("💵 Cost", cost_str)
        st.metric("🔄 Iterations", iterations)
    
    # Token usage if available
    input_tokens = stats_data.get('input_tokens', 0)
    output_tokens = stats_data.get('output_tokens', 0)
    
    if input_tokens > 0 or output_tokens > 0:
        st.markdown("**Token Usage:**")
        token_col1, token_col2 = st.columns(2)
        with token_col1:
            st.caption(f"Input: {input_tokens:,}")
        with token_col2:
            st.caption(f"Output: {output_tokens:,}")

def render_sidebar_navigation():
    """Render minimal navigation in sidebar"""
    with st.sidebar:
        # Compact header
        st.markdown("### 🇺🇾")
        
        # Navigation links with icons only
        pages = [
            ("🏠", "Home", "Home.py"),
            ("🔬", "Research", "pages/0_🔬_Research_Agent.py"),
            ("📚", "Browse", "pages/1_📚_Interview_Browser.py"),
            ("📄", "Read", "pages/2_📄_Interview_Viewer.py"),
            ("🏷️", "Themes", "pages/3_🏷️_Theme_Explorer.py"),
            ("📊", "Analytics", "pages/4_📊_Analytics.py"),
        ]
        
        # Current page detection
        current_script = __import__('streamlit').runtime.scriptrunner.get_script_run_ctx().page_script_hash
        
        for icon, label, page in pages:
            # Minimal button styling
            button_style = "nav-active" if page in str(current_script) else "nav-item"
            if st.button(f"{icon}", key=f"nav_{page}", help=label, use_container_width=True):
                st.switch_page(page)
        
        st.divider()
        
        # Minimal debug toggle
        show_debug = st.toggle("🪵", value=False, help="Debug logs")
        
        return show_debug

def create_typing_effect(text_placeholder, full_text, delay=0.02):
    """Create a typing effect for streaming responses"""
    import time
    
    for i in range(len(full_text) + 1):
        partial_text = full_text[:i]
        if i < len(full_text):
            text_placeholder.markdown(partial_text + "▌")  # Typing cursor
        else:
            text_placeholder.markdown(partial_text)  # Final text without cursor
        time.sleep(delay)

def format_research_findings(findings_data):
    """Format research findings with rich widgets"""
    if not findings_data:
        return
    
    # Key findings
    if 'key_findings' in findings_data:
        st.markdown("### 🔍 Key Findings")
        for i, finding in enumerate(findings_data['key_findings'], 1):
            st.markdown(f"**{i}.** {finding}")
        st.divider()
    
    # Topic frequencies
    if 'topics' in findings_data:
        st.markdown("### 📈 Topic Mentions")
        topics = findings_data['topics']
        if topics and isinstance(topics, list) and len(topics) > 0:
            # Simple display without pandas
            for topic_data in topics[:10]:  # Show top 10
                if isinstance(topic_data, dict) and 'topic' in topic_data and 'mentions' in topic_data:
                    st.markdown(f"**{topic_data['topic']}:** {topic_data['mentions']} mentions")
        st.divider()
    
    # Citations
    if 'citations' in findings_data:
        st.markdown("### 📚 Citations")
        citations = findings_data['citations']
        if citations and isinstance(citations, list):
            for citation in citations[:10]:  # Show top 10
                if isinstance(citation, dict):
                    interview_id = citation.get('interview_id', 'N/A')
                    turn = citation.get('turn', 'N/A')
                    preview = citation.get('text_preview', 'No preview')
                    st.markdown(f"**{interview_id}:{turn}** - {preview}")
        st.divider()

def create_progress_tracker(total_steps, current_step=0, step_description="Processing..."):
    """Create a progress tracker for long-running operations"""
    progress = current_step / total_steps if total_steps > 0 else 0
    return st.progress(progress, text=f"Step {current_step}/{total_steps}: {step_description}")

def debug_console(logs, expanded=False):
    """Render debug console with logs"""
    with st.expander("🪵 Debug Console", expanded=expanded):
        if logs:
            # Show last 300 lines to prevent overwhelming
            recent_logs = logs[-300:] if len(logs) > 300 else logs
            log_text = "\n".join(recent_logs) if isinstance(logs, list) else str(logs)
            st.code(log_text, language="bash")
        else:
            st.info("No debug logs available")