"""
Conversation flow visualization for the dashboard.
Shows turn-by-turn analysis and conversation dynamics.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any


def calculate_speaker_stats(turns) -> Dict[str, Any]:
    """Calculate speaker statistics from turns."""
    if not turns:
        return {}
    
    speakers = {}
    total_words = 0
    
    for turn in turns:
        speaker_key = f"{turn.speaker}_{turn.speaker_id}" if turn.speaker_id else turn.speaker
        if speaker_key not in speakers:
            speakers[speaker_key] = {
                'speaker': turn.speaker,
                'speaker_id': turn.speaker_id,
                'turn_count': 0,
                'word_count': 0
            }
        
        speakers[speaker_key]['turn_count'] += 1
        speakers[speaker_key]['word_count'] += turn.word_count
        total_words += turn.word_count
    
    return {
        'total_turns': len(turns),
        'total_words': total_words,
        'unique_speakers': len(speakers),
        'speakers': list(speakers.values()),
        'avg_words_per_turn': total_words / len(turns) if turns else 0
    }


def show_conversation_flow(interview_id: int, session):
    """Display conversation flow for a specific interview."""
    from src.database.models import Turn
    
    # Load turns for this interview directly 
    turns = session.query(Turn).filter_by(interview_id=interview_id).order_by(Turn.turn_number).all()
    
    if not turns:
        st.info("No conversation turns available for this interview")
        return
    
    # Calculate speaker statistics directly
    stats = calculate_speaker_stats(turns)
    
    # Display overview metrics
    st.markdown("### Conversation Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Turns", stats['total_turns'])
    
    with col2:
        st.metric("Avg Turn Length", f"{stats['avg_words_per_turn']:.1f} words")
    
    with col3:
        st.metric("Speakers", stats['unique_speakers'])
    
    with col4:
        questions = sum(1 for t in turns if '?' in t.text)
        st.metric("Questions", questions)
    
    # Speaker distribution
    st.markdown("### Speaker Distribution")
    speaker_data = stats['speakers']
    speaker_df = pd.DataFrame(speaker_data)
    
    if not speaker_df.empty:
        # Speaker turn distribution
        fig_speakers = px.pie(speaker_df, values='turn_count', names='speaker', 
                              title="Turn Distribution by Speaker")
        st.plotly_chart(fig_speakers, use_container_width=True)
        
        # Speaker word distribution  
        fig_words = px.bar(speaker_df, x='speaker', y='word_count',
                          title="Word Count by Speaker")
        st.plotly_chart(fig_words, use_container_width=True)
    
    # Turn-by-turn visualization
    st.markdown("### Conversation Timeline")
    
    # Prepare data for timeline
    timeline_data = []
    for turn in turns:
        timeline_data.append({
            'Turn': turn.turn_number,
            'Speaker': turn.speaker,
            'Words': turn.word_count,
            'Text Preview': turn.text[:100] + '...' if len(turn.text) > 100 else turn.text
        })
    
    timeline_df = pd.DataFrame(timeline_data)
    
    # Turn length over time
    fig_timeline = go.Figure()
    
    # Add bars for each speaker with different colors
    speaker_colors = px.colors.qualitative.Set2
    for i, speaker in enumerate(set(t.speaker for t in turns)):
        speaker_data = timeline_df[timeline_df['Speaker'] == speaker]
        fig_timeline.add_trace(go.Bar(
            x=speaker_data['Turn'],
            y=speaker_data['Words'],
            name=speaker,
            marker_color=speaker_colors[i % len(speaker_colors)],
            text=speaker_data['Text Preview'],
            hovertemplate='Turn %{x}<br>Speaker: %{fullData.name}<br>Words: %{y}<br>Preview: %{text}<extra></extra>'
        ))
    
    fig_timeline.update_layout(
        title="Turn Length Over Time",
        xaxis_title="Turn Number",
        yaxis_title="Word Count",
        barmode='overlay'
    )
    st.plotly_chart(fig_timeline, use_container_width=True)
    
    # Full conversation display
    st.markdown("### Full Conversation")
    
    # Option to show/hide full conversation
    show_full = st.checkbox("Show full conversation", value=False)
    
    if show_full:
        # Display the conversation in a chat-like format
        for turn in turns:
            # Create speaker badge with color
            speaker_colors = {
                'AM': '#FFE6E6', 'CR': '#E6F3FF', 'JP': '#E6FFE6',
                'Interviewer': '#F0F0F0', 'Participant': '#FFF3E6',
                'Moderator': '#F5E6FF'
            }
            
            color = speaker_colors.get(turn.speaker, '#FFFFFF')
            
            with st.container():
                st.markdown(f"""
                <div style="background-color: {color}; padding: 10px; margin: 5px 0; border-radius: 5px; border-left: 4px solid #333;">
                    <strong>Turn {turn.turn_number} - {turn.speaker}</strong> ({turn.word_count} words)
                    <br><br>
                    {turn.text}
                </div>
                """, unsafe_allow_html=True)
    
    # Conversation summary table
    st.markdown("### Turn Summary")
    summary_df = pd.DataFrame([{
        'Turn': turn.turn_number,
        'Speaker': turn.speaker,
        'Words': turn.word_count,
        'Preview': turn.text[:80] + '...' if len(turn.text) > 80 else turn.text
    } for turn in turns])
    
    st.dataframe(summary_df, use_container_width=True)
