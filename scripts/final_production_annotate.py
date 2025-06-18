#!/usr/bin/env python3
"""
Final production annotation script - optimized for 8-10 minute total runtime.
Based on timing test: 58s per interview, targeting 4.5-9 minutes with 4-8 workers.
"""
import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import traceback

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.pipeline.annotation.multipass_annotator import MultiPassAnnotator
from src.pipeline.ingestion.document_processor import DocumentProcessor

# Configure concise logging
logging.basicConfig(
    level=logging.WARNING,  # Reduce log noise
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('final_production.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Silence verbose libraries
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('src.pipeline.annotation.multipass_annotator').setLevel(logging.WARNING)


class FinalProductionProcessor:
    """Final production processor optimized for speed and reliability."""
    
    def __init__(self, max_concurrent: int = 6, budget_limit: float = 1.00):
        """
        Initialize final processor.
        
        Args:
            max_concurrent: Optimal concurrency (6 workers = ~6 minute target)
            budget_limit: Safety budget limit
        """
        self.max_concurrent = max_concurrent
        self.budget_limit = budget_limit
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        # Thread-safe tracking
        self.completed = 0
        self.failed = 0
        self.total_cost = 0.0
        self.results = []
        self.lock = asyncio.Lock()
        
        # Setup output
        self.output_dir = Path("data/processed/annotations/production")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"🎯 Final production processor: {max_concurrent} workers, ${budget_limit} budget")
    
    def discover_interviews(self) -> List[Path]:
        """Get all interview files."""
        txt_dir = Path("data/processed/interviews_txt")
        files = list(txt_dir.glob("*.txt"))
        files.sort()
        return files
    
    async def process_single_interview(self, interview_path: Path, job_id: int) -> Dict[str, Any]:
        """Process one interview with timing."""
        async with self.semaphore:
            start_time = time.time()
            result = {
                'job_id': job_id,
                'file_path': str(interview_path),
                'interview_id': None,
                'success': False,
                'cost': 0.0,
                'processing_time': 0.0,
                'turn_coverage': 0,
                'error': None
            }
            
            try:
                # Budget check
                async with self.lock:
                    if self.total_cost >= self.budget_limit:
                        result['error'] = f"Budget limit ${self.budget_limit} reached"
                        self.failed += 1
                        return result
                
                # Load interview
                processor = DocumentProcessor()
                interview = processor.process_interview(interview_path)
                result['interview_id'] = interview.id
                
                # Create annotator for this job
                annotator = MultiPassAnnotator(
                    model_name="gpt-4.1-nano",
                    temperature=0.1,
                    turns_per_batch=6
                )
                
                # Annotate
                annotation_data, metadata = await annotator.annotate_interview(interview)
                
                # Process results
                result['cost'] = metadata['total_cost']
                result['processing_time'] = time.time() - start_time
                result['turn_coverage'] = metadata['turn_coverage']['coverage_percentage']
                result['api_calls'] = metadata['total_api_calls']
                
                # Save annotation
                output_file = self.output_dir / f"{interview.id}_final_annotation.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        "annotation_data": annotation_data,
                        "processing_metadata": metadata,
                        "production_info": {
                            "job_id": job_id,
                            "processed_at": datetime.now().isoformat(),
                            "processing_time": result['processing_time'],
                            "script_version": "final_production_v1.0"
                        }
                    }, f, indent=2, ensure_ascii=False)
                
                result['success'] = True
                
                # Update global counters
                async with self.lock:
                    self.completed += 1
                    self.total_cost += result['cost']
                
                print(f"[{job_id:2d}] ✅ {interview.id}: {result['turn_coverage']:.0f}% coverage, ${result['cost']:.4f}, {result['processing_time']:.1f}s")
                
            except Exception as e:
                result['error'] = str(e)
                result['processing_time'] = time.time() - start_time
                
                async with self.lock:
                    self.failed += 1
                
                print(f"[{job_id:2d}] ❌ {interview_path.name}: {e}")
            
            return result
    
    async def monitor_progress(self, total_files: int, start_time: float):
        """Lightweight progress monitoring."""
        while True:
            await asyncio.sleep(30)  # Update every 30 seconds
            
            async with self.lock:
                completed = self.completed
                failed = self.failed
                cost = self.total_cost
            
            if completed + failed >= total_files:
                break
            
            elapsed = time.time() - start_time
            rate = completed / elapsed if elapsed > 0 else 0
            remaining = total_files - completed - failed
            eta = remaining / rate if rate > 0 else 0
            
            print(f"📊 Progress: {completed}/{total_files} done, {failed} failed | ${cost:.3f} | {rate*60:.1f}/min | ETA: {eta/60:.1f}min")
    
    async def process_all_interviews(self) -> Dict[str, Any]:
        """Process all interviews with optimized parallel execution."""
        print("🚀 Starting final production annotation")
        
        # Discover interviews
        interview_files = self.discover_interviews()
        total_files = len(interview_files)
        
        print(f"📄 Processing {total_files} interviews with {self.max_concurrent} workers")
        print(f"⏱️  Estimated time: {total_files * 58 / self.max_concurrent / 60:.1f} minutes")
        print(f"💰 Estimated cost: ${total_files * 0.006:.2f}")
        print()
        
        start_time = time.time()
        
        # Create all tasks
        tasks = []
        for i, interview_path in enumerate(interview_files):
            task = asyncio.create_task(
                self.process_single_interview(interview_path, i + 1)
            )
            tasks.append(task)
        
        # Start monitoring
        monitor_task = asyncio.create_task(
            self.monitor_progress(total_files, start_time)
        )
        
        # Execute all tasks
        print("⚡ Processing started...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Stop monitoring
        monitor_task.cancel()
        
        # Process results
        total_time = time.time() - start_time
        successful_results = []
        failed_results = []
        
        for result in results:
            if isinstance(result, Exception):
                failed_results.append({'error': str(result)})
            elif result['success']:
                successful_results.append(result)
            else:
                failed_results.append(result)
        
        # Final stats
        async with self.lock:
            final_cost = self.total_cost
            final_completed = self.completed
            final_failed = self.failed
        
        # Generate report
        total_turns = sum(r.get('turn_coverage', 0) for r in successful_results) / len(successful_results) if successful_results else 0
        
        report = {
            "final_production_summary": {
                "total_interviews": total_files,
                "successful": final_completed,
                "failed": final_failed,
                "success_rate": (final_completed / total_files) * 100,
                "total_cost": final_cost,
                "total_time_minutes": total_time / 60,
                "interviews_per_minute": final_completed / (total_time / 60),
                "avg_cost_per_interview": final_cost / max(final_completed, 1),
                "avg_time_per_interview": total_time / max(final_completed, 1),
                "avg_turn_coverage": total_turns,
                "concurrency_used": self.max_concurrent
            },
            "detailed_results": successful_results + failed_results,
            "timestamp": datetime.now().isoformat()
        }
        
        # Save report
        report_file = self.output_dir / f"final_production_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return report


async def main():
    """Main production function."""
    print("🎯 URUGUAY INTERVIEWS - FINAL PRODUCTION RUN")
    print("Multi-pass annotation system - optimized for speed")
    print("Expected: ~6-9 minutes total, $0.22 cost, 100% coverage")
    print("="*60)
    
    try:
        # Create processor with optimal settings
        processor = FinalProductionProcessor(
            max_concurrent=6,  # Sweet spot for speed vs API limits
            budget_limit=1.00
        )
        
        # Process all interviews
        report = await processor.process_all_interviews()
        
        # Print final results
        summary = report['final_production_summary']
        
        print("\n" + "="*60)
        print("🎯 FINAL PRODUCTION COMPLETE")
        print("="*60)
        print(f"Success rate: {summary['success_rate']:.1f}% ({summary['successful']}/{summary['total_interviews']})")
        print(f"Total cost: ${summary['total_cost']:.4f}")
        print(f"Processing time: {summary['total_time_minutes']:.1f} minutes")
        print(f"Throughput: {summary['interviews_per_minute']:.1f} interviews/minute")
        print(f"Average coverage: {summary['avg_turn_coverage']:.1f}%")
        print(f"Cost per interview: ${summary['avg_cost_per_interview']:.4f}")
        
        # Success criteria
        time_ok = summary['total_time_minutes'] <= 15
        cost_ok = summary['total_cost'] <= 0.30
        success_ok = summary['success_rate'] >= 95
        coverage_ok = summary['avg_turn_coverage'] >= 95
        
        if time_ok and cost_ok and success_ok and coverage_ok:
            print(f"\n✅ PRODUCTION SUCCESS!")
            print(f"   ⚡ Completed in {summary['total_time_minutes']:.1f} minutes")
            print(f"   💰 Total cost: ${summary['total_cost']:.4f}")
            print(f"   🎯 {summary['avg_turn_coverage']:.1f}% average turn coverage")
            print(f"   📊 {summary['success_rate']:.1f}% success rate")
        else:
            print(f"\n⚠️  Production completed with issues:")
            if not time_ok: print(f"   ⏱️  Time: {summary['total_time_minutes']:.1f}min (target: ≤15min)")
            if not cost_ok: print(f"   💰 Cost: ${summary['total_cost']:.4f} (target: ≤$0.30)")
            if not success_ok: print(f"   📊 Success: {summary['success_rate']:.1f}% (target: ≥95%)")
            if not coverage_ok: print(f"   🎯 Coverage: {summary['avg_turn_coverage']:.1f}% (target: ≥95%)")
        
        return True
        
    except Exception as e:
        print(f"❌ Final production failed: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)