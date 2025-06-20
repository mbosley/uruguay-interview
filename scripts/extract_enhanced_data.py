#!/usr/bin/env python3
"""
Enhanced data extraction from JSON annotations to populate comprehensive database schema.
Maps rich JSON annotation data to our enhanced database models.
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class EnhancedDataExtractor:
    """Extract comprehensive data from JSON annotations for enhanced database schema."""
    
    def __init__(self):
        self.extraction_stats = {
            'interviews_processed': 0,
            'participants_extracted': 0,
            'narrative_features_extracted': 0,
            'turns_extracted': 0,
            'priorities_extracted': 0,
            'errors': []
        }
    
    def extract_interview_metadata(self, annotation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract enhanced interview metadata."""
        interview_meta = annotation_data.get('interview_metadata', {})
        
        return {
            'interview_id': interview_meta.get('interview_id'),
            'date': interview_meta.get('date'),
            'municipality': interview_meta.get('municipality'),
            'department': interview_meta.get('department'),
            'locality_size': interview_meta.get('locality_size'),
            'duration_minutes': interview_meta.get('duration_minutes'),
            'interviewer_ids': interview_meta.get('interviewer_ids', []),
            'interview_context': interview_meta.get('interview_context')
        }
    
    def extract_participant_profile(self, annotation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract comprehensive participant profile data."""
        profile = annotation_data.get('participant_profile', {})
        
        return {
            'age_range': profile.get('age_range'),
            'gender': profile.get('gender'),
            'occupation_sector': profile.get('occupation_sector'),
            'organizational_affiliation': profile.get('organizational_affiliation'),
            'self_described_political_stance': profile.get('self_described_political_stance'),
            'profile_confidence': profile.get('profile_confidence'),
            'profile_notes': profile.get('profile_notes')
        }
    
    def extract_narrative_features(self, annotation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract narrative features and temporal analysis."""
        narrative = annotation_data.get('narrative_features', {})
        agency = narrative.get('agency_attribution', {})
        
        return {
            'dominant_frame': narrative.get('dominant_frame'),
            'frame_narrative': narrative.get('frame_narrative'),
            'temporal_orientation': narrative.get('temporal_orientation'),
            'temporal_narrative': narrative.get('temporal_narrative'),
            'government_responsibility': agency.get('government_responsibility'),
            'individual_responsibility': agency.get('individual_responsibility'),
            'structural_factors': agency.get('structural_factors'),
            'agency_narrative': agency.get('agency_narrative'),
            'solution_orientation': narrative.get('solution_orientation'),
            'solution_narrative': narrative.get('solution_narrative'),
            'cultural_patterns_identified': narrative.get('cultural_patterns_identified', []),
            'narrative_confidence': narrative.get('narrative_confidence')
        }
    
    def extract_key_narratives(self, annotation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key narratives and rhetorical analysis."""
        narratives = annotation_data.get('key_narratives', {})
        
        return {
            'identity_narrative': narratives.get('identity_narrative'),
            'problem_narrative': narratives.get('problem_narrative'),
            'hope_narrative': narratives.get('hope_narrative'),
            'memorable_quotes': narratives.get('memorable_quotes', []),
            'rhetorical_strategies': narratives.get('rhetorical_strategies', []),
            'narrative_confidence': narratives.get('narrative_confidence')
        }
    
    def extract_interview_dynamics(self, annotation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract interview interaction dynamics."""
        dynamics = annotation_data.get('interview_dynamics', {})
        
        return {
            'rapport': dynamics.get('rapport'),
            'rapport_narrative': dynamics.get('rapport_narrative'),
            'participant_engagement': dynamics.get('participant_engagement'),
            'engagement_narrative': dynamics.get('engagement_narrative'),
            'coherence': dynamics.get('coherence'),
            'coherence_narrative': dynamics.get('coherence_narrative'),
            'interviewer_effects': dynamics.get('interviewer_effects'),
            'dynamics_confidence': dynamics.get('dynamics_confidence')
        }
    
    def extract_analytical_synthesis(self, annotation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract analytical synthesis."""
        synthesis = annotation_data.get('analytical_synthesis', {})
        
        return {
            'tensions_contradictions': synthesis.get('tensions_contradictions'),
            'silences_omissions': synthesis.get('silences_omissions'),
            'cultural_context_notes': synthesis.get('cultural_context_notes'),
            'connections_to_broader_themes': synthesis.get('connections_to_broader_themes'),
            'analytical_confidence': synthesis.get('analytical_confidence')
        }
    
    def extract_priorities(self, annotation_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract enhanced priority analysis."""
        priority_analysis = annotation_data.get('priority_analysis', {})
        priorities = []
        
        # Extract national priorities
        for priority in priority_analysis.get('national_priorities', []):
            priorities.append({
                'scope': 'national',
                'rank': priority.get('rank'),
                'theme': priority.get('theme'),
                'specific_issues': priority.get('specific_issues', []),
                'narrative_elaboration': priority.get('narrative_elaboration'),
                'emotional_intensity': priority.get('emotional_intensity'),
                'supporting_quotes': priority.get('supporting_quotes', []),
                'confidence': priority.get('confidence'),
                'reasoning': priority.get('reasoning')
            })
        
        # Extract local priorities
        for priority in priority_analysis.get('local_priorities', []):
            priorities.append({
                'scope': 'local',
                'rank': priority.get('rank'),
                'theme': priority.get('theme'),
                'specific_issues': priority.get('specific_issues', []),
                'narrative_elaboration': priority.get('narrative_elaboration'),
                'emotional_intensity': priority.get('emotional_intensity'),
                'supporting_quotes': priority.get('supporting_quotes', []),
                'confidence': priority.get('confidence'),
                'reasoning': priority.get('reasoning')
            })
        
        return priorities
    
    def extract_turns_analysis(self, annotation_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract comprehensive turn-by-turn analysis."""
        conversation = annotation_data.get('conversation_analysis', {})
        turns = []
        
        for turn_data in conversation.get('turns', []):
            # Extract base turn data
            turn = {
                'turn_id': turn_data.get('turn_id'),
                'turn_significance': turn_data.get('turn_significance'),
                'functional_analysis': self._extract_turn_functional_analysis(turn_data),
                'content_analysis': self._extract_turn_content_analysis(turn_data),
                'evidence_analysis': self._extract_turn_evidence_analysis(turn_data),
                'emotional_analysis': self._extract_turn_emotional_analysis(turn_data),
                'uncertainty_tracking': self._extract_turn_uncertainty_tracking(turn_data)
            }
            turns.append(turn)
        
        return turns
    
    def _extract_turn_functional_analysis(self, turn_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract functional analysis for a turn."""
        func_analysis = turn_data.get('turn_analysis', {})
        
        return {
            'reasoning': func_analysis.get('reasoning'),
            'primary_function': func_analysis.get('primary_function'),
            'secondary_functions': func_analysis.get('secondary_functions', []),
            'function_confidence': func_analysis.get('function_confidence')
        }
    
    def _extract_turn_content_analysis(self, turn_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract content analysis for a turn."""
        content_analysis = turn_data.get('content_analysis', {})
        
        return {
            'reasoning': content_analysis.get('reasoning'),
            'topics': content_analysis.get('topics', []),
            'geographic_scope': content_analysis.get('geographic_scope', []),
            'temporal_reference': content_analysis.get('temporal_reference'),
            'topic_narrative': content_analysis.get('topic_narrative'),
            'content_confidence': content_analysis.get('content_confidence')
        }
    
    def _extract_turn_evidence_analysis(self, turn_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract evidence analysis for a turn."""
        evidence_analysis = turn_data.get('evidence_analysis', {})
        
        return {
            'reasoning': evidence_analysis.get('reasoning'),
            'evidence_type': evidence_analysis.get('evidence_type'),
            'evidence_narrative': evidence_analysis.get('evidence_narrative'),
            'specificity': evidence_analysis.get('specificity'),
            'evidence_confidence': evidence_analysis.get('evidence_confidence')
        }
    
    def _extract_turn_emotional_analysis(self, turn_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract emotional analysis for a turn."""
        emotional_analysis = turn_data.get('emotional_analysis', {})
        
        return {
            'reasoning': emotional_analysis.get('reasoning'),
            'emotional_valence': emotional_analysis.get('emotional_valence'),
            'emotional_intensity': emotional_analysis.get('emotional_intensity'),
            'specific_emotions': emotional_analysis.get('specific_emotions', []),
            'emotional_narrative': emotional_analysis.get('emotional_narrative'),
            'certainty': emotional_analysis.get('certainty'),
            'rhetorical_features': emotional_analysis.get('rhetorical_features')
        }
    
    def _extract_turn_uncertainty_tracking(self, turn_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract uncertainty tracking for a turn."""
        uncertainty = turn_data.get('uncertainty_tracking', {})
        
        return {
            'coding_confidence': uncertainty.get('coding_confidence'),
            'ambiguous_aspects': uncertainty.get('ambiguous_aspects', []),
            'edge_case_flag': uncertainty.get('edge_case_flag', False),
            'alternative_interpretations': uncertainty.get('alternative_interpretations', []),
            'resolution_strategy': uncertainty.get('resolution_strategy'),
            'annotator_notes': uncertainty.get('annotator_notes')
        }
    
    def extract_annotation_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract comprehensive annotation metadata."""
        annotation_meta = data.get('annotation_data', {}).get('annotation_metadata', {})
        processing_meta = data.get('processing_metadata', {})
        production_info = data.get('production_info', {})
        
        return {
            'model_provider': 'openai',  # Inferred from our system
            'model_name': processing_meta.get('model_name', 'gpt-4.1-nano'),
            'temperature': 0.1,  # Our standard setting
            'annotation_approach': annotation_meta.get('annotator_approach', 'multipass_comprehensive'),
            'overall_confidence': annotation_meta.get('overall_confidence'),
            'uncertainty_flags': annotation_meta.get('uncertainty_flags', []),
            'uncertainty_narrative': annotation_meta.get('uncertainty_narrative'),
            'turn_coverage_percentage': processing_meta.get('turn_coverage', {}).get('coverage_percentage'),
            'analyzed_turns': processing_meta.get('turn_coverage', {}).get('analyzed_turns'),
            'expected_turns': processing_meta.get('turn_coverage', {}).get('total_turns'),
            'all_turns_analyzed': processing_meta.get('turn_coverage', {}).get('coverage_percentage') >= 99.9,
            'total_api_calls': processing_meta.get('total_api_calls'),
            'api_call_breakdown': processing_meta.get('api_call_breakdown', []),
            'processing_time': production_info.get('processing_time', processing_meta.get('processing_time')),
            'total_cost': processing_meta.get('total_cost'),
            'json_content': data.get('annotation_data')  # Store full annotation
        }
    
    def extract_processing_analytics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract detailed processing analytics."""
        processing_meta = data.get('processing_metadata', {})
        production_info = data.get('production_info', {})
        
        return {
            'model_name': processing_meta.get('model_name', 'gpt-4.1-nano'),
            'annotation_approach': processing_meta.get('annotation_approach', 'multipass_comprehensive'),
            'timeout_used': production_info.get('timeout_used'),
            'total_api_calls': processing_meta.get('total_api_calls'),
            'processing_time_seconds': production_info.get('processing_time', processing_meta.get('processing_time')),
            'total_cost': processing_meta.get('total_cost'),
            'turn_coverage_percentage': processing_meta.get('turn_coverage', {}).get('coverage_percentage'),
            'overall_confidence': data.get('annotation_data', {}).get('annotation_metadata', {}).get('overall_confidence'),
            'retry_count': production_info.get('retry_count', 0),
            'api_call_breakdown': processing_meta.get('api_call_breakdown', []),
            'processed_at': datetime.now().isoformat(),
            'pipeline_version': production_info.get('pipeline_version', 'production_v1.0')
        }
    
    def process_annotation_file(self, file_path: Path) -> Dict[str, Any]:
        """Process a single JSON annotation file and extract all data."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            annotation_data = data.get('annotation_data', {})
            
            # Extract all components
            extracted = {
                'interview_metadata': self.extract_interview_metadata(annotation_data),
                'participant_profile': self.extract_participant_profile(annotation_data),
                'narrative_features': self.extract_narrative_features(annotation_data),
                'key_narratives': self.extract_key_narratives(annotation_data),
                'interview_dynamics': self.extract_interview_dynamics(annotation_data),
                'analytical_synthesis': self.extract_analytical_synthesis(annotation_data),
                'priorities': self.extract_priorities(annotation_data),
                'turns': self.extract_turns_analysis(annotation_data),
                'annotation_metadata': self.extract_annotation_metadata(data),
                'processing_analytics': self.extract_processing_analytics(data)
            }
            
            # Update stats
            self.extraction_stats['interviews_processed'] += 1
            self.extraction_stats['participants_extracted'] += 1
            self.extraction_stats['narrative_features_extracted'] += 1
            self.extraction_stats['turns_extracted'] += len(extracted['turns'])
            self.extraction_stats['priorities_extracted'] += len(extracted['priorities'])
            
            return extracted
            
        except Exception as e:
            error_msg = f"Error processing {file_path}: {str(e)}"
            self.extraction_stats['errors'].append(error_msg)
            print(f"❌ {error_msg}")
            return None
    
    def process_all_annotations(self, input_dir: Path) -> List[Dict[str, Any]]:
        """Process all JSON annotation files in a directory."""
        print("🔄 Processing JSON annotations for enhanced database extraction")
        print("="*60)
        
        annotation_files = list(input_dir.glob("*_final_annotation.json"))
        
        if not annotation_files:
            print(f"❌ No annotation files found in {input_dir}")
            return []
        
        print(f"📄 Found {len(annotation_files)} annotation files")
        print()
        
        extracted_data = []
        
        for i, file_path in enumerate(annotation_files, 1):
            print(f"[{i:2d}/{len(annotation_files)}] Processing {file_path.name}")
            
            extracted = self.process_annotation_file(file_path)
            if extracted:
                extracted_data.append(extracted)
                
                # Show progress
                interview_id = extracted['interview_metadata']['interview_id']
                turn_count = len(extracted['turns'])
                priority_count = len(extracted['priorities'])
                print(f"    ✅ {interview_id}: {turn_count} turns, {priority_count} priorities extracted")
        
        print(f"\n📊 EXTRACTION SUMMARY")
        print(f"="*30)
        print(f"Interviews processed: {self.extraction_stats['interviews_processed']}")
        print(f"Participants extracted: {self.extraction_stats['participants_extracted']}")
        print(f"Narrative features: {self.extraction_stats['narrative_features_extracted']}")
        print(f"Total turns: {self.extraction_stats['turns_extracted']}")
        print(f"Total priorities: {self.extraction_stats['priorities_extracted']}")
        print(f"Errors: {len(self.extraction_stats['errors'])}")
        
        if self.extraction_stats['errors']:
            print(f"\n⚠️  Errors encountered:")
            for error in self.extraction_stats['errors']:
                print(f"    {error}")
        
        return extracted_data


def main():
    """Main extraction function."""
    print("🎯 ENHANCED DATA EXTRACTION")
    print("Extracting comprehensive data from JSON annotations")
    print("="*60)
    
    # Initialize extractor
    extractor = EnhancedDataExtractor()
    
    # Process annotations
    input_dir = Path("data/processed/annotations/production")
    extracted_data = extractor.process_all_annotations(input_dir)
    
    if not extracted_data:
        print("❌ No data extracted")
        return False
    
    # Save extracted data for database loading
    output_file = Path("data/processed/extracted_enhanced_data.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'extraction_metadata': {
                'extracted_at': datetime.now().isoformat(),
                'extractor_version': 'enhanced_v1.0',
                'extraction_stats': extractor.extraction_stats
            },
            'extracted_interviews': extracted_data
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Enhanced data saved: {output_file}")
    print(f"✅ Ready for database loading with enhanced schema")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)