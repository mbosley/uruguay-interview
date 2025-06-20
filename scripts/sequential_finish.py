#!/usr/bin/env python3
"""
Sequential annotation processor to finish remaining interviews.
Based on successful individual tests - no parallel complexity.
"""
import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.pipeline.annotation.multipass_annotator import MultiPassAnnotator
from src.pipeline.ingestion.document_processor import DocumentProcessor

class SequentialProcessor:
    """Simple sequential processor without parallel complexity."""
    
    def __init__(self, budget_limit: float = 0.30):
        self.budget_limit = budget_limit
        self.output_dir = Path("data/processed/annotations/production")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.total_cost = 0.0
        self.completed = 0
        self.failed = 0
        self.results = []
        
        print(f"📝 Sequential processor initialized - Budget: ${budget_limit}")
    
    def get_remaining_interviews(self):
        """Get list of remaining interviews."""
        txt_dir = Path("data/processed/interviews_txt")
        completed_ids = set()
        
        # Get completed IDs
        for file_path in self.output_dir.glob("*_final_annotation.json"):
            interview_id = file_path.stem.replace("_final_annotation", "")
            completed_ids.add(interview_id)
        
        # Get remaining
        remaining = []
        for txt_file in txt_dir.glob("*.txt"):
            parts = txt_file.stem.split("_")
            interview_id = parts[2] if len(parts) >= 3 else txt_file.stem
            
            if interview_id not in completed_ids:
                try:
                    with open(txt_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    word_count = len(content.split())
                except:
                    word_count = 0
                
                remaining.append({
                    'interview_id': interview_id,
                    'file_path': txt_file,
                    'word_count': word_count
                })
        
        # Sort by word count (easiest first)
        remaining.sort(key=lambda x: x['word_count'])
        return remaining
    
    async def process_single_interview(self, interview_info):
        """Process one interview with proper timeout."""
        interview_id = interview_info['interview_id']
        file_path = interview_info['file_path']
        word_count = interview_info['word_count']
        
        print(f"📄 Processing {interview_id} ({word_count:,} words)")
        
        # Budget check
        if self.total_cost >= self.budget_limit:
            print(f"💰 Budget limit ${self.budget_limit} reached - stopping")
            return False
        
        start_time = time.time()
        
        try:
            # Load interview
            processor = DocumentProcessor()
            interview = processor.process_interview(file_path)
            
            # Create annotator
            annotator = MultiPassAnnotator(
                model_name="gpt-4.1-nano",
                temperature=0.1,
                turns_per_batch=6
            )
            
            # Set timeout based on word count
            if word_count < 3000:
                timeout = 200  # ~3 minutes
            elif word_count < 6000:
                timeout = 350  # ~6 minutes  
            elif word_count < 10000:
                timeout = 500  # ~8 minutes
            else:
                timeout = 800  # ~13 minutes for very large ones
            
            print(f"   Timeout: {timeout}s, Starting annotation...")
            
            # Annotate with timeout
            annotation_data, metadata = await asyncio.wait_for(
                annotator.annotate_interview(interview),
                timeout=timeout
            )
            
            processing_time = time.time() - start_time
            cost = metadata['total_cost']
            coverage = metadata['turn_coverage']['coverage_percentage']
            
            # Save annotation
            output_file = self.output_dir / f"{interview_id}_final_annotation.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "annotation_data": annotation_data,
                    "processing_metadata": metadata,
                    "production_info": {
                        "processed_at": datetime.now().isoformat(),
                        "processing_time": processing_time,
                        "timeout_used": timeout,
                        "pipeline_version": "sequential_v1.0",
                        "word_count": word_count
                    }
                }, f, indent=2, ensure_ascii=False)
            
            # Update counters
            self.total_cost += cost
            self.completed += 1
            
            result = {
                'interview_id': interview_id,
                'success': True,
                'cost': cost,
                'time': processing_time,
                'coverage': coverage,
                'api_calls': metadata['total_api_calls'],
                'word_count': word_count
            }
            self.results.append(result)
            
            print(f"   ✅ Success: {coverage:.0f}% coverage, ${cost:.4f}, {processing_time:.1f}s")
            return True
            
        except asyncio.TimeoutError:
            processing_time = time.time() - start_time
            print(f"   ⏰ TIMEOUT after {processing_time:.1f}s (limit: {timeout}s)")
            self.failed += 1
            
            self.results.append({
                'interview_id': interview_id,
                'success': False,
                'error': f'Timeout after {timeout}s',
                'time': processing_time,
                'word_count': word_count
            })
            return True  # Continue processing others
            
        except Exception as e:
            processing_time = time.time() - start_time
            print(f"   ❌ Error: {e}")
            self.failed += 1
            
            self.results.append({
                'interview_id': interview_id,
                'success': False,
                'error': str(e),
                'time': processing_time,
                'word_count': word_count
            })
            return True  # Continue processing others
    
    async def run_sequential_processing(self):
        """Run sequential processing of all remaining interviews."""
        print("🚀 Starting sequential annotation processing")
        print("="*50)
        
        remaining = self.get_remaining_interviews()
        total = len(remaining)
        
        if total == 0:
            print("✅ No remaining interviews - all complete!")
            return {"status": "complete"}
        
        print(f"📊 Found {total} remaining interviews")
        print(f"💰 Budget: ${self.budget_limit}")
        print(f"📈 Estimated cost: ${total * 0.006:.2f}")
        print(f"⏱️  Estimated time: {total * 1.5:.1f} minutes")
        print()
        
        start_time = time.time()
        
        # Process each interview sequentially
        for i, interview_info in enumerate(remaining, 1):
            print(f"[{i:2d}/{total}] ", end="")
            
            success = await self.process_single_interview(interview_info)
            if not success:  # Budget exceeded
                break
            
            # Progress update
            if i % 5 == 0 or i == total:
                elapsed = time.time() - start_time
                rate = self.completed / elapsed if elapsed > 0 else 0
                remaining_count = total - i
                eta = remaining_count / rate if rate > 0 else 0
                
                print(f"   📊 Progress: {self.completed}/{total} completed, {self.failed} failed")
                print(f"   💰 Cost: ${self.total_cost:.4f} / ${self.budget_limit}")
                print(f"   ⚡ Rate: {rate * 60:.1f} interviews/minute")
                print(f"   ⏱️  ETA: {eta / 60:.1f} minutes")
                print()
        
        total_time = time.time() - start_time
        
        # Final summary
        print("="*50)
        print(f"🎯 SEQUENTIAL PROCESSING COMPLETE")
        print("="*50)
        print(f"Total processed: {self.completed + self.failed}/{total}")
        print(f"Successful: {self.completed}")
        print(f"Failed: {self.failed}")
        print(f"Success rate: {(self.completed / (self.completed + self.failed)) * 100:.1f}%")
        print(f"Total cost: ${self.total_cost:.4f}")
        print(f"Total time: {total_time / 60:.1f} minutes")
        print(f"Average time per interview: {total_time / max(self.completed + self.failed, 1):.1f} seconds")
        
        # Save results
        summary = {
            "sequential_summary": {
                "total_interviews": total,
                "completed": self.completed,
                "failed": self.failed,
                "success_rate": (self.completed / (self.completed + self.failed)) * 100 if (self.completed + self.failed) > 0 else 0,
                "total_cost": self.total_cost,
                "total_time_minutes": total_time / 60,
                "avg_time_per_interview": total_time / max(self.completed + self.failed, 1)
            },
            "results": self.results,
            "timestamp": datetime.now().isoformat()
        }
        
        summary_file = self.output_dir / f"sequential_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Summary saved: {summary_file}")
        
        return summary

async def main():
    """Main sequential processing function."""
    try:
        processor = SequentialProcessor(budget_limit=0.30)
        summary = await processor.run_sequential_processing()
        
        if "status" in summary and summary["status"] == "complete":
            return True
        
        summary_data = summary.get("sequential_summary", {})
        success_rate = summary_data.get("success_rate", 0)
        
        return success_rate >= 80
        
    except Exception as e:
        print(f"❌ Sequential processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)