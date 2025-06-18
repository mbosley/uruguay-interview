#!/usr/bin/env python3
"""
Optimized batch annotation script for maximum throughput.
Uses high concurrency with smart batching and minimal latency.
"""
import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import traceback
from dataclasses import dataclass, field
from threading import Lock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.pipeline.annotation.multipass_annotator import MultiPassAnnotator
from src.pipeline.ingestion.document_processor import DocumentProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('optimized_annotation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class FastJobTracker:
    """Ultra-fast job tracking with minimal overhead."""
    total: int = 0
    completed: int = 0
    failed: int = 0
    total_cost: float = 0.0
    start_time: Optional[datetime] = None
    completed_jobs: List[str] = field(default_factory=list)
    lock: Lock = field(default_factory=Lock)
    
    def complete_job(self, job_id: str, cost: float):
        with self.lock:
            self.completed += 1
            self.total_cost += cost
            self.completed_jobs.append(job_id)
    
    def fail_job(self):
        with self.lock:
            self.failed += 1
    
    def get_status(self) -> Dict[str, Any]:
        with self.lock:
            elapsed = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
            rate = self.completed / elapsed if elapsed > 0 else 0
            remaining = self.total - self.completed - self.failed
            eta = remaining / rate if rate > 0 else 0
            
            return {
                'completed': self.completed,
                'failed': self.failed,
                'remaining': remaining,
                'total_cost': self.total_cost,
                'rate_per_min': rate * 60,
                'eta_minutes': eta / 60,
                'success_rate': (self.completed / max(self.completed + self.failed, 1)) * 100
            }


class OptimizedBatchProcessor:
    """Ultra-fast batch processor optimized for maximum throughput."""
    
    def __init__(self, 
                 budget_limit: float = 1.00,
                 max_concurrent: int = 8,  # Higher concurrency
                 batch_interviews: bool = True):
        """
        Initialize optimized processor.
        
        Args:
            budget_limit: Maximum cost limit
            max_concurrent: Max concurrent jobs (higher for speed)
            batch_interviews: Whether to process multiple small interviews together
        """
        self.budget_limit = budget_limit
        self.max_concurrent = max_concurrent
        self.batch_interviews = batch_interviews
        
        # Fast tracking
        self.tracker = FastJobTracker()
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        # Shared components
        self.document_processor = DocumentProcessor()
        
        # Output setup
        self.output_dir = Path("data/processed/annotations/optimized")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"🚀 Optimized processor: {max_concurrent} workers, ${budget_limit} budget")
    
    def discover_and_group_interviews(self) -> List[List[Path]]:
        """Discover interviews and group them for batch processing."""
        txt_dir = Path("data/processed/interviews_txt")
        txt_files = list(txt_dir.glob("*.txt"))
        txt_files.sort()
        
        if not self.batch_interviews:
            return [[f] for f in txt_files]  # Each interview separate
        
        # Group by estimated processing time
        groups = []
        current_group = []
        current_group_words = 0
        max_group_words = 15000  # ~2-3 interviews per group
        
        for txt_file in txt_files:
            try:
                interview = self.document_processor.process_interview(txt_file)
                word_count = len(interview.text.split())
                
                if current_group_words + word_count > max_group_words and current_group:
                    groups.append(current_group)
                    current_group = [txt_file]
                    current_group_words = word_count
                else:
                    current_group.append(txt_file)
                    current_group_words += word_count
                    
            except Exception as e:
                logger.warning(f"Failed to process {txt_file}: {e}")
                # Add as single item
                if current_group:
                    groups.append(current_group)
                groups.append([txt_file])
                current_group = []
                current_group_words = 0
        
        if current_group:
            groups.append(current_group)
        
        total_interviews = sum(len(group) for group in groups)
        logger.info(f"📦 Grouped {total_interviews} interviews into {len(groups)} batches")
        return groups
    
    async def process_interview_group(self, group: List[Path], group_id: int) -> List[Dict[str, Any]]:
        """Process a group of interviews with a single annotator instance."""
        async with self.semaphore:
            results = []
            group_start = time.time()
            
            # Create single annotator for this group
            annotator = MultiPassAnnotator(
                model_name="gpt-4.1-nano",
                temperature=0.1,
                turns_per_batch=6
            )
            
            logger.info(f"[Group {group_id}] Starting {len(group)} interviews")
            
            for i, interview_path in enumerate(group):
                start_time = time.time()
                result = {
                    'group_id': group_id,
                    'file_path': str(interview_path),
                    'interview_id': None,
                    'success': False,
                    'cost': 0.0,
                    'processing_time': 0.0,
                    'error': None
                }
                
                try:
                    # Check budget
                    status = self.tracker.get_status()
                    if status['total_cost'] >= self.budget_limit:
                        result['error'] = f"Budget limit ${self.budget_limit} reached"
                        self.tracker.fail_job()
                        results.append(result)
                        continue
                    
                    # Load and process interview
                    interview = self.document_processor.process_interview(interview_path)
                    result['interview_id'] = interview.id
                    
                    word_count = len(interview.text.split())
                    
                    # Multi-pass annotation
                    annotation_data, metadata = await annotator.annotate_interview(interview)
                    
                    # Record results
                    actual_cost = metadata['total_cost']
                    result['cost'] = actual_cost
                    result['processing_time'] = time.time() - start_time
                    result['turn_coverage'] = metadata['turn_coverage']
                    
                    # Quick quality check
                    coverage_pct = metadata['turn_coverage']['coverage_percentage']
                    quality_ok = coverage_pct >= 95
                    
                    # Save annotation
                    annotation_file = self.output_dir / f"{interview.id}_optimized_annotation.json"
                    with open(annotation_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            "annotation_data": annotation_data,
                            "processing_metadata": metadata,
                            "optimization_info": {
                                "group_id": group_id,
                                "processed_at": datetime.now().isoformat(),
                                "word_count": word_count,
                                "quality_ok": quality_ok,
                                "script_version": "optimized_v1.0"
                            }
                        }, f, indent=2, ensure_ascii=False)
                    
                    result['success'] = True
                    self.tracker.complete_job(interview.id, actual_cost)
                    
                    logger.info(f"[Group {group_id}] ✅ {interview.id}: {coverage_pct:.0f}% coverage, ${actual_cost:.4f}, {result['processing_time']:.1f}s")
                    
                except Exception as e:
                    result['error'] = str(e)
                    result['processing_time'] = time.time() - start_time
                    self.tracker.fail_job()
                    
                    logger.error(f"[Group {group_id}] ❌ {interview_path.name}: {e}")
                
                results.append(result)
            
            group_time = time.time() - group_start
            logger.info(f"[Group {group_id}] Completed {len(group)} interviews in {group_time:.1f}s")
            
            return results
    
    async def process_all_interviews(self) -> Dict[str, Any]:
        """Process all interviews with maximum speed."""
        logger.info("🚀 Starting optimized batch annotation")
        
        # Discover and group interviews
        interview_groups = self.discover_and_group_interviews()
        total_interviews = sum(len(group) for group in interview_groups)
        
        self.tracker.total = total_interviews
        self.tracker.start_time = datetime.now()
        
        logger.info(f"⚡ Processing {total_interviews} interviews in {len(interview_groups)} groups with {self.max_concurrent} workers")
        
        # Create tasks for all groups
        tasks = []
        for i, group in enumerate(interview_groups):
            task = asyncio.create_task(
                self.process_interview_group(group, i + 1)
            )
            tasks.append(task)
        
        # Start monitoring
        monitor_task = asyncio.create_task(self.monitor_progress())
        
        # Wait for all processing to complete
        all_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Stop monitoring
        monitor_task.cancel()
        
        # Flatten results
        final_results = []
        for group_results in all_results:
            if isinstance(group_results, Exception):
                logger.error(f"Group failed: {group_results}")
                continue
            final_results.extend(group_results)
        
        # Generate final report
        return self.generate_final_report(final_results, total_interviews)
    
    async def monitor_progress(self):
        """Monitor progress with minimal overhead."""
        while True:
            await asyncio.sleep(15)  # Update every 15 seconds
            
            status = self.tracker.get_status()
            
            if status['remaining'] <= 0:
                break
            
            logger.info(
                f"📊 Progress: {status['completed']}/{self.tracker.total} | "
                f"${status['total_cost']:.3f} | "
                f"{status['rate_per_min']:.1f}/min | "
                f"ETA: {status['eta_minutes']:.1f}min"
            )
    
    def generate_final_report(self, results: List[Dict], total_interviews: int) -> Dict[str, Any]:
        """Generate comprehensive final report."""
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        total_time = (datetime.now() - self.tracker.start_time).total_seconds()
        
        # Calculate quality metrics
        total_turns = sum(r.get('turn_coverage', {}).get('total_turns', 0) for r in successful)
        analyzed_turns = sum(r.get('turn_coverage', {}).get('analyzed_turns', 0) for r in successful)
        
        report = {
            "optimization_summary": {
                "total_interviews": total_interviews,
                "successful": len(successful),
                "failed": len(failed),
                "success_rate": (len(successful) / total_interviews) * 100,
                "total_cost": self.tracker.total_cost,
                "total_time_minutes": total_time / 60,
                "interviews_per_minute": len(successful) / (total_time / 60),
                "avg_cost_per_interview": self.tracker.total_cost / max(len(successful), 1),
                "concurrency_used": self.max_concurrent
            },
            "quality_metrics": {
                "total_turns_analyzed": analyzed_turns,
                "overall_coverage_rate": (analyzed_turns / total_turns) * 100 if total_turns > 0 else 0,
                "perfect_coverage_count": sum(1 for r in successful if r.get('turn_coverage', {}).get('coverage_percentage', 0) >= 99)
            },
            "detailed_results": results,
            "timestamp": datetime.now().isoformat(),
            "system_info": {
                "approach": "optimized_batch_parallel",
                "max_concurrent": self.max_concurrent,
                "script_version": "optimized_v1.0"
            }
        }
        
        # Save report
        report_file = self.output_dir / f"optimized_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return report


async def main():
    """Main optimized processing function."""
    logger.info("🎯 URUGUAY INTERVIEWS - OPTIMIZED BATCH PROCESSING")
    logger.info("Maximum throughput with smart batching and high concurrency")
    
    try:
        # Create optimized processor
        processor = OptimizedBatchProcessor(
            budget_limit=1.00,
            max_concurrent=8,  # Higher concurrency for speed
            batch_interviews=True  # Group related interviews
        )
        
        # Process all interviews
        report = await processor.process_all_interviews()
        
        # Print results
        summary = report['optimization_summary']
        quality = report['quality_metrics']
        
        print(f"\n" + "="*70)
        print(f"🎯 OPTIMIZED PROCESSING COMPLETE")
        print(f"="*70)
        print(f"Interviews processed: {summary['successful']}/{summary['total_interviews']}")
        print(f"Success rate: {summary['success_rate']:.1f}%")
        print(f"Total cost: ${summary['total_cost']:.4f}")
        print(f"Processing time: {summary['total_time_minutes']:.1f} minutes")
        print(f"Throughput: {summary['interviews_per_minute']:.1f} interviews/minute")
        print(f"Concurrency: {summary['concurrency_used']} workers")
        
        print(f"\n🎯 Quality Metrics:")
        print(f"Total turns analyzed: {quality['total_turns_analyzed']:,}")
        print(f"Overall coverage: {quality['overall_coverage_rate']:.1f}%")
        print(f"Perfect coverage: {quality['perfect_coverage_count']}/{summary['successful']}")
        
        # Success criteria
        if (summary['success_rate'] >= 95 and 
            summary['total_cost'] <= 0.30 and 
            summary['total_time_minutes'] <= 15):
            print(f"\n✅ OPTIMIZATION SUCCESS!")
            print(f"   ⚡ {summary['interviews_per_minute']:.1f} interviews/minute")
            print(f"   💰 ${summary['avg_cost_per_interview']:.4f} per interview")
            print(f"   🎯 {quality['overall_coverage_rate']:.1f}% turn coverage")
        else:
            print(f"\n⚠️  Processing completed - check metrics")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Optimized processing failed: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Run optimized processing
    success = asyncio.run(main())
    sys.exit(0 if success else 1)