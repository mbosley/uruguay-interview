#!/usr/bin/env python3
"""Test and compare enhanced JSON annotator with original approaches."""
import json
import time
from pathlib import Path
import sys
sys.path.insert(0, str(Path.cwd()))

from src.pipeline.annotation.enhanced_json_annotator import EnhancedJSONAnnotator
from src.pipeline.annotation.json_mode_annotator import JSONModeAnnotator
from src.pipeline.ingestion.document_processor import DocumentProcessor


def test_enhanced_vs_original():
    """Compare enhanced annotator with original JSON mode."""
    
    print("🔍 ENHANCED vs ORIGINAL JSON MODE COMPARISON")
    print("=" * 60)
    
    # Get test interview
    txt_dir = Path("data/processed/interviews_txt")
    txt_files = list(txt_dir.glob("*.txt"))
    
    if not txt_files:
        print("❌ No interview files found")
        return
    
    # Use a small-medium file for testing
    test_files = sorted(txt_files, key=lambda f: f.stat().st_size)
    test_file = test_files[3]  # Small but not tiny
    
    # Process interview
    processor = DocumentProcessor()
    interview = processor.process_interview(test_file)
    
    print(f"📄 Test Interview: {interview.id}")
    print(f"   Word count: {len(interview.text.split()):,}")
    print(f"   File size: {test_file.stat().st_size:,} bytes")
    print()
    
    results = {}
    
    # Test Original JSON Mode
    print("🤖 Testing Original JSON Mode...")
    original_annotator = JSONModeAnnotator()
    
    start_time = time.time()
    try:
        original_data, original_metadata = original_annotator.annotate_interview(interview)
        original_time = time.time() - start_time
        
        results["original"] = {
            "data": original_data,
            "metadata": original_metadata,
            "processing_time": original_time,
            "status": "success"
        }
        
        print(f"✅ Original completed in {original_time:.1f}s")
        print(f"   Cost: ${original_metadata['estimated_cost']:.4f}")
        print(f"   Turns: {len(original_data['conversation_turns'])}")
        
    except Exception as e:
        results["original"] = {"status": "failed", "error": str(e)}
        print(f"❌ Original failed: {e}")
    
    print()
    
    # Test Enhanced JSON Mode
    print("🚀 Testing Enhanced JSON Mode...")
    enhanced_annotator = EnhancedJSONAnnotator()
    
    start_time = time.time()
    try:
        enhanced_data, enhanced_metadata = enhanced_annotator.annotate_interview(interview)
        enhanced_time = time.time() - start_time
        
        results["enhanced"] = {
            "data": enhanced_data,
            "metadata": enhanced_metadata,
            "processing_time": enhanced_time,
            "status": "success"
        }
        
        print(f"✅ Enhanced completed in {enhanced_time:.1f}s")
        print(f"   Cost: ${enhanced_metadata['estimated_cost']:.4f}")
        print(f"   Turns: {len(enhanced_data['conversation_analysis']['turns'])}")
        
        # Quality validation
        quality_report = enhanced_annotator.validate_annotation_quality(enhanced_data)
        print(f"   Quality score: {quality_report['overall_score']:.2f}")
        
        results["enhanced"]["quality_report"] = quality_report
        
    except Exception as e:
        results["enhanced"] = {"status": "failed", "error": str(e)}
        print(f"❌ Enhanced failed: {e}")
    
    print()
    
    # Compare Results
    if results["original"]["status"] == "success" and results["enhanced"]["status"] == "success":
        print("📊 DETAILED COMPARISON")
        print("-" * 40)
        
        orig = results["original"]
        enh = results["enhanced"]
        
        print(f"COST COMPARISON:")
        print(f"  Original: ${orig['metadata']['estimated_cost']:.4f}")
        print(f"  Enhanced: ${enh['metadata']['estimated_cost']:.4f}")
        cost_ratio = enh['metadata']['estimated_cost'] / orig['metadata']['estimated_cost']
        print(f"  Cost ratio: {cost_ratio:.1f}x")
        
        print(f"\nTIME COMPARISON:")
        print(f"  Original: {orig['processing_time']:.1f}s")
        print(f"  Enhanced: {enh['processing_time']:.1f}s")
        time_ratio = enh['processing_time'] / orig['processing_time']
        print(f"  Time ratio: {time_ratio:.1f}x")
        
        print(f"\nCOVERAGE COMPARISON:")
        orig_turns = len(orig['data']['conversation_turns'])
        enh_turns = len(enh['data']['conversation_analysis']['turns'])
        print(f"  Original turns: {orig_turns}")
        print(f"  Enhanced turns: {enh_turns}")
        
        print(f"\nANALYTICAL DEPTH:")
        
        # Compare priority analysis depth
        orig_p1 = orig['data']['national_priorities'][0]
        enh_p1 = enh['data']['priority_analysis']['national_priorities'][0]
        
        print(f"  Original priority 1 narrative: {len(orig_p1['narrative_elaboration'])} chars")
        print(f"  Enhanced priority 1 narrative: {len(enh_p1['narrative_elaboration'])} chars")
        
        print(f"\nFEATURE COMPARISON:")
        
        # Enhanced features not in original
        enhanced_features = [
            "uncertainty_tracking" in str(enh['data']),
            "confidence" in str(enh_p1),
            "supporting_quotes" in enh_p1,
            "cultural_patterns_identified" in str(enh['data']),
            "rhetorical_strategies" in str(enh['data']),
            "quality_assessment" in enh['data']
        ]
        
        feature_names = [
            "Uncertainty tracking",
            "Confidence scores", 
            "Supporting quotes",
            "Cultural patterns",
            "Rhetorical analysis",
            "Quality assessment"
        ]
        
        for feature, name in zip(enhanced_features, feature_names):
            status = "✅" if feature else "❌"
            print(f"  {status} {name}")
        
        # Sample content comparison
        print(f"\n📋 SAMPLE PRIORITY COMPARISON:")
        print(f"Original Theme: {orig_p1['theme']}")
        print(f"Enhanced Theme: {enh_p1['theme']}")
        
        print(f"\nOriginal Narrative:")
        print(f"  {orig_p1['narrative_elaboration'][:150]}...")
        
        print(f"\nEnhanced Narrative:")
        print(f"  {enh_p1['narrative_elaboration'][:150]}...")
        
        if 'supporting_quotes' in enh_p1 and enh_p1['supporting_quotes']:
            print(f"\nEnhanced Supporting Quote:")
            print(f"  \"{enh_p1['supporting_quotes'][0][:100]}...\"")
        
        print(f"\nEnhanced Confidence: {enh_p1.get('confidence', 'N/A')}")
        
    # Save comparison results
    output_file = f"enhanced_vs_original_comparison_{interview.id}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: {output_file}")
    
    # Summary
    if results["original"]["status"] == "success" and results["enhanced"]["status"] == "success":
        print(f"\n🎯 SUMMARY:")
        print(f"   Enhanced approach adds {cost_ratio:.1f}x cost for comprehensive XML-level analysis")
        print(f"   Processing time: {time_ratio:.1f}x longer but more thorough")
        print(f"   Quality features: uncertainty tracking, confidence scores, cultural context")
        print(f"   Analytical depth: Significantly enhanced with supporting quotes and reasoning")


if __name__ == "__main__":
    test_enhanced_vs_original()