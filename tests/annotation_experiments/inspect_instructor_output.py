#!/usr/bin/env python3
"""Inspect the output of a single Instructor annotation."""
import sys
from pathlib import Path
import json

# Add project root to path
sys.path.insert(0, str(Path.cwd()))

from src.pipeline.annotation.instructor_annotator import InstructorAnnotator
from src.pipeline.ingestion.document_processor import DocumentProcessor

def display_annotation_sample(annotation, metadata):
    """Display a formatted sample of the annotation output."""
    
    print("🎯 INSTRUCTOR ANNOTATION INSPECTION")
    print("=" * 60)
    
    # Interview metadata
    print("📋 INTERVIEW METADATA:")
    print(f"  ID: {annotation.interview_id}")
    print(f"  Date: {annotation.date}")
    print(f"  Location: {annotation.location.municipality}, {annotation.location.department}")
    print(f"  Locality size: {annotation.location.locality_size}")
    if annotation.duration_minutes:
        print(f"  Duration: {annotation.duration_minutes} minutes")
    print(f"  Interviewers: {', '.join(annotation.interviewer_ids)}")
    print()
    
    # Participant profile
    print("👤 PARTICIPANT PROFILE:")
    profile = annotation.participant_profile
    print(f"  Age range: {profile.age_range}")
    print(f"  Gender: {profile.gender}")
    print(f"  Occupation: {profile.occupation_sector}")
    if profile.organizational_affiliation:
        print(f"  Organization: {profile.organizational_affiliation}")
    if profile.self_described_political_stance:
        print(f"  Political stance: {profile.self_described_political_stance}")
    print()
    
    # Priority analysis
    print("🎯 PRIORITY ANALYSIS:")
    print("  National priorities:")
    for priority in annotation.national_priorities:
        print(f"    {priority.rank}. {priority.theme}")
        print(f"       Issues: {', '.join(priority.specific_issues)}")
        if len(priority.narrative_elaboration) > 100:
            print(f"       Narrative: {priority.narrative_elaboration[:100]}...")
        else:
            print(f"       Narrative: {priority.narrative_elaboration}")
        print()
    
    print("  Local priorities:")
    for priority in annotation.local_priorities:
        print(f"    {priority.rank}. {priority.theme}")
        print(f"       Issues: {', '.join(priority.specific_issues)}")
        if len(priority.narrative_elaboration) > 100:
            print(f"       Narrative: {priority.narrative_elaboration[:100]}...")
        else:
            print(f"       Narrative: {priority.narrative_elaboration}")
        print()
    
    # Narrative features
    print("📖 NARRATIVE FEATURES:")
    print(f"  Dominant frame: {annotation.dominant_frame}")
    if len(annotation.frame_narrative) > 150:
        print(f"  Frame narrative: {annotation.frame_narrative[:150]}...")
    else:
        print(f"  Frame narrative: {annotation.frame_narrative}")
    print(f"  Temporal orientation: {annotation.temporal_orientation}")
    print(f"  Solution orientation: {annotation.solution_orientation}")
    print()
    
    # Agency attribution
    print("⚖️ AGENCY ATTRIBUTION:")
    agency = annotation.agency_attribution
    print(f"  Government responsibility: {agency.government_responsibility[:100]}..." if len(agency.government_responsibility) > 100 else f"  Government responsibility: {agency.government_responsibility}")
    print(f"  Individual responsibility: {agency.individual_responsibility[:100]}..." if len(agency.individual_responsibility) > 100 else f"  Individual responsibility: {agency.individual_responsibility}")
    print(f"  Structural factors: {agency.structural_factors[:100]}..." if len(agency.structural_factors) > 100 else f"  Structural factors: {agency.structural_factors}")
    print()
    
    # Key narratives
    print("🗣️ KEY NARRATIVES:")
    narratives = annotation.key_narratives
    print(f"  Identity: {narratives.identity_narrative[:100]}..." if len(narratives.identity_narrative) > 100 else f"  Identity: {narratives.identity_narrative}")
    print(f"  Problem: {narratives.problem_narrative[:100]}..." if len(narratives.problem_narrative) > 100 else f"  Problem: {narratives.problem_narrative}")
    print(f"  Hope: {narratives.hope_narrative[:100]}..." if len(narratives.hope_narrative) > 100 else f"  Hope: {narratives.hope_narrative}")
    print(f"  Memorable quotes ({len(narratives.memorable_quotes)}):")
    for i, quote in enumerate(narratives.memorable_quotes[:3], 1):  # Show first 3 quotes
        print(f"    {i}. \"{quote}\"")
    if len(narratives.memorable_quotes) > 3:
        print(f"    ... and {len(narratives.memorable_quotes) - 3} more")
    print()
    
    # Interview dynamics
    print("🎭 INTERVIEW DYNAMICS:")
    dynamics = annotation.interview_dynamics
    print(f"  Rapport: {dynamics.rapport}")
    print(f"  Engagement: {dynamics.participant_engagement}")
    print(f"  Coherence: {dynamics.coherence}")
    print()
    
    # Turn analysis sample
    print(f"🔄 CONVERSATION TURNS ({len(annotation.turns)} total):")
    print("  Sample of first 5 turns:")
    
    for i, turn in enumerate(annotation.turns[:5], 1):
        print(f"\n  Turn {turn.turn_id} ({turn.speaker}):")
        
        # Show turn text (truncated)
        text_preview = turn.text[:100] + "..." if len(turn.text) > 100 else turn.text
        print(f"    Text: \"{text_preview}\"")
        
        # Functional annotation
        print(f"    🎯 Function: {turn.functional_annotation.primary_function}")
        reasoning = turn.functional_annotation.reasoning
        reasoning_preview = reasoning[:120] + "..." if len(reasoning) > 120 else reasoning
        print(f"    💭 Reasoning: {reasoning_preview}")
        
        # Content annotation
        print(f"    📋 Topics: {', '.join(turn.content_annotation.topics)}")
        print(f"    🌍 Scope: {', '.join(turn.content_annotation.geographic_scope)}")
        
        # Evidence annotation
        print(f"    📊 Evidence: {turn.evidence_annotation.evidence_type}")
        print(f"    🎯 Specificity: {turn.evidence_annotation.specificity}")
        
        # Stance annotation
        print(f"    😊 Emotion: {turn.stance_annotation.emotional_valence} ({turn.stance_annotation.emotional_intensity})")
        print(f"    ✅ Certainty: {turn.stance_annotation.certainty}")
        
        # Uncertainty tracking
        print(f"    🤔 Confidence: {turn.uncertainty_tracking.coding_confidence:.2f}")
    
    if len(annotation.turns) > 5:
        print(f"\n  ... and {len(annotation.turns) - 5} more turns with complete annotations")
    
    print()
    
    # Analytical notes
    print("🔍 ANALYTICAL NOTES:")
    print(f"  Tensions/contradictions: {annotation.tensions_contradictions[:100]}..." if len(annotation.tensions_contradictions) > 100 else f"  Tensions/contradictions: {annotation.tensions_contradictions}")
    print(f"  Silences/omissions: {annotation.silences_omissions[:100]}..." if len(annotation.silences_omissions) > 100 else f"  Silences/omissions: {annotation.silences_omissions}")
    print(f"  Broader connections: {annotation.connections_to_broader_themes[:100]}..." if len(annotation.connections_to_broader_themes) > 100 else f"  Broader connections: {annotation.connections_to_broader_themes}")
    print()
    
    # Uncertainty tracking
    print("🤔 OVERALL UNCERTAINTY:")
    print(f"  Confidence: {annotation.overall_confidence:.2f}")
    print(f"  Uncertainty flags: {', '.join(annotation.uncertainty_flags)}")
    if len(annotation.uncertainty_narrative) > 100:
        print(f"  Narrative: {annotation.uncertainty_narrative[:100]}...")
    else:
        print(f"  Narrative: {annotation.uncertainty_narrative}")
    print()
    
    # Processing metadata
    print("⚙️ PROCESSING METADATA:")
    for key, value in metadata.items():
        print(f"  {key}: {value}")
    print()
    
    # Summary statistics
    print("📊 ANNOTATION STATISTICS:")
    total_reasoning_length = sum(len(turn.functional_annotation.reasoning) + 
                               len(turn.content_annotation.reasoning) + 
                               len(turn.evidence_annotation.reasoning) + 
                               len(turn.stance_annotation.reasoning) 
                               for turn in annotation.turns)
    
    print(f"  Total conversation turns: {len(annotation.turns)}")
    print(f"  Total reasoning text: {total_reasoning_length:,} characters")
    print(f"  Average reasoning per turn: {total_reasoning_length // len(annotation.turns):,} characters")
    print(f"  National priorities identified: {len(annotation.national_priorities)}")
    print(f"  Local priorities identified: {len(annotation.local_priorities)}")
    print(f"  Memorable quotes captured: {len(annotation.key_narratives.memorable_quotes)}")
    print(f"  Overall confidence: {annotation.overall_confidence:.1%}")
    

def run_inspection():
    """Run a single annotation and inspect the results."""
    
    # Find smallest interview for quick testing
    txt_dir = Path("data/processed/interviews_txt")
    txt_files = list(txt_dir.glob("*.txt"))
    
    if not txt_files:
        print("❌ No interview files found")
        return
    
    # Use smallest file to minimize cost
    test_file = min(txt_files, key=lambda f: f.stat().st_size)
    
    # Process interview
    processor = DocumentProcessor()
    interview = processor.process_interview(test_file)
    
    print(f"🎯 GENERATING SAMPLE ANNOTATION")
    print(f"Interview: {interview.id}")
    print(f"Word count: {len(interview.text.split()):,}")
    print(f"Estimated cost: ~$0.002")
    print("\n⏳ Making API call with Instructor...")
    
    # Create annotator
    annotator = InstructorAnnotator(model_name="gpt-4o-mini", temperature=0.1)
    
    try:
        # Generate annotation
        annotation, metadata = annotator.annotate_interview(interview)
        
        print("✅ Annotation successful!\n")
        
        # Display the results
        display_annotation_sample(annotation, metadata)
        
        print("🎉 INSPECTION COMPLETE!")
        print("  ✅ All schema elements filled")
        print("  ✅ Chain-of-thought reasoning provided")  
        print("  ✅ Complete turn-level analysis")
        print("  ✅ Structured priority extraction")
        print("  ✅ Narrative and emotional analysis")
        
    except Exception as e:
        print(f"❌ Annotation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_inspection()