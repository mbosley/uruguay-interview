#!/usr/bin/env python3
"""Test OpenAI JSON mode annotation with actual API call."""
import sys
from pathlib import Path
import json

# Add project root to path
sys.path.insert(0, str(Path.cwd()))

from src.pipeline.annotation.json_mode_annotator import JSONModeAnnotator
from src.pipeline.ingestion.document_processor import DocumentProcessor

def test_json_mode():
    """Test JSON mode annotation with real API call."""
    
    # Find test interview
    txt_dir = Path("data/processed/interviews_txt")
    txt_files = list(txt_dir.glob("*.txt"))
    
    if not txt_files:
        print("❌ No interview files found")
        return
    
    # Use smallest file for testing
    test_file = min(txt_files, key=lambda f: f.stat().st_size)
    
    # Process interview
    processor = DocumentProcessor()
    interview = processor.process_interview(test_file)
    
    print("🎯 OPENAI JSON MODE ANNOTATION TEST")
    print("=" * 50)
    print(f"Interview: {interview.id}")
    print(f"Text length: {len(interview.text):,} characters")
    print(f"Word count: {len(interview.text.split()):,} words")
    print(f"Estimated cost: ~$0.003")
    print()
    
    # Create annotator
    annotator = JSONModeAnnotator(model_name="gpt-4o-mini", temperature=0.1)
    
    try:
        print("🤖 Making JSON mode API call...")
        annotation_data, metadata = annotator.annotate_interview(interview)
        
        print("✅ JSON mode annotation successful!")
        print()
        
        # Display results
        print("📊 ACTUAL ANNOTATION RESULTS:")
        print("=" * 40)
        
        # Interview metadata
        meta = annotation_data["interview_metadata"]
        print(f"Interview ID: {meta['interview_id']}")
        print(f"Location: {meta['municipality']}, {meta['department']}")
        print(f"Locality size: {meta['locality_size']}")
        if meta.get('duration_minutes'):
            print(f"Duration: {meta['duration_minutes']} minutes")
        print()
        
        # Participant profile
        profile = annotation_data["participant_profile"]
        print("👤 PARTICIPANT PROFILE:")
        print(f"  Age: {profile['age_range']}")
        print(f"  Gender: {profile['gender']}")
        print(f"  Occupation: {profile['occupation_sector']}")
        if profile.get('organizational_affiliation'):
            print(f"  Organization: {profile['organizational_affiliation']}")
        if profile.get('political_stance'):
            print(f"  Political stance: {profile['political_stance']}")
        print()
        
        # National priorities
        print("🎯 NATIONAL PRIORITIES:")
        for priority in annotation_data["national_priorities"]:
            print(f"  {priority['rank']}. {priority['theme']}")
            print(f"     Issues: {', '.join(priority['specific_issues'])}")
            narrative = priority['narrative_elaboration']
            narrative_preview = narrative[:100] + "..." if len(narrative) > 100 else narrative
            print(f"     Narrative: {narrative_preview}")
            print()
        
        # Local priorities
        print("🏠 LOCAL PRIORITIES:")
        for priority in annotation_data["local_priorities"]:
            print(f"  {priority['rank']}. {priority['theme']}")
            print(f"     Issues: {', '.join(priority['specific_issues'])}")
            narrative = priority['narrative_elaboration']
            narrative_preview = narrative[:100] + "..." if len(narrative) > 100 else narrative
            print(f"     Narrative: {narrative_preview}")
            print()
        
        # Conversation turns sample
        turns = annotation_data["conversation_turns"]
        print(f"🔄 CONVERSATION TURNS ({len(turns)} total):")
        print("Sample of first 3 turns:")
        
        for turn in turns[:3]:
            print(f"\n  Turn {turn['turn_id']} ({turn['speaker']}):")
            text_preview = turn['text'][:80] + "..." if len(turn['text']) > 80 else turn['text']
            print(f"    Text: \"{text_preview}\"")
            print(f"    Function: {turn['functional_analysis']['primary_function']}")
            print(f"    Topics: {', '.join(turn['content_analysis']['topics'])}")
            print(f"    Evidence: {turn['evidence_analysis']['evidence_type']}")
            print(f"    Emotion: {turn['stance_analysis']['emotional_valence']}")
            
            # Show reasoning sample
            reasoning = turn['functional_analysis']['reasoning']
            reasoning_preview = reasoning[:100] + "..." if len(reasoning) > 100 else reasoning
            print(f"    Reasoning: {reasoning_preview}")
            print(f"    Confidence: {turn['confidence']}")
        
        if len(turns) > 3:
            print(f"\n  ... and {len(turns) - 3} more turns with complete annotations")
        print()
        
        # Narrative features
        narrative = annotation_data.get("narrative_features", {})
        if narrative:
            print("📖 NARRATIVE FEATURES:")
            print(f"  Dominant frame: {narrative.get('dominant_frame', 'N/A')}")
            print(f"  Temporal orientation: {narrative.get('temporal_orientation', 'N/A')}")
            print(f"  Solution orientation: {narrative.get('solution_orientation', 'N/A')}")
            print()
        
        # Key narratives
        key_narratives = annotation_data.get("key_narratives", {})
        if key_narratives and key_narratives.get("memorable_quotes"):
            print("🗣️ MEMORABLE QUOTES:")
            for i, quote in enumerate(key_narratives["memorable_quotes"][:3], 1):
                print(f"  {i}. \"{quote}\"")
            print()
        
        # Overall assessment
        assessment = annotation_data["overall_assessment"]
        print("🤔 OVERALL ASSESSMENT:")
        print(f"  Confidence: {assessment['confidence']:.2f}")
        print(f"  Uncertainty flags: {', '.join(assessment['uncertainty_flags'])}")
        print()
        
        # Processing metadata
        print("⚙️ PROCESSING METADATA:")
        for key, value in metadata.items():
            print(f"  {key}: {value}")
        print()
        
        # Save actual result
        output_file = "actual_json_mode_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(annotation_data, f, indent=2, ensure_ascii=False)
        
        print("📁 RESULT SAVED:")
        print(f"  File: {output_file}")
        print(f"  Size: {Path(output_file).stat().st_size:,} bytes")
        print()
        
        print("✅ JSON MODE SUCCESS:")
        print(f"  ✅ {len(turns)} conversation turns annotated")
        print(f"  ✅ Complete priority analysis with narratives")
        print(f"  ✅ Chain-of-thought reasoning for all decisions")
        print(f"  ✅ Structured JSON output validated")
        print(f"  ✅ Processing time: {metadata['processing_time']:.1f}s")
        print(f"  ✅ Actual cost: ${metadata['estimated_cost']:.4f}")
        
        # Calculate total reasoning content
        total_reasoning = sum(
            len(turn['functional_analysis']['reasoning']) +
            len(turn['content_analysis']['reasoning']) +
            len(turn['evidence_analysis']['reasoning']) +
            len(turn['stance_analysis']['reasoning'])
            for turn in turns
        )
        
        print(f"  ✅ {total_reasoning:,} characters of reasoning generated")
        print(f"  ✅ Average {total_reasoning // len(turns):,} characters per turn")
        
    except Exception as e:
        print(f"❌ JSON mode annotation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_json_mode()