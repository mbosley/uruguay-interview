#!/usr/bin/env python3
"""
Load enhanced extracted data into comprehensive database schema.
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from decimal import Decimal

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.connection import get_db
from src.database.models import (
    Interview, Annotation, ParticipantProfile, NarrativeFeatures,
    KeyNarratives, InterviewDynamics, AnalyticalSynthesis, Priority,
    Turn, TurnFunctionalAnalysis, TurnContentAnalysis, TurnEvidenceAnalysis,
    TurnEmotionalAnalysis, TurnUncertaintyTracking, ProcessingAnalytics
)

class EnhancedDatabaseLoader:
    """Load enhanced extracted data into database."""
    
    def __init__(self):
        self.db = get_db()
        self.stats = {
            'interviews_loaded': 0,
            'participants_loaded': 0,
            'narratives_loaded': 0,
            'priorities_loaded': 0,
            'turns_loaded': 0,
            'errors': []
        }
    
    def load_interview_metadata(self, session, data: Dict[str, Any]) -> Interview:
        """Load interview metadata."""
        metadata = data['interview_metadata']
        
        interview = Interview(
            interview_id=metadata['interview_id'],
            date=metadata['date'],
            time="00:00",  # Default time
            location=f"{metadata.get('municipality', '')}, {metadata.get('department', '')}",
            department=metadata.get('department'),
            municipality=metadata.get('municipality'),
            locality_size=metadata.get('locality_size'),
            duration_minutes=metadata.get('duration_minutes'),
            interviewer_ids=metadata.get('interviewer_ids', []),
            interview_context=metadata.get('interview_context'),
            status='completed',
            processed_at=datetime.now()
        )
        
        session.add(interview)
        session.flush()  # Get the ID
        return interview
    
    def load_annotation_metadata(self, session, interview: Interview, data: Dict[str, Any]) -> Annotation:
        """Load annotation metadata."""
        meta = data['annotation_metadata']
        
        annotation = Annotation(
            interview_id=interview.id,
            model_provider=meta.get('model_provider', 'openai'),
            model_name=meta.get('model_name', 'gpt-4.1-nano'),
            temperature=meta.get('temperature', 0.1),
            annotation_approach=meta.get('annotation_approach', 'multipass_comprehensive'),
            overall_confidence=meta.get('overall_confidence'),
            uncertainty_flags=meta.get('uncertainty_flags', []),
            uncertainty_narrative=meta.get('uncertainty_narrative'),
            turn_coverage_percentage=meta.get('turn_coverage_percentage'),
            analyzed_turns=meta.get('analyzed_turns'),
            expected_turns=meta.get('expected_turns'),
            all_turns_analyzed=meta.get('all_turns_analyzed', False),
            total_api_calls=meta.get('total_api_calls'),
            api_call_breakdown=meta.get('api_call_breakdown', []),
            processing_time=meta.get('processing_time'),
            total_cost=Decimal(str(meta.get('total_cost', 0))),
            json_content=meta.get('json_content')
        )
        
        session.add(annotation)
        session.flush()
        return annotation
    
    def load_participant_profile(self, session, interview: Interview, data: Dict[str, Any]):
        """Load participant profile."""
        profile_data = data['participant_profile']
        
        profile = ParticipantProfile(
            interview_id=interview.id,
            age_range=profile_data.get('age_range'),
            gender=profile_data.get('gender'),
            occupation_sector=profile_data.get('occupation_sector'),
            organizational_affiliation=profile_data.get('organizational_affiliation'),
            self_described_political_stance=profile_data.get('self_described_political_stance'),
            profile_confidence=profile_data.get('profile_confidence'),
            profile_notes=profile_data.get('profile_notes')
        )
        
        session.add(profile)
    
    def load_narrative_features(self, session, interview: Interview, data: Dict[str, Any]):
        """Load narrative features."""
        narrative_data = data['narrative_features']
        
        narrative = NarrativeFeatures(
            interview_id=interview.id,
            dominant_frame=narrative_data.get('dominant_frame'),
            frame_narrative=narrative_data.get('frame_narrative'),
            temporal_orientation=narrative_data.get('temporal_orientation'),
            temporal_narrative=narrative_data.get('temporal_narrative'),
            government_responsibility=narrative_data.get('government_responsibility'),
            individual_responsibility=narrative_data.get('individual_responsibility'),
            structural_factors=narrative_data.get('structural_factors'),
            agency_narrative=narrative_data.get('agency_narrative'),
            solution_orientation=narrative_data.get('solution_orientation'),
            solution_narrative=narrative_data.get('solution_narrative'),
            cultural_patterns_identified=narrative_data.get('cultural_patterns_identified', []),
            narrative_confidence=narrative_data.get('narrative_confidence')
        )
        
        session.add(narrative)
    
    def load_key_narratives(self, session, interview: Interview, data: Dict[str, Any]):
        """Load key narratives."""
        narratives_data = data['key_narratives']
        
        key_narratives = KeyNarratives(
            interview_id=interview.id,
            identity_narrative=narratives_data.get('identity_narrative'),
            problem_narrative=narratives_data.get('problem_narrative'),
            hope_narrative=narratives_data.get('hope_narrative'),
            memorable_quotes=narratives_data.get('memorable_quotes', []),
            rhetorical_strategies=narratives_data.get('rhetorical_strategies', []),
            narrative_confidence=narratives_data.get('narrative_confidence')
        )
        
        session.add(key_narratives)
    
    def load_interview_dynamics(self, session, interview: Interview, data: Dict[str, Any]):
        """Load interview dynamics."""
        dynamics_data = data['interview_dynamics']
        
        dynamics = InterviewDynamics(
            interview_id=interview.id,
            rapport=dynamics_data.get('rapport'),
            rapport_narrative=dynamics_data.get('rapport_narrative'),
            participant_engagement=dynamics_data.get('participant_engagement'),
            engagement_narrative=dynamics_data.get('engagement_narrative'),
            coherence=dynamics_data.get('coherence'),
            coherence_narrative=dynamics_data.get('coherence_narrative'),
            interviewer_effects=dynamics_data.get('interviewer_effects'),
            dynamics_confidence=dynamics_data.get('dynamics_confidence')
        )
        
        session.add(dynamics)
    
    def load_analytical_synthesis(self, session, interview: Interview, data: Dict[str, Any]):
        """Load analytical synthesis."""
        synthesis_data = data['analytical_synthesis']
        
        synthesis = AnalyticalSynthesis(
            interview_id=interview.id,
            tensions_contradictions=synthesis_data.get('tensions_contradictions'),
            silences_omissions=synthesis_data.get('silences_omissions'),
            cultural_context_notes=synthesis_data.get('cultural_context_notes'),
            connections_to_broader_themes=synthesis_data.get('connections_to_broader_themes'),
            analytical_confidence=synthesis_data.get('analytical_confidence')
        )
        
        session.add(synthesis)
    
    def load_priorities(self, session, interview: Interview, data: Dict[str, Any]):
        """Load priorities."""
        for priority_data in data['priorities']:
            priority = Priority(
                interview_id=interview.id,
                scope=priority_data.get('scope'),
                rank=priority_data.get('rank'),
                theme=priority_data.get('theme'),
                specific_issues=priority_data.get('specific_issues', []),
                narrative_elaboration=priority_data.get('narrative_elaboration'),
                emotional_intensity=priority_data.get('emotional_intensity'),
                supporting_quotes=priority_data.get('supporting_quotes', []),
                confidence=priority_data.get('confidence'),
                reasoning=priority_data.get('reasoning')
            )
            
            session.add(priority)
            self.stats['priorities_loaded'] += 1
    
    def load_turns(self, session, interview: Interview, annotation: Annotation, data: Dict[str, Any]):
        """Load turns with comprehensive analysis."""
        for turn_data in data['turns']:
            # Create base turn
            turn = Turn(
                interview_id=interview.id,
                annotation_id=annotation.id,
                turn_id=turn_data.get('turn_id'),
                speaker='participant',  # Default
                text='',  # We don't have original text in extracted data
                significance='medium',  # Default
                turn_significance=turn_data.get('turn_significance')
            )
            
            session.add(turn)
            session.flush()  # Get turn ID
            
            # Load functional analysis
            func_data = turn_data.get('functional_analysis', {})
            func_analysis = TurnFunctionalAnalysis(
                turn_id=turn.id,
                reasoning=func_data.get('reasoning'),
                primary_function=func_data.get('primary_function'),
                secondary_functions=func_data.get('secondary_functions', []),
                function_confidence=func_data.get('function_confidence')
            )
            session.add(func_analysis)
            
            # Load content analysis
            content_data = turn_data.get('content_analysis', {})
            content_analysis = TurnContentAnalysis(
                turn_id=turn.id,
                reasoning=content_data.get('reasoning'),
                topics=content_data.get('topics', []),
                geographic_scope=content_data.get('geographic_scope', []),
                temporal_reference=content_data.get('temporal_reference'),
                topic_narrative=content_data.get('topic_narrative'),
                content_confidence=content_data.get('content_confidence')
            )
            session.add(content_analysis)
            
            # Load evidence analysis
            evidence_data = turn_data.get('evidence_analysis', {})
            evidence_analysis = TurnEvidenceAnalysis(
                turn_id=turn.id,
                reasoning=evidence_data.get('reasoning'),
                evidence_type=evidence_data.get('evidence_type'),
                evidence_narrative=evidence_data.get('evidence_narrative'),
                specificity=evidence_data.get('specificity'),
                evidence_confidence=evidence_data.get('evidence_confidence')
            )
            session.add(evidence_analysis)
            
            # Load emotional analysis
            emotional_data = turn_data.get('emotional_analysis', {})
            emotional_analysis = TurnEmotionalAnalysis(
                turn_id=turn.id,
                reasoning=emotional_data.get('reasoning'),
                emotional_valence=emotional_data.get('emotional_valence'),
                emotional_intensity=emotional_data.get('emotional_intensity'),
                specific_emotions=emotional_data.get('specific_emotions', []),
                emotional_narrative=emotional_data.get('emotional_narrative'),
                certainty=emotional_data.get('certainty'),
                rhetorical_features=emotional_data.get('rhetorical_features')
            )
            session.add(emotional_analysis)
            
            # Load uncertainty tracking
            uncertainty_data = turn_data.get('uncertainty_tracking', {})
            uncertainty_tracking = TurnUncertaintyTracking(
                turn_id=turn.id,
                coding_confidence=uncertainty_data.get('coding_confidence'),
                ambiguous_aspects=uncertainty_data.get('ambiguous_aspects', []),
                edge_case_flag=uncertainty_data.get('edge_case_flag', False),
                alternative_interpretations=uncertainty_data.get('alternative_interpretations', []),
                resolution_strategy=uncertainty_data.get('resolution_strategy'),
                annotator_notes=uncertainty_data.get('annotator_notes')
            )
            session.add(uncertainty_tracking)
            
            self.stats['turns_loaded'] += 1
    
    def load_processing_analytics(self, session, interview: Interview, data: Dict[str, Any]):
        """Load processing analytics."""
        analytics_data = data['processing_analytics']
        
        analytics = ProcessingAnalytics(
            interview_id=interview.id,
            model_name=analytics_data.get('model_name'),
            annotation_approach=analytics_data.get('annotation_approach'),
            timeout_used=analytics_data.get('timeout_used'),
            total_api_calls=analytics_data.get('total_api_calls'),
            processing_time_seconds=analytics_data.get('processing_time_seconds'),
            total_cost=Decimal(str(analytics_data.get('total_cost', 0))),
            turn_coverage_percentage=analytics_data.get('turn_coverage_percentage'),
            overall_confidence=analytics_data.get('overall_confidence'),
            retry_count=analytics_data.get('retry_count', 0),
            api_call_breakdown=analytics_data.get('api_call_breakdown', []),
            pipeline_version=analytics_data.get('pipeline_version')
        )
        
        session.add(analytics)
    
    def load_interview_data(self, session, interview_data: Dict[str, Any]):
        """Load all data for a single interview."""
        try:
            # 1. Load interview metadata
            interview = self.load_interview_metadata(session, interview_data)
            
            # 2. Load annotation metadata
            annotation = self.load_annotation_metadata(session, interview, interview_data)
            
            # 3. Load participant profile
            self.load_participant_profile(session, interview, interview_data)
            
            # 4. Load narrative features
            self.load_narrative_features(session, interview, interview_data)
            
            # 5. Load key narratives
            self.load_key_narratives(session, interview, interview_data)
            
            # 6. Load interview dynamics
            self.load_interview_dynamics(session, interview, interview_data)
            
            # 7. Load analytical synthesis
            self.load_analytical_synthesis(session, interview, interview_data)
            
            # 8. Load priorities
            self.load_priorities(session, interview, interview_data)
            
            # 9. Load turns with analysis
            self.load_turns(session, interview, annotation, interview_data)
            
            # 10. Load processing analytics
            self.load_processing_analytics(session, interview, interview_data)
            
            self.stats['interviews_loaded'] += 1
            self.stats['participants_loaded'] += 1
            self.stats['narratives_loaded'] += 1
            
            print(f"✅ Loaded interview {interview.interview_id}")
            
        except Exception as e:
            error_msg = f"Error loading interview: {str(e)}"
            self.stats['errors'].append(error_msg)
            print(f"❌ {error_msg}")
            raise
    
    def load_all_data(self, data_file: Path):
        """Load all extracted data into database."""
        print("🏗️  LOADING ENHANCED DATA INTO DATABASE")
        print("=" * 50)
        
        # Load extracted data
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        interviews = data['extracted_interviews']
        print(f"📄 Found {len(interviews)} interviews to load")
        
        # Initialize database
        print("🔧 Initializing database...")
        self.db.create_tables()
        
        # Load data
        with self.db.get_session() as session:
            for i, interview_data in enumerate(interviews, 1):
                print(f"[{i:2d}/{len(interviews)}] Loading interview {interview_data['interview_metadata']['interview_id']}")
                self.load_interview_data(session, interview_data)
        
        print(f"\n📊 DATABASE LOADING SUMMARY")
        print("=" * 30)
        print(f"Interviews loaded: {self.stats['interviews_loaded']}")
        print(f"Participants loaded: {self.stats['participants_loaded']}")
        print(f"Narratives loaded: {self.stats['narratives_loaded']}")
        print(f"Priorities loaded: {self.stats['priorities_loaded']}")
        print(f"Turns loaded: {self.stats['turns_loaded']}")
        print(f"Errors: {len(self.stats['errors'])}")
        
        if self.stats['errors']:
            print(f"\n⚠️  Errors encountered:")
            for error in self.stats['errors']:
                print(f"    {error}")
        
        return len(self.stats['errors']) == 0


def main():
    """Main loading function."""
    print("🎯 ENHANCED DATABASE LOADING")
    print("Loading comprehensive data into research-grade schema")
    print("=" * 60)
    
    # Initialize loader
    loader = EnhancedDatabaseLoader()
    
    # Load data
    data_file = Path("data/processed/extracted_enhanced_data.json")
    if not data_file.exists():
        print(f"❌ Data file not found: {data_file}")
        return False
    
    success = loader.load_all_data(data_file)
    
    if success:
        print(f"\n✅ Enhanced database loading completed successfully!")
        print(f"🔬 Research-grade schema now populated with comprehensive data")
    else:
        print(f"\n❌ Database loading failed")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)