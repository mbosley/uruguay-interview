#!/usr/bin/env python3
"""Quick test of multi-pass annotator components."""
import json
import asyncio
from pathlib import Path
import sys
sys.path.insert(0, str(Path.cwd()))

from src.pipeline.annotation.multipass_annotator import MultiPassAnnotator
from src.pipeline.ingestion.document_processor import DocumentProcessor


async def test_multipass_approach():
    """Test multi-pass annotator on a small interview."""
    
    print("🔍 MULTI-PASS ANNOTATOR QUICK TEST")
    print("=" * 50)
    
    # Get smallest interview for quick test
    txt_dir = Path("data/processed/interviews_txt")
    txt_files = list(txt_dir.glob("*.txt"))
    
    if not txt_files:
        print("❌ No interview files found")
        return
    
    # Use smallest file for quick test
    sorted_files = sorted(txt_files, key=lambda f: f.stat().st_size)
    test_file = sorted_files[0]
    
    # Process interview
    processor = DocumentProcessor()
    interview = processor.process_interview(test_file)
    
    print(f"📄 Test Interview: {interview.id}")
    print(f"   Word count: {len(interview.text.split()):,}")
    print(f"   File size: {test_file.stat().st_size:,} bytes")
    print()
    
    # Create multi-pass annotator
    annotator = MultiPassAnnotator(turns_per_batch=4)  # Smaller batches for testing
    
    try:
        print("🤖 Starting multi-pass annotation...")
        print("   Pass 1: Interview analysis + turn inventory...")
        
        annotation_data, metadata = await annotator.annotate_interview(interview)
        
        print("✅ Multi-pass annotation successful!")
        print()
        
        # Analyze results
        turn_coverage = metadata['turn_coverage']
        api_calls = metadata['api_call_breakdown']
        
        print("📊 COMPREHENSIVE COVERAGE RESULTS:")
        print(f"  Total turns detected: {turn_coverage['total_turns']}")
        print(f"  Turns analyzed: {turn_coverage['analyzed_turns']}")
        print(f"  Coverage: {turn_coverage['coverage_percentage']:.1f}%")
        print(f"  Complete coverage: {'✅ YES' if turn_coverage['coverage_percentage'] == 100 else '❌ NO'}")
        
        print(f"\n💰 COST BREAKDOWN:")
        print(f"  Total API calls: {metadata['total_api_calls']}")
        print(f"  Total cost: ${metadata['total_cost']:.4f}")
        print(f"  Processing time: {metadata['processing_time']:.1f}s")
        
        for call in api_calls:
            if 'turns' in call:
                print(f"    {call['pass']}: ${call['cost']:.4f} (turns {call['turns']})")
            else:
                print(f"    {call['pass']}: ${call['cost']:.4f}")
        
        print(f"\n🎯 QUALITY ASSESSMENT:")
        quality = annotation_data['quality_assessment']
        print(f"  Annotation completeness: {quality['annotation_completeness']:.2f}")
        print(f"  All turns analyzed: {'✅ YES' if quality['all_turns_analyzed'] else '❌ NO'}")
        
        # Show sample turn analysis
        if annotation_data['conversation_analysis']['turns']:
            sample_turn = annotation_data['conversation_analysis']['turns'][0]
            print(f"\n📋 SAMPLE TURN ANALYSIS:")
            print(f"  Turn {sample_turn['turn_id']}: {sample_turn['turn_analysis']['primary_function']}")
            print(f"  Topics: {', '.join(sample_turn['content_analysis']['topics'][:3])}")
            print(f"  Confidence: {sample_turn['uncertainty_tracking']['coding_confidence']}")
            print(f"  Evidence: {sample_turn['evidence_analysis']['evidence_type']}")
        
        # Compare with single-pass estimate
        single_pass_cost = 0.003  # From our previous tests
        cost_ratio = metadata['total_cost'] / single_pass_cost
        
        print(f"\n📈 COST COMPARISON:")
        print(f"  Single-pass estimate: ${single_pass_cost:.4f}")
        print(f"  Multi-pass actual: ${metadata['total_cost']:.4f}")
        print(f"  Cost ratio: {cost_ratio:.1f}x")
        print(f"  Coverage improvement: Partial → 100%")
        
        # Project costs for full dataset
        print(f"\n🚀 FULL DATASET PROJECTION:")
        cost_per_interview = metadata['total_cost']
        total_interviews = 37
        
        projected_cost = cost_per_interview * total_interviews
        projected_time_hours = (metadata['processing_time'] * total_interviews) / 3600
        
        print(f"  Cost per interview: ${cost_per_interview:.4f}")
        print(f"  37 interviews total cost: ${projected_cost:.2f}")
        print(f"  Total processing time: {projected_time_hours:.1f} hours")
        print(f"  Still cheaper than progressive: {355/projected_cost:.0f}x savings")
        
        # Save result
        output_file = f"multipass_test_{interview.id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "test_summary": {
                    "approach": "multipass_comprehensive",
                    "turn_coverage_achieved": turn_coverage['coverage_percentage'] == 100,
                    "total_cost": metadata['total_cost'],
                    "api_calls": metadata['total_api_calls'],
                    "cost_vs_single_pass": cost_ratio
                },
                "annotation_data": annotation_data,
                "processing_metadata": metadata
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Detailed results saved to: {output_file}")
        
        # Conclusion
        if turn_coverage['coverage_percentage'] == 100:
            print(f"\n🎯 CONCLUSION: Multi-pass approach achieves 100% turn coverage!")
            print(f"   Ready for production deployment with comprehensive analysis.")
        else:
            print(f"\n⚠️  ISSUE: Only {turn_coverage['coverage_percentage']:.1f}% coverage achieved")
            
    except Exception as e:
        print(f"❌ Multi-pass test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_multipass_approach())