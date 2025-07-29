"""
Uruguay Interview Research Agent - Direct Research Tool Interface
"""

import streamlit as st
import os
import sys
import time
import re
import asyncio
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import threading

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
web_demo_dir = os.path.dirname(current_dir)
parent_dir = os.path.dirname(web_demo_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, web_demo_dir)

# Load environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(parent_dir, '.env'))

# Import project modules
from interview_research_agent_improved import InterviewResearchAgent
from config.providers import get_provider_config
from utils.styling import inject_css, render_sidebar_navigation

# Page config
st.set_page_config(
    page_title="Uruguay Research Agent",
    page_icon="🇺🇾",
    layout="wide"
)

# Custom CSS for trace display
st.markdown("""
<style>
    .trace-container {
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        background-color: #1e1e1e;
        color: #d4d4d4;
        border-radius: 8px;
        padding: 20px;
        height: 400px;
        overflow-y: auto;
        margin-bottom: 20px;
        font-size: 14px;
        line-height: 1.6;
    }
    .trace-iteration {
        color: #4ec9b0;
        font-weight: bold;
        margin-top: 15px;
    }
    .trace-thinking {
        color: #9cdcfe;
        margin-left: 20px;
    }
    .trace-tool {
        color: #dcdcaa;
        margin-left: 20px;
    }
    .trace-result {
        color: #ce9178;
        margin-left: 40px;
        white-space: pre-wrap;
    }
    .report-container {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 30px;
        margin-top: 20px;
        font-size: 16px;
        line-height: 1.8;
    }
    .report-container h1, .report-container h2, .report-container h3 {
        margin-top: 20px;
        margin-bottom: 10px;
    }
    .metrics-container {
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

inject_css()

# Constants
LOG_FILE = Path(parent_dir) / "logs/agent_session.log"

# Initialize session state
if 'running' not in st.session_state:
    st.session_state.running = False
if 'trace_lines' not in st.session_state:
    st.session_state.trace_lines = []
if 'final_report' not in st.session_state:
    st.session_state.final_report = ""
if 'stats' not in st.session_state:
    st.session_state.stats = {}
if 'agent_instance' not in st.session_state:
    st.session_state.agent_instance = None

def format_trace_line(line):
    """Format a log line for pretty display in the trace"""
    # Remove timestamp and log level
    if '|' in line:
        parts = line.split('|', 2)
        if len(parts) > 2:
            content = parts[2].strip()
        else:
            content = line
    else:
        content = line
    
    # Format based on content
    if '🔄 Iteration' in content:
        return f'<div class="trace-iteration">{content}</div>'
    elif '💭' in content:
        return f'<div class="trace-thinking">{content.replace("💭", "🧠 Thinking:")}</div>'
    elif '🔧' in content:
        return f'<div class="trace-tool">{content.replace("🔧", "🔧 Tool Call:")}</div>'
    elif '📊' in content or 'Tool Result:' in content:
        # Clean up the result formatting
        result = content.replace('📊', '').replace('Tool Result:', '').strip()
        if result:
            return f'<div class="trace-result">📊 Result:\n{result}</div>'
    elif content.strip():
        return f'<div style="margin-left: 20px; color: #d4d4d4;">{content}</div>'
    return ''

def monitor_research_progress(trace_container, progress_bar):
    """Monitor the log file and update the UI with real-time progress"""
    last_size = 0
    trace_html = []
    
    while st.session_state.running:
        try:
            if LOG_FILE.exists() and LOG_FILE.stat().st_size > last_size:
                with open(LOG_FILE, 'r', encoding='utf-8') as f:
                    f.seek(last_size)
                    new_content = f.read()
                    last_size = f.tell()
                
                # Process new lines
                for line in new_content.strip().split('\n'):
                    if line.strip():
                        formatted = format_trace_line(line)
                        if formatted:
                            trace_html.append(formatted)
                            st.session_state.trace_lines.append(formatted)
                        
                        # Update progress based on iterations
                        if 'Iteration' in line:
                            match = re.search(r'Iteration (\d+)/(\d+)', line)
                            if match:
                                current, total = map(int, match.groups())
                                progress = current / total
                                progress_bar.progress(progress, f"Research Progress: Step {current} of {total}")
                
                # Update trace display
                if trace_html:
                    trace_container.markdown(
                        f'<div class="trace-container">{"".join(trace_html)}</div>',
                        unsafe_allow_html=True
                    )
        except Exception as e:
            pass
        
        time.sleep(0.1)

async def run_research(question):
    """Run the research agent and capture results"""
    # Clear log file
    if LOG_FILE.exists():
        LOG_FILE.unlink()
    LOG_FILE.parent.mkdir(exist_ok=True)
    LOG_FILE.touch()
    
    # Initialize agent if needed
    if st.session_state.agent_instance is None:
        st.session_state.agent_instance = InterviewResearchAgent(
            provider="moonshot",
            verbose=True,
            research_mode=True
        )
    
    # Run research
    start_time = datetime.now()
    result = await st.session_state.agent_instance.autonomous_research(question, max_iterations=8)
    end_time = datetime.now()
    
    # Extract stats
    stats = result.get('stats', {})
    stats['duration'] = (end_time - start_time).total_seconds()
    
    return result.get('final_response', 'No response generated.'), stats

def stream_report(report_text, container):
    """Stream the final report with typing effect"""
    words = report_text.split()
    streamed = []
    
    for i, word in enumerate(words):
        streamed.append(word)
        display_text = ' '.join(streamed)
        
        # Add cursor at the end
        if i < len(words) - 1:
            display_text += ' ▌'
        
        container.markdown(
            f'<div class="report-container">{display_text}</div>',
            unsafe_allow_html=True
        )
        time.sleep(0.03)
    
    # Final display without cursor
    container.markdown(
        f'<div class="report-container">{" ".join(words)}</div>',
        unsafe_allow_html=True
    )

def main():
    # Sidebar
    render_sidebar_navigation()
    
    # Main content
    st.title("🇺🇾 Uruguay Interview Research Agent")
    st.markdown("Ask a research question about the citizen consultation interviews. The agent will analyze the corpus and provide a comprehensive answer.")
    
    # Input form
    with st.form("research_form", clear_on_submit=False):
        question = st.text_area(
            "Enter your research question:",
            placeholder="e.g., What are the main healthcare concerns mentioned by citizens?",
            height=100
        )
        col1, col2, col3 = st.columns([1, 1, 3])
        with col1:
            submit = st.form_submit_button("🔍 Start Research", type="primary", use_container_width=True)
        with col2:
            if st.form_submit_button("🗑️ Clear", use_container_width=True):
                st.session_state.trace_lines = []
                st.session_state.final_report = ""
                st.session_state.stats = {}
                st.rerun()
    
    # Handle research request
    if submit and question and not st.session_state.running:
        st.session_state.running = True
        st.session_state.trace_lines = []
        st.session_state.final_report = ""
        st.session_state.stats = {}
        
        # Create containers for live updates
        st.markdown("### 🔍 Agent Trace")
        trace_container = st.empty()
        progress_bar = st.progress(0, "Initializing research...")
        
        st.markdown("### 📄 Final Report")
        report_container = st.empty()
        
        # Start monitoring in background thread
        monitor_thread = threading.Thread(
            target=monitor_research_progress,
            args=(trace_container, progress_bar),
            daemon=True
        )
        monitor_thread.start()
        
        # Run research
        with st.spinner("Research agent is working..."):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            final_report, stats = loop.run_until_complete(run_research(question))
            
        # Stop monitoring
        st.session_state.running = False
        time.sleep(0.5)  # Let monitor thread finish
        
        # Update progress
        progress_bar.progress(1.0, "Research complete!")
        
        # Stream final report
        st.session_state.final_report = final_report
        st.session_state.stats = stats
        stream_report(final_report, report_container)
        
        # Show metrics
        st.markdown("### 📊 Research Metrics")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("⏱ Duration", f"{stats.get('duration', 0):.1f}s")
        col2.metric("🔧 Tool Calls", stats.get('tool_calls', 0))
        col3.metric("💬 LLM Calls", stats.get('llm_calls', 0))
        col4.metric("💵 Est. Cost", f"${stats.get('total_cost', 0):.4f}")
        
        st.success("✅ Research complete!")
        
    elif submit and not question:
        st.error("Please enter a research question.")
    
    # Show previous results if available
    elif st.session_state.final_report and not st.session_state.running:
        st.markdown("### 🔍 Agent Trace")
        if st.session_state.trace_lines:
            trace_html = "".join(st.session_state.trace_lines)
            st.markdown(
                f'<div class="trace-container">{trace_html}</div>',
                unsafe_allow_html=True
            )
        
        st.markdown("### 📄 Final Report")
        st.markdown(
            f'<div class="report-container">{st.session_state.final_report}</div>',
            unsafe_allow_html=True
        )
        
        if st.session_state.stats:
            st.markdown("### 📊 Research Metrics")
            stats = st.session_state.stats
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("⏱ Duration", f"{stats.get('duration', 0):.1f}s")
            col2.metric("🔧 Tool Calls", stats.get('tool_calls', 0))
            col3.metric("💬 LLM Calls", stats.get('llm_calls', 0))
            col4.metric("💵 Est. Cost", f"${stats.get('total_cost', 0):.4f}")

if __name__ == "__main__":
    main()