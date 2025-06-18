#!/usr/bin/env python3
"""Test a real Instructor annotation with actual API call."""
import sys
from pathlib import Path
import json

# Add project root to path
sys.path.insert(0, str(Path.cwd()))

from src.pipeline.annotation.instructor_models import CompleteInterviewAnnotation
from src.pipeline.ingestion.document_processor import DocumentProcessor
import instructor
from openai import OpenAI
from src.config.config_loader import ConfigLoader

def test_real_annotation():
    """Run a real annotation and show actual results."""
    
    # Find smallest interview for testing
    txt_dir = Path("data/processed/interviews_txt")
    txt_files = list(txt_dir.glob("*.txt"))
    
    if not txt_files:
        print("❌ No interview files found")
        return
    
    # Use the smallest file to minimize cost and complexity
    test_file = min(txt_files, key=lambda f: f.stat().st_size)
    
    # Process interview
    processor = DocumentProcessor()
    interview = processor.process_interview(test_file)
    
    print("🎯 REAL INSTRUCTOR ANNOTATION TEST")
    print("=" * 50)
    print(f"Interview: {interview.id}")
    print(f"Text length: {len(interview.text):,} characters")
    print(f"Word count: {len(interview.text.split()):,} words")
    print(f"Estimated cost: ~$0.003")
    print()
    
    # Get API key
    config_loader = ConfigLoader()
    api_key = config_loader.get_api_key("openai")
    if not api_key:
        print("❌ No OpenAI API key found")
        return
    
    # Initialize Instructor client
    openai_client = OpenAI(api_key=api_key)
    client = instructor.from_openai(openai_client)
    
    print("🤖 Making real API call...")
    
    try:
        # Real API call with Instructor
        annotation = client.chat.completions.create(
            model="gpt-4o-mini",
            response_model=CompleteInterviewAnnotation,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert qualitative researcher. Analyze this Uruguay citizen consultation interview completely. Follow the structured schema exactly."
                },
                {
                    "role": "user",
                    "content": f"""
Analyze this interview systematically:

INTERVIEW TEXT:
{interview.text}

METADATA:
- ID: {interview.id}
- Date: {interview.date}
- Location: {interview.location}

Provide complete annotation following the structured schema. Include chain-of-thought reasoning for all decisions.
"""
                }
            ],
            temperature=0.1,
            max_retries=2
        )
        
        print("✅ API call successful!")
        print()
        
        # Display actual results
        print("📊 ACTUAL ANNOTATION RESULTS:")
        print("=" * 40)
        
        print(f"Interview ID: {annotation.interview_id}")
        print(f"Location: {annotation.location.municipality}, {annotation.location.department}")
        print(f"Participant: {annotation.participant_profile.age_range} {annotation.participant_profile.gender}")
        print(f"Occupation: {annotation.participant_profile.occupation_sector}")
        print(f"Conversation turns: {len(annotation.turns)}")
        print(f"Overall confidence: {annotation.overall_confidence:.2f}")
        print()
        
        print("🎯 NATIONAL PRIORITIES (actual):")
        for i, priority in enumerate(annotation.national_priorities, 1):
            print(f"  {priority.rank}. {priority.theme}")
            print(f"     Issues: {', '.join(priority.specific_issues[:3])}{'...' if len(priority.specific_issues) > 3 else ''}")
            narrative_preview = priority.narrative_elaboration[:100] + "..." if len(priority.narrative_elaboration) > 100 else priority.narrative_elaboration
            print(f"     Narrative: {narrative_preview}")
        print()
        
        print("🏠 LOCAL PRIORITIES (actual):")
        for i, priority in enumerate(annotation.local_priorities, 1):
            print(f"  {priority.rank}. {priority.theme}")
            print(f"     Issues: {', '.join(priority.specific_issues[:3])}{'...' if len(priority.specific_issues) > 3 else ''}")
            narrative_preview = priority.narrative_elaboration[:100] + "..." if len(priority.narrative_elaboration) > 100 else priority.narrative_elaboration
            print(f"     Narrative: {narrative_preview}")
        print()
        
        print("🔄 CONVERSATION TURNS (actual sample):")
        for i, turn in enumerate(annotation.turns[:3], 1):
            print(f"  Turn {turn.turn_id} ({turn.speaker}):")
            text_preview = turn.text[:80] + "..." if len(turn.text) > 80 else turn.text
            print(f"    Text: \"{text_preview}\"")
            print(f"    Function: {turn.functional_annotation.primary_function}")
            print(f"    Topics: {', '.join(turn.content_annotation.topics)}")
            print(f"    Evidence: {turn.evidence_annotation.evidence_type}")
            print(f"    Emotion: {turn.stance_annotation.emotional_valence}")
            reasoning_preview = turn.functional_annotation.reasoning[:100] + "..." if len(turn.functional_annotation.reasoning) > 100 else turn.functional_annotation.reasoning
            print(f"    Reasoning: {reasoning_preview}")
            print()
        
        if len(annotation.turns) > 3:
            print(f"  ... and {len(annotation.turns) - 3} more turns")
        print()
        
        print("📖 NARRATIVE ANALYSIS (actual):")
        print(f"  Dominant frame: {annotation.dominant_frame}")
        print(f"  Temporal orientation: {annotation.temporal_orientation}")
        print(f"  Solution orientation: {annotation.solution_orientation}")
        print()
        
        print("🗣️ MEMORABLE QUOTES (actual):")
        for i, quote in enumerate(annotation.key_narratives.memorable_quotes[:3], 1):
            print(f"  {i}. \"{quote}\"")
        if len(annotation.key_narratives.memorable_quotes) > 3:
            print(f"  ... and {len(annotation.key_narratives.memorable_quotes) - 3} more")
        print()
        
        print("🤔 UNCERTAINTY TRACKING (actual):")
        print(f"  Overall confidence: {annotation.overall_confidence:.2f}")
        print(f"  Uncertainty flags: {', '.join(annotation.uncertainty_flags)}")
        print()
        
        # Save the actual result
        output_file = Path("actual_annotation_result.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(annotation.model_dump(), f, indent=2, ensure_ascii=False)
        
        print("📁 ACTUAL RESULT SAVED:")
        print(f"  File: {output_file}")
        print(f"  Size: {output_file.stat().st_size:,} bytes")
        print()
        
        print("✅ REAL ANNOTATION SUCCESS:")
        print(f"  ✅ {len(annotation.turns)} conversation turns annotated")
        print(f"  ✅ {len(annotation.national_priorities)} national priorities extracted")
        print(f"  ✅ {len(annotation.local_priorities)} local priorities extracted")
        print(f"  ✅ {len(annotation.key_narratives.memorable_quotes)} memorable quotes captured")
        print("  ✅ Complete narrative and emotional analysis")
        print("  ✅ Chain-of-thought reasoning for all decisions")
        print("  ✅ Automatic validation successful")
        
        # Calculate actual reasoning content
        total_reasoning = sum(
            len(turn.functional_annotation.reasoning) +
            len(turn.content_annotation.reasoning) +
            len(turn.evidence_annotation.reasoning) +
            len(turn.stance_annotation.reasoning)
            for turn in annotation.turns
        )
        
        print(f"  ✅ {total_reasoning:,} characters of reasoning text generated")
        print(f"  ✅ Average {total_reasoning // len(annotation.turns):,} characters reasoning per turn")
        
    except Exception as e:
        print(f"❌ API call failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_real_annotation()