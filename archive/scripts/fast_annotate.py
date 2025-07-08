#!/usr/bin/env python3
"""
Fast annotation with aggressive timeouts and error recovery.
Designed to avoid hanging processes.
"""
import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Set
import signal

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.pipeline.annotation.multipass_annotator import MultiPassAnnotator
from src.pipeline.ingestion.document_processor import DocumentProcessor

# Configure minimal logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class FastAnnotator:
    """Fast annotator with aggressive timeouts to prevent hanging."""
    
    def __init__(self, max_workers: int = 4, budget_limit: float = 0.30):
        self.max_workers = max_workers
        self.budget_limit = budget_limit
        self.output_dir = Path("data/processed/annotations/production")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.total_cost = 0.0
        self.completed = 0
        self.failed = 0
        self.start_time = time.time()
        
        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.shutdown)
        self.shutdown_requested = False
        
        print(f"🚀 Fast annotator: {max_workers} workers, ${budget_limit} budget")
    
    def shutdown(self, signum, frame):
        """Graceful shutdown handler."""
        print(f"\n⚠️  Shutdown requested...")
        self.shutdown_requested = True
    
    def get_remaining_interviews(self) -> List[Dict[str, Any]]:
        """Get remaining interviews sorted by difficulty."""
        txt_dir = Path("data/processed/interviews_txt")
        completed_ids = set()
        
        # Get completed IDs
        for file_path in self.output_dir.glob("*_final_annotation.json"):
            interview_id = file_path.stem.replace("_final_annotation", "")
            completed_ids.add(interview_id)
        
        # Get remaining interviews
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
    
    async def annotate_single_interview(self, interview_info: Dict[str, Any], job_id: int) -> Dict[str, Any]:
        """Annotate one interview with aggressive timeout."""
        interview_id = interview_info['interview_id']
        file_path = interview_info['file_path']
        word_count = interview_info['word_count']
        
        start_time = time.time()
        result = {
            'job_id': job_id,
            'interview_id': interview_id,
            'success': False,
            'cost': 0.0,
            'time': 0.0,
            'error': None
        }
        
        # Check for shutdown or budget
        if self.shutdown_requested:
            result['error'] = "Shutdown requested"
            return result
        
        if self.total_cost >= self.budget_limit:
            result['error'] = f"Budget limit ${self.budget_limit} reached"
            return result
        
        try:
            print(f"[{job_id:2d}] Starting {interview_id} ({word_count:,} words)")
            
            # Load interview
            processor = DocumentProcessor()
            interview = processor.process_interview(file_path)
            
            # Create annotator
            annotator = MultiPassAnnotator(
                model_name="gpt-4.1-nano",
                temperature=0.1,
                turns_per_batch=6
            )
            
            # Determine timeout based on word count
            if word_count < 3000:
                timeout = 120  # 2 minutes for small interviews
            elif word_count < 6000:
                timeout = 180  # 3 minutes for medium interviews
            else:
                timeout = 300  # 5 minutes for large interviews
            
            print(f"[{job_id:2d}] Timeout set to {timeout}s for {word_count:,} words")
            
            # Annotate with strict timeout
            annotation_data, metadata = await asyncio.wait_for(
                annotator.annotate_interview(interview),
                timeout=timeout
            )
            
            # Success
            result['cost'] = metadata['total_cost']
            result['time'] = time.time() - start_time
            result['coverage'] = metadata['turn_coverage']['coverage_percentage']
            result['api_calls'] = metadata['total_api_calls']
            
            # Save annotation
            output_file = self.output_dir / f"{interview_id}_final_annotation.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "annotation_data": annotation_data,
                    "processing_metadata": metadata,
                    "production_info": {
                        "job_id": job_id,
                        "processed_at": datetime.now().isoformat(),
                        "processing_time": result['time'],
                        "timeout_used": timeout,
                        "pipeline_version": "fast_v1.0"
                    }
                }, f, indent=2, ensure_ascii=False)
            
            result['success'] = True
            self.total_cost += result['cost']
            self.completed += 1
            
            print(f"[{job_id:2d}] ✅ {interview_id}: {result['coverage']:.0f}% coverage, ${result['cost']:.4f}, {result['time']:.1f}s")
            
        except asyncio.TimeoutError:
            result['error'] = f"Timeout after {timeout}s"
            result['time'] = time.time() - start_time
            self.failed += 1
            print(f"[{job_id:2d}] ⏰ {interview_id}: TIMEOUT after {timeout}s")
            
        except Exception as e:
            result['error'] = str(e)
            result['time'] = time.time() - start_time
            self.failed += 1
            print(f"[{job_id:2d}] ❌ {interview_id}: {e}")
        
        return result
    
    async def run_fast_annotation(self) -> Dict[str, Any]:
        """Run fast annotation with aggressive error handling."""
        print("⚡ Starting fast annotation pipeline")
        
        remaining = self.get_remaining_interviews()
        total = len(remaining)
        
        if total == 0:
            print("✅ No remaining interviews")
            return {"status": "complete"}
        
        print(f"📄 Processing {total} remaining interviews")
        print(f"💰 Budget: ${self.budget_limit}, Estimated: ${total * 0.008:.2f}")
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def controlled_process(interview_info, job_id):
            async with semaphore:
                return await self.annotate_single_interview(interview_info, job_id)
        
        # Process in small batches to avoid overwhelming the system
        batch_size = 10
        all_results = []
        
        for i in range(0, total, batch_size):
            if self.shutdown_requested:
                break
            
            batch = remaining[i:i + batch_size]
            print(f"\n🔄 Processing batch {i//batch_size + 1}: {len(batch)} interviews")
            
            # Create tasks for this batch
            tasks = []
            for j, interview_info in enumerate(batch):
                task = asyncio.create_task(
                    controlled_process(interview_info, i + j + 1)
                )
                tasks.append(task)
            
            # Wait for batch completion
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process batch results
            for result in batch_results:
                if isinstance(result, Exception):
                    all_results.append({'error': str(result), 'success': False})
                else:
                    all_results.append(result)
            
            # Progress update
            elapsed = time.time() - self.start_time
            rate = self.completed / elapsed if elapsed > 0 else 0
            print(f"📊 Batch complete: {self.completed}/{total} done, {self.failed} failed, ${self.total_cost:.3f} spent, {rate*60:.1f}/min")
        
        # Final summary
        total_time = time.time() - self.start_time
        
        summary = {
            "fast_annotation_summary": {
                "total_interviews": total,
                "completed": self.completed,
                "failed": self.failed,
                "success_rate": (self.completed / total) * 100 if total > 0 else 0,
                "total_cost": self.total_cost,
                "total_time_minutes": total_time / 60,
                "avg_time_per_interview": total_time / max(self.completed, 1),
                "shutdown_requested": self.shutdown_requested
            },
            "results": all_results,
            "timestamp": datetime.now().isoformat()
        }
        
        return summary

async def main():
    """Main function."""
    try:
        annotator = FastAnnotator(max_workers=4, budget_limit=0.30)
        summary = await annotator.run_fast_annotation()
        
        # Print final results
        summary_data = summary.get("fast_annotation_summary", {})
        
        print(f"\n" + "="*50)
        print(f"⚡ FAST ANNOTATION COMPLETE")
        print(f"="*50)
        print(f"Completed: {summary_data.get('completed', 0)}/{summary_data.get('total_interviews', 0)}")
        print(f"Failed: {summary_data.get('failed', 0)}")
        print(f"Success rate: {summary_data.get('success_rate', 0):.1f}%")
        print(f"Total cost: ${summary_data.get('total_cost', 0):.4f}")
        print(f"Total time: {summary_data.get('total_time_minutes', 0):.1f} minutes")
        
        # Save summary
        summary_file = Path("data/processed/annotations/production") / f"fast_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        return summary_data.get('success_rate', 0) >= 80
        
    except Exception as e:
        print(f"❌ Fast annotation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)