"""
Load and cache the enriched corpus for the web app
"""

import json
import os
from typing import Dict, Any, Optional
import streamlit as st
import glob
import re
from datetime import datetime

def get_interview_date_mapping():
    """Extract date/time information from raw interview filenames"""
    date_mapping = {}
    
    # Find raw interviews directory
    possible_dirs = [
        "../data/raw/interviews",
        "../../data/raw/interviews",
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                     "../data/raw/interviews")
    ]
    
    raw_dir = None
    for dir_path in possible_dirs:
        if os.path.exists(dir_path):
            raw_dir = dir_path
            break
    
    if raw_dir:
        # Pattern: T - YYYYMMDD HHMM ID.ext
        pattern = r'T\s*-\s*(\d{8})\s+(\d{4})\s+(\d+)\.(docx|odt)'
        
        for filename in os.listdir(raw_dir):
            match = re.match(pattern, filename)
            if match:
                date_str = match.group(1)
                time_str = match.group(2)
                interview_id = match.group(3).zfill(3)  # Pad with zeros
                
                # Format date and time
                try:
                    date = datetime.strptime(date_str, "%Y%m%d").strftime("%Y-%m-%d")
                    time = f"{time_str[:2]}:{time_str[2:]}"
                    date_mapping[interview_id] = {
                        'date': date,
                        'time': time,
                        'datetime': f"{date} {time}"
                    }
                except:
                    pass
    
    return date_mapping

@st.cache_data
def load_theme_consolidation() -> Dict[str, Any]:
    """Load the theme consolidation mapping"""
    possible_dirs = [
        "../data/processed/enriched",
        "../../data/processed/enriched",
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                     "../data/processed/enriched")
    ]
    
    for dir_path in possible_dirs:
        consolidation_path = os.path.join(dir_path, "theme_consolidation.json")
        if os.path.exists(consolidation_path):
            with open(consolidation_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    
    return {}

@st.cache_data
def load_enriched_corpus() -> Dict[str, Any]:
    """Load the enriched corpus with caching"""
    # Find the enriched directory
    possible_dirs = [
        "../data/processed/enriched",
        "../../data/processed/enriched",
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                     "../data/processed/enriched")
    ]
    
    enriched_dir = None
    for dir_path in possible_dirs:
        if os.path.exists(dir_path):
            enriched_dir = dir_path
            break
    
    if not enriched_dir:
        st.error("Enriched data directory not found. Please run 'make enrich' to generate the enriched corpus")
        return {'interviews': {}, 'turns': {}, 'metadata': {}, 'theme_consolidation': {}}
    
    # Get date mapping from raw filenames
    date_mapping = get_interview_date_mapping()
    
    # Create lookup indices
    interview_index = {}
    turn_index = {}
    
    # Load each enriched interview file
    enriched_files = glob.glob(os.path.join(enriched_dir, "*_enriched.json"))
    
    for file_path in enriched_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                interview_data = json.load(f)
            
            # Extract interview ID from filename
            filename = os.path.basename(file_path)
            interview_id = filename.replace('_enriched.json', '')
            
            # Add date/time metadata if available
            if interview_id in date_mapping:
                interview_data['metadata']['date'] = date_mapping[interview_id]['date']
                interview_data['metadata']['time'] = date_mapping[interview_id]['time']
                interview_data['metadata']['datetime'] = date_mapping[interview_id]['datetime']
            
            # Store in index
            interview_index[interview_id] = interview_data
            
            # Index all turns
            for turn in interview_data.get('turns', []):
                if isinstance(turn, dict) and 'turn_number' in turn:
                    turn_key = f"{interview_id}:{turn['turn_number']}"
                    turn_index[turn_key] = {
                        'interview_id': interview_id,
                        'turn': turn,
                        'interview_summary': interview_data.get('annotation', {}).get('interview_annotation', {})
                    }
                    
        except Exception as e:
            st.warning(f"Error loading {file_path}: {e}")
            continue
    
    # Calculate metadata from loaded interviews
    total_speakers = set()
    total_turns = 0
    
    for interview_id, interview in interview_index.items():
        # Count turns
        turns = interview.get('turns', [])
        total_turns += len(turns)
        
        # Count unique speakers
        for turn in turns:
            if 'speaker' in turn:
                total_speakers.add(turn['speaker'])
    
    metadata = {
        'total_interviews': len(interview_index),
        'total_turns': total_turns,
        'total_speakers': len(total_speakers)
    }
    
    summary_path = os.path.join(enriched_dir, "_enriched_corpus_summary.json")
    if os.path.exists(summary_path):
        try:
            with open(summary_path, 'r') as f:
                summary_data = json.load(f)
                metadata['total_speakers'] = summary_data.get('total_speakers', 0)
        except:
            pass
    
    # Load theme consolidation if available
    theme_consolidation = load_theme_consolidation()
    
    return {
        'interviews': interview_index,
        'turns': turn_index,
        'metadata': metadata,
        'theme_consolidation': theme_consolidation
    }

def get_turn_preview(turn_ref: str, corpus_data: Dict[str, Any], max_length: int = 200) -> Optional[Dict[str, Any]]:
    """Get a preview of a turn for hover display"""
    turn_data = corpus_data['turns'].get(turn_ref)
    
    if not turn_data:
        return None
    
    turn = turn_data['turn']
    text = turn.get('text', '')
    
    # Truncate if needed
    preview_text = text if len(text) <= max_length else text[:max_length] + "..."
    
    return {
        'turn_ref': turn_ref,
        'speaker': turn.get('speaker', 'Unknown'),
        'text': preview_text,
        'full_text': text,
        'themes': turn.get('themes', []),
        'interview_id': turn_data['interview_id']
    }

def get_interview_context(interview_id: str, corpus_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get full interview with enriched data"""
    interview = corpus_data['interviews'].get(interview_id)
    
    if not interview:
        return None
    
    # Extract annotation data
    annotation = interview.get('annotation', {})
    
    # Build enriched summary from annotation fields
    enriched_summary = {
        'overview': annotation.get('summary', ''),
        'themes': annotation.get('key_themes', []),
        'key_quotes': annotation.get('notable_quotes', []),
        'tags': annotation.get('tags', []),
        'research_notes': annotation.get('research_notes', ''),
        'conversation_structure': annotation.get('conversation_structure', {})
    }
    
    return {
        'id': interview_id,
        'summary': enriched_summary,
        'enriched_summary': enriched_summary,
        'annotation': annotation,
        'turns': interview.get('turns', []),
        'metadata': interview.get('metadata', {}),
        'themes': annotation.get('key_themes', [])
    }