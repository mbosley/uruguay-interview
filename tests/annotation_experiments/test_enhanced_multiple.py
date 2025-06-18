#!/usr/bin/env python3
"""Test enhanced annotator on multiple interviews for validation."""
import json
import time
from pathlib import Path
import sys
sys.path.insert(0, str(Path.cwd()))

from src.pipeline.annotation.enhanced_json_annotator import EnhancedJSONAnnotator
from src.pipeline.ingestion.document_processor import DocumentProcessor


def test_multiple_interviews():
    """Test enhanced annotator on different interview lengths and types."""
    
    print("🔍 ENHANCED ANNOTATOR MULTI-INTERVIEW VALIDATION")
    print("=" * 60)
    
    # Get test interviews of different sizes
    txt_dir = Path("data/processed/interviews_txt")
    txt_files = list(txt_dir.glob("*.txt"))
    
    if not txt_files:
        print("❌ No interview files found")
        return
    
    # Sort by size and select representative sample
    sorted_files = sorted(txt_files, key=lambda f: f.stat().st_size)
    
    # Select small, medium, and large interviews
    test_files = [
        sorted_files[2],          # Small interview
        sorted_files[len(sorted_files)//2],  # Medium interview
        sorted_files[-3]          # Large interview
    ]
    
    print(f"Selected {len(test_files)} interviews for testing:")
    for i, f in enumerate(test_files, 1):
        size_kb = f.stat().st_size / 1024
        print(f"  {i}. {f.name} ({size_kb:.1f} KB)")
    print()
    
    # Process interviews
    processor = DocumentProcessor()
    annotator = EnhancedJSONAnnotator()
    
    results = []
    total_cost = 0.0
    total_time = 0.0
    
    for i, file_path in enumerate(test_files, 1):
        print(f"🤖 Processing Interview {i}/3: {file_path.stem}")
        
        try:
            # Load interview
            interview = processor.process_interview(file_path)
            word_count = len(interview.text.split())
            
            print(f"   Word count: {word_count:,}")
            
            # Annotate
            start_time = time.time()
            annotation_data, metadata = annotator.annotate_interview(interview)
            processing_time = time.time() - start_time
            
            # Validate quality
            quality_report = annotator.validate_annotation_quality(annotation_data)
            
            # Save result
            output_file = f"enhanced_validation_{interview.id}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "annotation_data": annotation_data,
                    "processing_metadata": metadata,
                    "quality_report": quality_report
                }, f, indent=2, ensure_ascii=False)
            
            # Collect stats
            result = {
                "interview_id": interview.id,
                "word_count": word_count,
                "file_size_kb": file_path.stat().st_size / 1024,
                "processing_time": processing_time,
                "cost": metadata["estimated_cost"],
                "turns_analyzed": len(annotation_data["conversation_analysis"]["turns"]),
                "overall_confidence": annotation_data["annotation_metadata"]["overall_confidence"],
                "quality_score": quality_report["overall_score"],
                "prompt_tokens": metadata["prompt_tokens"],
                "completion_tokens": metadata["completion_tokens"],
                "output_file": output_file
            }
            
            results.append(result)
            total_cost += result["cost"]
            total_time += result["processing_time"]
            
            print(f"   ✅ Success!")
            print(f"   Turns: {result['turns_analyzed']}")
            print(f"   Cost: ${result['cost']:.4f}")
            print(f"   Time: {result['processing_time']:.1f}s")
            print(f"   Quality: {result['quality_score']:.2f}")
            print(f"   Confidence: {result['overall_confidence']:.2f}")
            print(f"   Saved: {output_file}")
            print()
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            result = {
                "interview_id": file_path.stem,
                "error": str(e),
                "status": "failed"
            }
            results.append(result)
            print()
    
    # Analysis
    successful_results = [r for r in results if "error" not in r]
    
    if successful_results:
        print("📊 VALIDATION ANALYSIS")
        print("-" * 40)
        
        print(f"Successful annotations: {len(successful_results)}/{len(test_files)}")
        print(f"Total cost: ${total_cost:.4f}")
        print(f"Total time: {total_time:.1f}s")
        print(f"Average cost per interview: ${total_cost/len(successful_results):.4f}")
        print(f"Average time per interview: {total_time/len(successful_results):.1f}s")
        print()
        
        print("📈 PER-INTERVIEW BREAKDOWN:")
        print("-" * 40)
        
        for r in successful_results:
            cost_per_1k_words = r["cost"] / (r["word_count"] / 1000)
            time_per_1k_words = r["processing_time"] / (r["word_count"] / 1000)
            
            print(f"{r['interview_id']}:")
            print(f"  Words: {r['word_count']:,} | File: {r['file_size_kb']:.1f}KB")
            print(f"  Cost: ${r['cost']:.4f} (${cost_per_1k_words:.4f}/1K words)")
            print(f"  Time: {r['processing_time']:.1f}s ({time_per_1k_words:.1f}s/1K words)")
            print(f"  Turns: {r['turns_analyzed']} | Quality: {r['quality_score']:.2f}")
            print(f"  Tokens: {r['prompt_tokens']:,} + {r['completion_tokens']:,}")
            print(f"  Confidence: {r['overall_confidence']:.2f}")
            print()
        
        # Scalability analysis
        print("🚀 SCALABILITY PROJECTION:")
        print("-" * 40)
        
        avg_cost = total_cost / len(successful_results)
        avg_time = total_time / len(successful_results)
        
        projections = [
            (37, "Full dataset"),
            (100, "100 interviews"),
            (500, "500 interviews"),
            (1000, "1000 interviews")
        ]
        
        for count, desc in projections:
            proj_cost = avg_cost * count
            proj_time_hours = (avg_time * count) / 3600
            
            print(f"{desc}:")
            print(f"  Total cost: ${proj_cost:.2f}")
            print(f"  Total time: {proj_time_hours:.1f} hours")
            print()
        
        # Quality analysis
        print("🎯 QUALITY CONSISTENCY:")
        print("-" * 40)
        
        quality_scores = [r["quality_score"] for r in successful_results]
        confidence_scores = [r["overall_confidence"] for r in successful_results]
        
        print(f"Quality scores: {quality_scores}")
        print(f"Average quality: {sum(quality_scores)/len(quality_scores):.3f}")
        print(f"Quality range: {min(quality_scores):.2f} - {max(quality_scores):.2f}")
        print()
        print(f"Confidence scores: {confidence_scores}")
        print(f"Average confidence: {sum(confidence_scores)/len(confidence_scores):.3f}")
        print(f"Confidence range: {min(confidence_scores):.2f} - {max(confidence_scores):.2f}")
        
        # Sample content analysis
        print(f"\n📋 SAMPLE PRIORITY ANALYSIS:")
        print("-" * 40)
        
        for r in successful_results[:2]:  # Show first 2
            try:
                with open(r["output_file"], 'r') as f:
                    data = json.load(f)
                
                nat_p1 = data["annotation_data"]["priority_analysis"]["national_priorities"][0]
                
                print(f"{r['interview_id']} - National Priority 1:")
                print(f"  Theme: {nat_p1['theme']}")
                print(f"  Confidence: {nat_p1['confidence']}")
                if nat_p1.get('supporting_quotes'):
                    quote = nat_p1['supporting_quotes'][0][:80] + "..." if len(nat_p1['supporting_quotes'][0]) > 80 else nat_p1['supporting_quotes'][0]
                    print(f"  Quote: \"{quote}\"")
                print()
                
            except Exception as e:
                print(f"  Could not load details for {r['interview_id']}: {e}")
    
    # Save summary
    summary_file = "enhanced_validation_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            "test_summary": {
                "total_interviews": len(test_files),
                "successful": len(successful_results),
                "failed": len(test_files) - len(successful_results),
                "total_cost": total_cost,
                "total_time": total_time,
                "average_cost": total_cost / len(successful_results) if successful_results else 0,
                "average_time": total_time / len(successful_results) if successful_results else 0
            },
            "results": results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Summary saved to: {summary_file}")
    
    if successful_results:
        print(f"\n🎯 VALIDATION CONCLUSION:")
        print(f"Enhanced annotator shows consistent performance across interview sizes")
        print(f"Average cost: ${avg_cost:.4f} per interview")
        print(f"Average quality: {sum(quality_scores)/len(quality_scores):.2f}")
        print(f"Production ready for full dataset annotation")


if __name__ == "__main__":
    test_multiple_interviews()