"""
Additional visualization utilities for the dashboard.
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any
import networkx as nx
from collections import Counter


def create_priority_sunburst(priorities_df: pd.DataFrame) -> go.Figure:
    """Create a sunburst chart of priorities by scope and category."""
    if priorities_df.empty:
        return go.Figure()
    
    # Prepare hierarchical data
    sunburst_data = priorities_df.groupby(['scope', 'category']).size().reset_index(name='count')
    
    fig = go.Figure(go.Sunburst(
        labels=['All'] + sunburst_data['scope'].tolist() + sunburst_data['category'].tolist(),
        parents=[''] + ['All'] * len(sunburst_data['scope'].unique()) + sunburst_data['scope'].tolist(),
        values=[sunburst_data['count'].sum()] + 
               [sunburst_data[sunburst_data['scope'] == s]['count'].sum() 
                for s in sunburst_data['scope'].unique()] + 
               sunburst_data['count'].tolist(),
        branchvalues="total",
    ))
    
    fig.update_layout(
        title="Priority Distribution by Scope and Category",
        margin=dict(t=50, l=0, r=0, b=0)
    )
    
    return fig


def create_sentiment_timeline(interviews_df: pd.DataFrame) -> go.Figure:
    """Create a timeline showing sentiment evolution."""
    if interviews_df.empty or 'date' not in interviews_df.columns:
        return go.Figure()
    
    # Group by date and sentiment
    sentiment_timeline = interviews_df.groupby(['date', 'overall_sentiment']).size().reset_index(name='count')
    
    fig = px.area(
        sentiment_timeline,
        x='date',
        y='count',
        color='overall_sentiment',
        title='Sentiment Evolution Over Time',
        color_discrete_map={
            'positive': '#2ecc71',
            'negative': '#e74c3c',
            'neutral': '#95a5a6',
            'mixed': '#3498db'
        }
    )
    
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Number of Interviews",
        hovermode='x unified'
    )
    
    return fig


def create_theme_network(themes_df: pd.DataFrame, min_cooccurrence: int = 2) -> go.Figure:
    """Create a network graph showing theme co-occurrences."""
    if themes_df.empty:
        return go.Figure()
    
    # Find co-occurring themes within interviews
    theme_pairs = []
    for interview_id in themes_df['interview_id'].unique():
        interview_themes = themes_df[themes_df['interview_id'] == interview_id]['theme'].tolist()
        for i in range(len(interview_themes)):
            for j in range(i + 1, len(interview_themes)):
                theme_pairs.append(tuple(sorted([interview_themes[i], interview_themes[j]])))
    
    # Count co-occurrences
    pair_counts = Counter(theme_pairs)
    
    # Build network
    G = nx.Graph()
    for (theme1, theme2), count in pair_counts.items():
        if count >= min_cooccurrence:
            G.add_edge(theme1, theme2, weight=count)
    
    if len(G.nodes()) == 0:
        return go.Figure()
    
    # Calculate positions
    pos = nx.spring_layout(G, k=2, iterations=50)
    
    # Create edge traces
    edge_traces = []
    for edge in G.edges(data=True):
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        weight = edge[2]['weight']
        
        edge_trace = go.Scatter(
            x=[x0, x1, None],
            y=[y0, y1, None],
            mode='lines',
            line=dict(width=weight * 0.5, color='gray'),
            hoverinfo='none',
            showlegend=False
        )
        edge_traces.append(edge_trace)
    
    # Create node trace
    node_x = []
    node_y = []
    node_text = []
    node_size = []
    
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(f"{node}<br>Connections: {G.degree(node)}")
        node_size.append(G.degree(node) * 10 + 10)
    
    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode='markers+text',
        text=[node for node in G.nodes()],
        textposition="top center",
        hoverinfo='text',
        hovertext=node_text,
        marker=dict(
            size=node_size,
            color='lightblue',
            line=dict(width=2, color='darkblue')
        )
    )
    
    # Create figure
    fig = go.Figure(data=edge_traces + [node_trace])
    
    fig.update_layout(
        title="Theme Co-occurrence Network",
        showlegend=False,
        hovermode='closest',
        margin=dict(b=0, l=0, r=0, t=50),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='white'
    )
    
    return fig


def create_geographic_heatmap(data_df: pd.DataFrame, value_column: str) -> go.Figure:
    """Create a heatmap of values by location."""
    if data_df.empty or value_column not in data_df.columns:
        return go.Figure()
    
    # Aggregate by location
    location_data = data_df.groupby(['department', 'location'])[value_column].mean().reset_index()
    
    # Create heatmap matrix
    heatmap_data = location_data.pivot(index='location', columns='department', values=value_column)
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns,
        y=heatmap_data.index,
        colorscale='Blues',
        text=heatmap_data.values.round(2),
        texttemplate='%{text}',
        textfont={"size": 10},
        hoverongaps=False
    ))
    
    fig.update_layout(
        title=f"{value_column.replace('_', ' ').title()} by Location",
        xaxis_title="Department",
        yaxis_title="Location",
        height=600
    )
    
    return fig


def create_word_cloud_data(texts: List[str]) -> Dict[str, int]:
    """Generate word frequency data for word cloud visualization."""
    from collections import Counter
    import re
    
    # Spanish stop words (basic set)
    stop_words = {
        'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'ser', 'se', 'no', 
        'haber', 'por', 'con', 'su', 'para', 'como', 'estar', 'tener', 'le',
        'lo', 'todo', 'pero', 'más', 'hacer', 'o', 'poder', 'decir', 'este',
        'ir', 'otro', 'ese', 'la', 'si', 'me', 'ya', 'ver', 'porque', 'dar',
        'cuando', 'él', 'muy', 'sin', 'vez', 'mucho', 'saber', 'qué', 'sobre',
        'mi', 'alguno', 'mismo', 'yo', 'también', 'hasta', 'año', 'dos', 'querer',
        'es', 'son', 'las', 'los', 'del', 'al', 'uno', 'una', 'nos', 'ni'
    }
    
    # Combine all texts
    combined_text = ' '.join(texts).lower()
    
    # Extract words (handling Spanish characters)
    words = re.findall(r'\b[a-záéíóúñü]+\b', combined_text)
    
    # Filter and count
    word_counts = Counter(word for word in words 
                         if len(word) > 3 and word not in stop_words)
    
    return dict(word_counts.most_common(50))


def create_interview_comparison(interviews: List[Any]) -> pd.DataFrame:
    """Create a comparison matrix of interviews."""
    comparison_data = []
    
    for interview in interviews:
        if interview.annotations:
            annotation = interview.annotations[0]
            
            row = {
                'Interview ID': interview.id,
                'Location': interview.location,
                'Date': interview.date,
                'Participants': interview.participant_count,
                'Sentiment': annotation.overall_sentiment,
                'Confidence': annotation.confidence_score,
                'National Priorities': len([p for p in annotation.priorities if p.scope == 'national']),
                'Local Priorities': len([p for p in annotation.priorities if p.scope == 'local']),
                'Themes': len(annotation.themes),
                'Top Priority': annotation.priorities[0].category if annotation.priorities else 'None'
            }
            comparison_data.append(row)
    
    return pd.DataFrame(comparison_data)