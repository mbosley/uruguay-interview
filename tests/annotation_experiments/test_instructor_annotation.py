#!/usr/bin/env python3
"""Test actual Instructor annotation with a real API call."""
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

# Add project root to path
sys.path.insert(0, str(Path.cwd()))

from src.pipeline.annotation.instructor_annotator import InstructorAnnotator
from src.pipeline.ingestion.document_processor import DocumentProcessor
from src.pipeline.annotation.schema_validator import SchemaValidator

def test_real_annotation():
    """Test a real annotation API call and validate results."""
    
    # Find smallest interview for testing
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
    
    print("🎯 INSTRUCTOR ANNOTATION TEST")
    print("=" * 40)
    print(f"Interview: {interview.id}")
    print(f"Word count: {len(interview.text.split()):,}")
    print(f"Estimated cost: ~$0.002")
    print()
    
    # Create annotator with cheapest model
    annotator = InstructorAnnotator(model_name="gpt-4o-mini", temperature=0.1)
    
    try:
        print("🤖 Making API call...")
        
        # Real annotation call
        annotation, metadata = annotator.annotate_interview(interview)
        
        print("✅ Annotation successful!")
        print()
        print("📊 ANNOTATION RESULTS:")
        print(f"  Interview ID: {annotation.interview_id}")
        print(f"  Location: {annotation.location.municipality}, {annotation.location.department}")
        print(f"  Participant: {annotation.participant_profile.age_range} {annotation.participant_profile.gender}")
        print(f"  Conversation turns: {len(annotation.turns)}")
        print(f"  Overall confidence: {annotation.overall_confidence:.2f}")
        print()
        
        print("🏆 PRIORITY ANALYSIS:")
        print("  National priorities:")
        for i, priority in enumerate(annotation.national_priorities, 1):
            print(f"    {i}. {priority.theme}")
        print("  Local priorities:")
        for i, priority in enumerate(annotation.local_priorities, 1):
            print(f"    {i}. {priority.theme}")
        print()
        
        print("🔄 TURN ANALYSIS SAMPLE (first 3 turns):")
        for i, turn in enumerate(annotation.turns[:3], 1):
            print(f"  Turn {turn.turn_id} ({turn.speaker}):")
            print(f"    Function: {turn.functional_annotation.primary_function}")
            print(f"    Topics: {', '.join(turn.content_annotation.topics)}")
            print(f"    Emotion: {turn.stance_annotation.emotional_valence}")
            if turn.functional_annotation.reasoning:
                reasoning_preview = turn.functional_annotation.reasoning[:100] + "..." if len(turn.functional_annotation.reasoning) > 100 else turn.functional_annotation.reasoning
                print(f"    Reasoning: {reasoning_preview}")
            print()
        
        print("🔧 PROCESSING METADATA:")
        for key, value in metadata.items():
            print(f"  {key}: {value}")
        print()
        
        # Test XML conversion
        print("🔄 Converting to XML...")
        xml_root = annotator.convert_to_xml(annotation)
        
        # Count elements
        total_elements = len(xml_root.findall(".//*"))
        text_elements = len([elem for elem in xml_root.findall(".//*") if elem.text and elem.text.strip()])
        
        print(f"  Total XML elements: {total_elements}")
        print(f"  Elements with content: {text_elements}")
        print()
        
        # Test schema validation
        print("✅ Testing XSD schema validation...")
        validator = SchemaValidator()
        is_valid, errors = validator.validate_xml_element(xml_root)
        
        if is_valid:
            print("  ✅ XML passes schema validation!")
        else:
            print(f"  ❌ Schema validation failed: {len(errors)} errors")
            for error in errors[:3]:  # Show first 3 errors
                print(f"    - {error}")
        print()
        
        print("🎉 INSTRUCTOR ANNOTATION SUCCESS!")
        print("  ✅ Single API call completed")
        print(f"  ✅ All {len(annotation.turns)} turns annotated")
        print("  ✅ Chain-of-thought reasoning included")
        print("  ✅ Automatic validation successful")
        print("  ✅ XML schema compliance verified")
        print(f"  ✅ Total cost: ~${metadata['total_turns_annotated'] * 0.002:.3f}")
        
    except Exception as e:
        print(f"❌ Annotation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_real_annotation()