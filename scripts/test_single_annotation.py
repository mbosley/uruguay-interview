#!/usr/bin/env python3
"""
Test single interview annotation to measure exact timing and performance.
"""
import asyncio
import time
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.pipeline.annotation.multipass_annotator import MultiPassAnnotator
from src.pipeline.ingestion.document_processor import DocumentProcessor


async def test_single_interview():
    """Test annotation of a single interview with detailed timing."""
    print("🎯 SINGLE INTERVIEW ANNOTATION TEST")
    print("="*50)
    
    # Find a medium-sized interview for testing
    txt_dir = Path("data/processed/interviews_txt")
    txt_files = list(txt_dir.glob("*.txt"))
    
    if not txt_files:
        print("❌ No interview files found")
        return
    
    # Sort by file size and pick a medium one
    txt_files.sort(key=lambda f: f.stat().st_size)
    test_file = txt_files[len(txt_files)//2]  # Pick middle-sized file
    
    print(f"📄 Test file: {test_file.name}")
    print(f"📊 File size: {test_file.stat().st_size:,} bytes")
    
    # Load interview
    processor = DocumentProcessor()
    interview = processor.process_interview(test_file)
    
    word_count = len(interview.text.split())
    print(f"📝 Interview {interview.id}: {word_count:,} words")
    print()
    
    # Create annotator
    annotator = MultiPassAnnotator(
        model_name="gpt-4.1-nano",
        temperature=0.1,
        turns_per_batch=6
    )
    
    # Time the annotation
    print("⏱️  Starting annotation...")
    start_time = time.time()
    
    try:
        annotation_data, metadata = await annotator.annotate_interview(interview)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print("✅ Annotation completed!")
        print()
        print("📈 RESULTS:")
        print(f"   Total time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
        print(f"   API calls: {metadata['total_api_calls']}")
        print(f"   Total cost: ${metadata['total_cost']:.4f}")
        print(f"   Turn coverage: {metadata['turn_coverage']['analyzed_turns']}/{metadata['turn_coverage']['total_turns']} ({metadata['turn_coverage']['coverage_percentage']:.1f}%)")
        print(f"   Overall confidence: {metadata['overall_confidence']}")
        
        print(f"\n📊 API CALL BREAKDOWN:")
        for call in metadata['api_call_breakdown']:
            print(f"   {call['pass']}: ${call['cost']:.4f} ({call['tokens']} tokens)")
        
        print(f"\n⚡ PERFORMANCE METRICS:")
        print(f"   Words per second: {word_count/total_time:.1f}")
        print(f"   Cost per word: ${metadata['total_cost']/word_count:.6f}")
        print(f"   Time per API call: {total_time/metadata['total_api_calls']:.1f}s")
        
        # Estimate for all 37 interviews
        estimated_total_time = total_time * 37
        estimated_total_cost = metadata['total_cost'] * 37
        
        print(f"\n🎯 PROJECTION FOR ALL 37 INTERVIEWS:")
        print(f"   Sequential time: {estimated_total_time/60:.1f} minutes ({estimated_total_time/3600:.1f} hours)")
        print(f"   Parallel time (4 workers): {estimated_total_time/4/60:.1f} minutes")
        print(f"   Parallel time (8 workers): {estimated_total_time/8/60:.1f} minutes")
        print(f"   Total cost: ${estimated_total_cost:.2f}")
        
        return {
            'time_seconds': total_time,
            'cost': metadata['total_cost'],
            'api_calls': metadata['total_api_calls'],
            'word_count': word_count,
            'turn_coverage': metadata['turn_coverage']['coverage_percentage']
        }
        
    except Exception as e:
        print(f"❌ Annotation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    result = await test_single_interview()
    return result is not None


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)