#!/usr/bin/env python3
"""
Generate a sample of the new progressive annotation output.
Shows what the completed XML looks like with chain-of-thought reasoning.
"""
import sys
from pathlib import Path
import xml.etree.ElementTree as ET
import logging

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.pipeline.ingestion.document_processor import DocumentProcessor
from src.pipeline.annotation.annotation_engine import AnnotationEngine
from src.pipeline.annotation.progressive_annotator import ProgressiveAnnotator

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def generate_sample_annotation():
    """Generate a sample of the new annotation output."""
    
    # Find test interview
    txt_dir = project_root / "data" / "processed" / "interviews_txt"
    txt_files = list(txt_dir.glob("*.txt"))
    
    if not txt_files:
        print("No interview files found")
        return
    
    # Use smallest file
    test_file = min(txt_files, key=lambda f: f.stat().st_size)
    
    # Process interview
    processor = DocumentProcessor()
    interview = processor.process_interview(test_file)
    
    # Create progressive annotator
    engine = AnnotationEngine(model_provider="openai", model_name="gpt-4o-mini")
    annotator = ProgressiveAnnotator(engine)
    
    # Create skeleton
    skeleton = annotator.create_skeleton(interview)
    annotator.current_xml = skeleton
    annotator.master_prompt = annotator.create_master_prompt(interview)
    
    print(f"Generating sample annotation for interview {interview.id}")
    print(f"Original interview has {len(skeleton.findall('.//turn'))} conversation turns")
    
    # Fill a few key sections to show the output
    sections_to_fill = [
        (".//metadata/interview_id", "Interview ID"),
        (".//metadata/date", "Interview date"),
        (".//metadata/location/municipality", "Municipality"),
        (".//metadata/location/department", "Department"),
        (".//metadata/location/locality_size", "Locality size (rural, small_town, etc.)"),
        (".//participant_profile/age_range", "Participant age range"),
        (".//participant_profile/gender", "Participant gender"),
        (".//participant_profile/occupation_sector", "Participant occupation sector"),
    ]
    
    print("\nFilling interview-level sections...")
    for xpath, description in sections_to_fill:
        print(f"  Filling: {description}")
        success = annotator.fill_section(xpath, description)
        if not success:
            print(f"    ❌ Failed")
    
    # Fill first turn's functional annotation with reasoning
    print("\nFilling first turn's functional annotation...")
    first_turn = skeleton.find(".//turn")
    turn_text = first_turn.find("text").text
    
    # Create a custom reasoning prompt for demonstration
    reasoning_prompt = f"""
{annotator.master_prompt}

CURRENT XML STATE:
{ET.tostring(annotator.current_xml, encoding='unicode')}

TASK: Fill the reasoning section for the first turn's functional annotation.

Turn text: "{turn_text}"

Provide chain-of-thought analysis for functional annotation. Consider:
1. What is the speaker doing in this turn?
2. What linguistic cues indicate the function?
3. What are alternative interpretations?
4. What is your confidence level?

Return only the reasoning content (no XML tags).
"""
    
    try:
        reasoning_response = engine._call_openai(reasoning_prompt, 0.1)
        
        # Update the reasoning section
        functional_reasoning = first_turn.find(".//functional_annotation/reasoning")
        if functional_reasoning is not None:
            functional_reasoning.text = reasoning_response.strip()
            print("  ✅ Added reasoning")
        
        # Fill the primary function
        function_prompt = f"""
{annotator.master_prompt}

Based on the reasoning: "{reasoning_response.strip()}"

What is the primary function of this turn? Choose from:
greeting, problem_identification, solution_proposal, agreement, disagreement, 
question, clarification, narrative, evaluation, closing, elaboration, meta_commentary

Return only the function name.
"""
        
        function_response = engine._call_openai(function_prompt, 0.1)
        primary_function = first_turn.find(".//functional_annotation/primary_function")
        if primary_function is not None:
            primary_function.text = function_response.strip()
            print("  ✅ Added primary function")
        
    except Exception as e:
        print(f"  ❌ Error filling turn annotation: {e}")
    
    return annotator.current_xml


def display_sample_output(xml_root):
    """Display formatted sample of the annotation output."""
    
    print("\n" + "="*80)
    print("SAMPLE PROGRESSIVE ANNOTATION OUTPUT")
    print("="*80)
    
    # Show interview-level metadata
    print("\n📋 INTERVIEW METADATA:")
    metadata = xml_root.find(".//metadata")
    if metadata is not None:
        for child in metadata:
            if child.tag == "location":
                print(f"  📍 Location:")
                for loc_child in child:
                    print(f"      {loc_child.tag}: {loc_child.text}")
            else:
                print(f"  {child.tag}: {child.text}")
    
    # Show participant profile
    print("\n👤 PARTICIPANT PROFILE:")
    profile = xml_root.find(".//participant_profile")
    if profile is not None:
        for child in profile:
            print(f"  {child.tag}: {child.text}")
    
    # Show turn count
    turns = xml_root.findall(".//turn")
    print(f"\n🔄 CONVERSATION TURNS: {len(turns)} total")
    
    # Show first few turns with details
    print("\n📝 SAMPLE TURNS (first 3):")
    for i, turn in enumerate(turns[:3], 1):
        turn_id = turn.find("turn_id").text
        speaker = turn.find("speaker").text
        text = turn.find("text").text
        
        print(f"\n  Turn {turn_id} ({speaker}):")
        print(f"    Text: {text[:100]}{'...' if len(text) > 100 else ''}")
        
        # Show functional annotation if filled
        functional = turn.find(".//functional_annotation")
        if functional is not None:
            reasoning = functional.find("reasoning")
            primary_func = functional.find("primary_function")
            
            if reasoning is not None and reasoning.text and "FILL" not in reasoning.text:
                print(f"    🧠 Reasoning: {reasoning.text[:150]}{'...' if len(reasoning.text) > 150 else ''}")
            
            if primary_func is not None and primary_func.text and "FILL" not in primary_func.text:
                print(f"    ⚡ Function: {primary_func.text}")
        
        # Show placeholders for other annotation types
        content_reasoning = turn.find(".//content_annotation/reasoning")
        evidence_reasoning = turn.find(".//evidence_annotation/reasoning")
        stance_reasoning = turn.find(".//stance_annotation/reasoning")
        
        placeholders = []
        if content_reasoning is not None and "FILL" in content_reasoning.text:
            placeholders.append("content")
        if evidence_reasoning is not None and "FILL" in evidence_reasoning.text:
            placeholders.append("evidence")
        if stance_reasoning is not None and "FILL" in stance_reasoning.text:
            placeholders.append("stance")
        
        if placeholders:
            print(f"    📋 Ready to fill: {', '.join(placeholders)} annotations")
    
    # Show structure overview
    total_elements = len(xml_root.findall(".//*"))
    filled_elements = len([e for e in xml_root.findall(".//*") if e.text and "FILL" not in e.text])
    
    print(f"\n📊 ANNOTATION STRUCTURE:")
    print(f"  Total XML elements: {total_elements}")
    print(f"  Elements filled: {filled_elements}")
    print(f"  Completion: {filled_elements/total_elements*100:.1f}%")
    
    print(f"\n✨ KEY ADVANTAGES:")
    print(f"  🎯 Complete turn coverage: {len(turns)} turns (vs 2 in old approach)")
    print(f"  🧠 Chain-of-thought reasoning for every annotation decision")
    print(f"  🔧 Section-by-section filling allows targeted retry and validation")
    print(f"  📋 Systematic progression ensures nothing is missed")
    print(f"  🎛️ Full control over annotation quality and consistency")


if __name__ == "__main__":
    try:
        xml_root = generate_sample_annotation()
        display_sample_output(xml_root)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)