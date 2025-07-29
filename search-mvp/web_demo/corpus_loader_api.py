"""
Load and cache the enriched corpus for the API server (no Streamlit dependencies)
"""

import json
import os
from typing import Dict, Any, Optional
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

# Cache for the corpus
_corpus_cache = None

def load_enriched_corpus(force_reload: bool = False) -> Optional[Dict[str, Any]]:
    """Load the enriched corpus with annotations"""
    global _corpus_cache
    
    if _corpus_cache is not None and not force_reload:
        return _corpus_cache
    
    # Try to load from a single corpus file first
    possible_corpus_paths = [
        "../data/processed/enriched/_enriched_corpus_summary.json",
        "../../data/processed/enriched/_enriched_corpus_summary.json",
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                     "data/processed/enriched/_enriched_corpus_summary.json")
    ]
    
    corpus_path = None
    for path in possible_corpus_paths:
        if os.path.exists(path):
            corpus_path = path
            break
    
    if corpus_path:
        try:
            with open(corpus_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Check if this is the summary file format
                if isinstance(data, dict) and 'interviews' in data and isinstance(data['interviews'], list):
                    print("Detected summary file format - loading individual enriched files instead")
                    corpus = None  # Will fall back to loading individual files
                else:
                    corpus = data
        except Exception as e:
            print(f"Error loading corpus file: {e}")
            corpus = None
    
    if corpus_path and corpus is None:
        # Detected summary format, continue to load individual files
        pass
        
    if corpus is None:
        # Load from individual enriched files
        corpus = {}
        enriched_dirs = [
            "../../data/processed/enriched",
            "../data/processed/enriched",
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                         "data/processed/enriched")
        ]
        
        enriched_dir = None
        for dir_path in enriched_dirs:
            if os.path.exists(dir_path):
                enriched_dir = dir_path
                break
        
        if enriched_dir:
            print(f"Loading enriched interviews from {enriched_dir}")
            enriched_files = [f for f in os.listdir(enriched_dir) if f.endswith('_enriched.json')]
            print(f"Found {len(enriched_files)} enriched files")
            
            for filename in sorted(enriched_files):
                interview_id = filename.replace('_enriched.json', '')
                try:
                    with open(os.path.join(enriched_dir, filename), 'r', encoding='utf-8') as f:
                        interview_data = json.load(f)
                        corpus[interview_id] = interview_data
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
            
            print(f"Loaded {len(corpus)} interviews into corpus")
        
        # If no enriched files, fall back to structured files
        if not corpus:
            structured_dirs = [
                "../../data/processed/structured",
                "../data/processed/structured",
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                             "data/processed/structured")
            ]
            
            structured_dir = None
            for dir_path in structured_dirs:
                if os.path.exists(dir_path):
                    structured_dir = dir_path
                    break
            
            if structured_dir:
                print(f"Loading interviews from {structured_dir}")
                for filename in sorted(os.listdir(structured_dir)):
                    if filename.endswith('.json') and not filename.startswith('_'):
                        interview_id = filename.replace('interview_', '').replace('.json', '')
                        try:
                            with open(os.path.join(structured_dir, filename), 'r', encoding='utf-8') as f:
                                interview_data = json.load(f)
                                corpus[interview_id] = interview_data
                        except Exception as e:
                            print(f"Error loading {filename}: {e}")
            else:
                print("Warning: No interview data found")
                return None
    
    if not corpus:
        print("Warning: No interview data loaded")
        return None
    
    # Get date mapping
    date_mapping = get_interview_date_mapping()
    
    # Enrich with date/time information
    for interview_id, interview_data in corpus.items():
        # Skip if interview_data is not a dictionary
        if not isinstance(interview_data, dict):
            print(f"Warning: Interview {interview_id} data is not a dictionary: {type(interview_data)}")
            continue
            
        if 'metadata' not in interview_data:
            interview_data['metadata'] = {}
        
        if interview_id in date_mapping:
            interview_data['metadata'].update(date_mapping[interview_id])
    
    _corpus_cache = corpus
    print(f"Successfully loaded enriched corpus with {len(corpus)} interviews")
    return corpus

def get_locations_from_corpus(corpus: Dict[str, Any]) -> Dict[str, str]:
    """Extract location information from corpus annotations"""
    locations = {}
    
    for interview_id, interview_data in corpus.items():
        location = None
        
        # Try to get location from annotation
        if 'annotation' in interview_data and 'summary' in interview_data['annotation']:
            summary = interview_data['annotation']['summary']
            if 'location' in summary:
                location = summary['location']
        
        # Default to pattern matching if no location found
        if not location:
            # Simple heuristic based on interview ID ranges (you can adjust these)
            id_num = int(interview_id)
            if id_num <= 12:
                location = 'Montevideo'
            elif id_num <= 24:
                location = 'Salto'
            else:
                location = 'Rivera'
        
        locations[interview_id] = location
    
    return locations