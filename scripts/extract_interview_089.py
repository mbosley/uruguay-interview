#!/usr/bin/env python3
"""
Extract comprehensive data for interview 089
"""

import json
import sys
from pathlib import Path

def extract_interview_data():
    """Extract all data for interview 089"""
    
    # Read the annotation file
    annotation_file = Path("data/processed/annotations/production/089_final_annotation.json")
    text_file = Path("data/processed/interviews_txt/20250529_1400_089.txt")
    
    if not annotation_file.exists():
        print(f"Error: {annotation_file} not found")
        return
        
    if not text_file.exists():
        print(f"Error: {text_file} not found")
        return
    
    # Load JSON data
    with open(annotation_file, 'r', encoding='utf-8') as f:
        annotation_data = json.load(f)
    
    # Read raw text
    with open(text_file, 'r', encoding='utf-8') as f:
        raw_text = f.read()
    
    # Extract and organize data
    data = annotation_data.get('annotation_data', {})
    
    result = {
        'interview_metadata': data.get('interview_metadata', {}),
        'participant_profile': data.get('participant_profile', {}),
        'priority_analysis': data.get('priority_analysis', {}),
        'narrative_features': data.get('narrative_features', {}),
        'key_narratives': data.get('key_narratives', {}),
        'interview_dynamics': data.get('interview_dynamics', {}),
        'analytical_synthesis': data.get('analytical_synthesis', {}),
        'conversation_analysis': data.get('conversation_analysis', {}),
        'raw_text': raw_text,
        'processing_info': annotation_data.get('production_info', {}),
        'annotation_metadata': data.get('annotation_metadata', {})
    }
    
    # Print formatted output
    print("="*80)
    print("INTERVIEW 089 - COMPLETE DATA EXTRACTION")
    print("="*80)
    
    print("\n📅 INTERVIEW METADATA")
    print("-" * 40)
    metadata = result['interview_metadata']
    print(f"Interview ID: {metadata.get('interview_id')}")
    print(f"Date: {metadata.get('date')}")
    print(f"Location: {metadata.get('municipality')}, {metadata.get('department')}")
    print(f"Locality Size: {metadata.get('locality_size')}")
    print(f"Duration: {metadata.get('duration_minutes')} minutes")
    print(f"Interviewers: {', '.join(metadata.get('interviewer_ids', []))}")
    print(f"Context: {metadata.get('interview_context')}")
    
    print("\n👤 PARTICIPANT PROFILE")
    print("-" * 40)
    profile = result['participant_profile']
    print(f"Age Range: {profile.get('age_range')}")
    print(f"Gender: {profile.get('gender')}")
    print(f"Occupation Sector: {profile.get('occupation_sector')}")
    print(f"Organization: {profile.get('organizational_affiliation')}")
    print(f"Political Stance: {profile.get('self_described_political_stance', 'Not specified')}")
    print(f"Profile Notes: {profile.get('profile_notes')}")
    
    print("\n🏛️ NATIONAL PRIORITIES")
    print("-" * 40)
    for priority in result['priority_analysis'].get('national_priorities', []):
        print(f"{priority['rank']}. {priority['theme']}")
        print(f"   Issues: {', '.join(priority['specific_issues'])}")
        print(f"   Emotion: {priority['emotional_intensity']}/1.0")
        print(f"   Key quotes: {priority['supporting_quotes']}")
        print(f"   Narrative: {priority['narrative_elaboration']}")
        print()
    
    print("\n🏘️ LOCAL PRIORITIES")
    print("-" * 40)
    for priority in result['priority_analysis'].get('local_priorities', []):
        print(f"{priority['rank']}. {priority['theme']}")
        print(f"   Issues: {', '.join(priority['specific_issues'])}")
        print(f"   Emotion: {priority['emotional_intensity']}/1.0")
        print(f"   Key quotes: {priority['supporting_quotes']}")
        print(f"   Narrative: {priority['narrative_elaboration']}")
        print()
    
    print("\n📖 NARRATIVE FEATURES")
    print("-" * 40)
    narrative = result['narrative_features']
    print(f"Dominant Frame: {narrative.get('dominant_frame')}")
    print(f"Frame Narrative: {narrative.get('frame_narrative')}")
    print(f"Temporal Orientation: {narrative.get('temporal_orientation')}")
    print(f"Agency Attribution:")
    agency = narrative.get('agency_attribution', {})
    print(f"  - Government Responsibility: {agency.get('government_responsibility')}")
    print(f"  - Individual Responsibility: {agency.get('individual_responsibility')}")
    print(f"  - Structural Factors: {agency.get('structural_factors')}")
    print(f"Cultural Patterns: {', '.join(narrative.get('cultural_patterns_identified', []))}")
    
    print("\n🗣️ KEY NARRATIVES")
    print("-" * 40)
    key_narr = result['key_narratives']
    print(f"Identity: {key_narr.get('identity_narrative')}")
    print(f"Problem: {key_narr.get('problem_narrative')}")
    print(f"Hope: {key_narr.get('hope_narrative')}")
    print(f"Memorable Quotes: {key_narr.get('memorable_quotes')}")
    print(f"Rhetorical Strategies: {', '.join(key_narr.get('rhetorical_strategies', []))}")
    
    print("\n🤝 INTERVIEW DYNAMICS")  
    print("-" * 40)
    dynamics = result['interview_dynamics']
    print(f"Rapport: {dynamics.get('rapport')}")
    print(f"Engagement: {dynamics.get('participant_engagement')}")
    print(f"Coherence: {dynamics.get('coherence')}")
    print(f"Interviewer Effects: {dynamics.get('interviewer_effects')}")
    
    print("\n🔬 ANALYTICAL SYNTHESIS")
    print("-" * 40)
    analysis = result['analytical_synthesis']
    print(f"Tensions/Contradictions: {analysis.get('tensions_contradictions')}")
    print(f"Silences/Omissions: {analysis.get('silences_omissions')}")
    print(f"Cultural Context: {analysis.get('cultural_context_notes')}")
    print(f"Broader Connections: {analysis.get('connections_to_broader_themes')}")
    
    print("\n💬 CONVERSATION ANALYSIS")
    print("-" * 40)
    conv = result['conversation_analysis']
    print(f"Total Turns: {conv.get('total_turns_detected')}")
    print(f"Participant Turns: {conv.get('participant_turns')}")
    print(f"Interviewer Turns: {conv.get('interviewer_turns')}")
    
    print("\nTURN-BY-TURN ANALYSIS:")
    print("=" * 60)
    
    # Show first 10 turns as examples
    for i, turn in enumerate(conv.get('turns', [])[:10]):
        turn_id = turn.get('turn_id')
        print(f"\n🗨️ TURN {turn_id}")
        print(f"Function: {turn.get('turn_analysis', {}).get('primary_function')}")
        print(f"Topics: {', '.join(turn.get('content_analysis', {}).get('topics', []))}")
        print(f"Evidence: {turn.get('evidence_analysis', {}).get('evidence_type')}")
        print(f"Emotion: {turn.get('emotional_analysis', {}).get('emotional_valence')} ({turn.get('emotional_analysis', {}).get('emotional_intensity')})")
        print(f"Significance: {turn.get('turn_significance')}")
    
    if len(conv.get('turns', [])) > 10:
        print(f"\n... and {len(conv.get('turns', [])) - 10} more turns")
    
    print("\n📊 PROCESSING INFO")
    print("-" * 40)
    proc_info = result['processing_info']
    print(f"Processed: {proc_info.get('processed_at')}")
    print(f"Processing Time: {proc_info.get('processing_time', 0):.2f} seconds")
    print(f"Pipeline Version: {proc_info.get('pipeline_version')}")
    
    print("\n📋 ANNOTATION METADATA")
    print("-" * 40)
    ann_meta = result['annotation_metadata']
    print(f"Approach: {ann_meta.get('annotator_approach')}")
    print(f"Timestamp: {ann_meta.get('annotation_timestamp')}")
    print(f"Overall Confidence: {ann_meta.get('overall_confidence')}")
    print(f"Uncertainty Flags: {', '.join(ann_meta.get('uncertainty_flags', []))}")
    print(f"Uncertainty Narrative: {ann_meta.get('uncertainty_narrative')}")
    
    return result

if __name__ == "__main__":
    result = extract_interview_data()