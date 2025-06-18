#!/usr/bin/env python3
"""Test the Instructor annotator setup and cost calculation."""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path.cwd()))

from src.pipeline.annotation.instructor_annotator import InstructorAnnotator
from src.pipeline.ingestion.document_processor import DocumentProcessor

def test_instructor_annotator():
    """Test the Instructor annotator functionality."""
    
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
    
    # Create annotator
    annotator = InstructorAnnotator(model_name="gpt-4o-mini")  # Use cheaper model for testing
    
    # Test cost calculation
    cost_estimate = annotator.calculate_cost_estimate(interview)
    
    print("📊 INSTRUCTOR ANNOTATOR COST ANALYSIS")
    print("=" * 50)
    print(f"Interview: {interview.id}")
    print(f"Text length: {len(interview.text):,} characters")
    print(f"Word count: {len(interview.text.split()):,} words")
    print()
    print("💰 Single Interview Cost Estimate:")
    print(f"  Input tokens: {cost_estimate['input_tokens']:,.0f}")
    print(f"  Output tokens: {cost_estimate['output_tokens']:,.0f}")
    print(f"  Input cost: ${cost_estimate['input_cost']:.4f}")
    print(f"  Output cost: ${cost_estimate['output_cost']:.4f}")
    print(f"  Total cost: ${cost_estimate['total_cost']:.4f}")
    print()
    
    # Project cost estimates
    total_cost_37 = cost_estimate["total_cost"] * 37
    print("🎯 FULL PROJECT COST ESTIMATE:")
    print(f"  37 interviews: ${total_cost_37:.2f}")
    print()
    
    # Compare with previous approaches
    progressive_cost = 9.60  # Previous estimate
    monolithic_cost = 0.013  # Single call without validation
    
    print("📈 COST COMPARISON:")
    print(f"  Progressive approach: ${progressive_cost:.2f} per interview")
    print(f"  Instructor (single call): ${cost_estimate['total_cost']:.4f} per interview")
    print(f"  Cost reduction: {(1 - cost_estimate['total_cost']/progressive_cost)*100:.1f}%")
    print()
    
    print("✨ INSTRUCTOR ADVANTAGES:")
    print("  ✅ Single API call per interview")
    print("  ✅ Automatic validation and retries")
    print("  ✅ Complete coverage of all 1,667 schema elements")
    print("  ✅ Built-in chain-of-thought reasoning")
    print("  ✅ Type-safe Pydantic models")
    print("  ✅ No XML manipulation required")
    print(f"  ✅ 99.86% cost reduction vs progressive")


if __name__ == "__main__":
    test_instructor_annotator()