#!/usr/bin/env python3
"""
Production batch annotation script for all Uruguay interviews.
Uses parallel async processing with dynamic backoff for optimal performance.
"""
import asyncio
import json
import logging
import sys
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import traceback
from dataclasses import dataclass
from threading import Lock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.pipeline.annotation.multipass_annotator import MultiPassAnnotator
from src.pipeline.ingestion.document_processor import DocumentProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('production_annotation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class JobProgress:
    """Thread-safe job progress tracking."""
    total_jobs: int = 0
    completed: int = 0
    failed: int = 0
    in_progress: int = 0
    total_cost: float = 0.0
    start_time: Optional[datetime] = None
    lock: Lock = Lock()
    
    def start_job(self):
        with self.lock:
            self.in_progress += 1
    
    def complete_job(self, cost: float):
        with self.lock:
            self.in_progress -= 1
            self.completed += 1
            self.total_cost += cost
    
    def fail_job(self):
        with self.lock:
            self.in_progress -= 1
            self.failed += 1
    
    def get_status(self) -> Dict[str, Any]:
        with self.lock:
            elapsed = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
            return {
                'total': self.total_jobs,
                'completed': self.completed,
                'failed': self.failed,
                'in_progress': self.in_progress,
                'total_cost': self.total_cost,
                'success_rate': (self.completed / max(self.completed + self.failed, 1)) * 100,
                'avg_cost': self.total_cost / max(self.completed, 1),
                'elapsed_time': elapsed,
                'estimated_remaining': (elapsed / max(self.completed, 1)) * (self.total_jobs - self.completed - self.failed) if self.completed > 0 else 0
            }


class RateLimitManager:
    """Dynamic backoff and rate limiting manager."""
    
    def __init__(self, base_delay: float = 1.0, max_delay: float = 60.0):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.consecutive_rate_limits = 0
        self.last_rate_limit = None
        self.lock = Lock()
    
    def is_rate_limit_error(self, error: Exception) -> bool:
        """Check if error is a rate limit error."""
        error_str = str(error).lower()
        return '429' in error_str or 'rate limit' in error_str or 'too many requests' in error_str
    
    async def handle_rate_limit(self):
        """Handle rate limit with exponential backoff + jitter."""
        with self.lock:
            self.consecutive_rate_limits += 1
            self.last_rate_limit = datetime.now()
        
        # Exponential backoff with jitter
        delay = min(self.base_delay * (2 ** self.consecutive_rate_limits), self.max_delay)
        jitter = random.uniform(0, delay * 0.1)  # Add up to 10% jitter
        total_delay = delay + jitter
        
        logger.warning(f"Rate limit detected. Backing off for {total_delay:.1f}s (attempt {self.consecutive_rate_limits})")
        await asyncio.sleep(total_delay)
    
    def reset_rate_limit_counter(self):
        """Reset rate limit counter on successful request."""
        with self.lock:
            if self.consecutive_rate_limits > 0:
                logger.info(f"Rate limit recovery - resetting counter from {self.consecutive_rate_limits}")
                self.consecutive_rate_limits = 0
    
    def should_delay_request(self) -> bool:
        """Check if we should delay before making a request."""
        with self.lock:
            if self.last_rate_limit and self.consecutive_rate_limits > 0:
                # Still in backoff period
                elapsed = (datetime.now() - self.last_rate_limit).total_seconds()
                backoff_period = self.base_delay * (2 ** max(0, self.consecutive_rate_limits - 1))
                return elapsed < backoff_period
            return False
    
    async def wait_if_needed(self):
        """Wait if we're still in a backoff period."""
        if self.should_delay_request():
            with self.lock:
                elapsed = (datetime.now() - self.last_rate_limit).total_seconds()
                backoff_period = self.base_delay * (2 ** max(0, self.consecutive_rate_limits - 1))
                remaining = backoff_period - elapsed
            
            if remaining > 0:
                logger.info(f"Waiting {remaining:.1f}s for rate limit recovery")
                await asyncio.sleep(remaining)


class ParallelAnnotationProcessor:
    """Parallel async annotation processor with dynamic rate limiting."""
    
    def __init__(self, 
                 budget_limit: float = 1.00, 
                 max_concurrent: int = 4,
                 base_delay: float = 2.0):
        """
        Initialize parallel processor.
        
        Args:
            budget_limit: Maximum allowed cost before stopping
            max_concurrent: Maximum concurrent annotation jobs
            base_delay: Base delay for rate limiting
        """
        self.budget_limit = budget_limit
        self.max_concurrent = max_concurrent
        
        # Thread-safe progress tracking
        self.progress = JobProgress()
        self.rate_limiter = RateLimitManager(base_delay=base_delay)
        
        # Concurrency control
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        # Initialize components (shared document processor)
        self.document_processor = DocumentProcessor()
        
        # Create output directories
        self.output_dir = Path("data/processed/annotations/multipass")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.metadata_dir = self.output_dir / "metadata"
        self.metadata_dir.mkdir(exist_ok=True)
        
        logger.info(f"Parallel processor initialized - Budget: ${budget_limit}, Concurrency: {max_concurrent}")
    
    def discover_interviews(self) -> List[Path]:
        """Discover all interview text files for processing."""
        txt_dir = Path("data/processed/interviews_txt")
        
        if not txt_dir.exists():
            raise FileNotFoundError(f"Interview directory not found: {txt_dir}")
        
        # Find all text files
        txt_files = list(txt_dir.glob("*.txt"))
        txt_files.sort()  # Process in consistent order
        
        logger.info(f"Discovered {len(txt_files)} interview files for processing")
        return txt_files
    
    async def create_annotator(self) -> MultiPassAnnotator:
        """Create a new annotator instance for this job."""
        return MultiPassAnnotator(
            model_name="gpt-4.1-nano",
            temperature=0.1,
            turns_per_batch=6
        )
    
    async def process_single_interview(self, interview_path: Path, job_id: int) -> Dict[str, Any]:
        """
        Process a single interview with rate limiting and parallel safety.
        
        Args:
            interview_path: Path to interview text file
            job_id: Unique job identifier for tracking
            
        Returns:
            Processing result dictionary
        """
        async with self.semaphore:  # Limit concurrent jobs
            start_time = datetime.now()
            result = {
                'job_id': job_id,
                'file_path': str(interview_path),
                'interview_id': None,
                'success': False,
                'cost': 0.0,
                'processing_time': 0.0,
                'error': None,
                'turn_coverage': {},
                'retries': 0
            }
            
            self.progress.start_job()
            
            try:
                # Check budget before processing
                status = self.progress.get_status()
                if status['total_cost'] >= self.budget_limit:
                    raise RuntimeError(f"Budget limit ${self.budget_limit} reached")
                
                # Load interview
                interview = self.document_processor.process_interview(interview_path)
                result['interview_id'] = interview.id
                
                word_count = len(interview.text.split())
                logger.info(f"[Job {job_id}] Processing {interview.id}: {word_count:,} words")
                
                # Create dedicated annotator for this job
                annotator = await self.create_annotator()
                
                # Retry logic with rate limiting
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        # Wait if in rate limit backoff
                        await self.rate_limiter.wait_if_needed()
                        
                        # Multi-pass annotation
                        annotation_data, metadata = await annotator.annotate_interview(interview)
                        
                        # Success - reset rate limit counter
                        self.rate_limiter.reset_rate_limit_counter()
                        break
                        
                    except Exception as e:
                        result['retries'] = attempt + 1
                        
                        if self.rate_limiter.is_rate_limit_error(e):
                            logger.warning(f"[Job {job_id}] Rate limit on attempt {attempt + 1}: {e}")
                            await self.rate_limiter.handle_rate_limit()
                            
                            if attempt < max_retries - 1:
                                continue  # Retry
                            else:
                                raise  # Final attempt failed
                        else:
                            logger.error(f"[Job {job_id}] Non-rate-limit error on attempt {attempt + 1}: {e}")
                            raise  # Don't retry non-rate-limit errors
                
                # Process results
                actual_cost = metadata['total_cost']
                result['cost'] = actual_cost
                result['turn_coverage'] = metadata['turn_coverage']
                result['processing_time'] = (datetime.now() - start_time).total_seconds()
                
                # Validate quality
                quality_check = self._validate_annotation_quality(annotation_data, metadata)
                if not quality_check['passed']:
                    logger.warning(f"[Job {job_id}] Quality issues: {quality_check['issues'][:2]}...")  # Truncate for readability
                
                # Save annotation
                annotation_file = self.output_dir / f"{interview.id}_multipass_annotation.json"
                with open(annotation_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        "annotation_data": annotation_data,
                        "processing_metadata": metadata,
                        "quality_validation": quality_check,
                        "production_info": {
                            "job_id": job_id,
                            "processed_at": datetime.now().isoformat(),
                            "script_version": "parallel_v2.0",
                            "retries_needed": result['retries']
                        }
                    }, f, indent=2, ensure_ascii=False)
                
                # Save processing metadata
                metadata_file = self.metadata_dir / f"{interview.id}_processing.json"
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        **metadata,
                        "job_id": job_id,
                        "file_path": str(interview_path),
                        "quality_validation": quality_check,
                        "production_timestamp": datetime.now().isoformat(),
                        "retries_needed": result['retries']
                    }, f, indent=2, ensure_ascii=False)
                
                result['success'] = True
                self.progress.complete_job(actual_cost)
                
                logger.info(f"[Job {job_id}] ✅ {metadata['turn_coverage']['analyzed_turns']}/{metadata['turn_coverage']['total_turns']} turns, ${actual_cost:.4f}")
                
            except Exception as e:
                result['error'] = str(e)
                result['processing_time'] = (datetime.now() - start_time).total_seconds()
                self.progress.fail_job()
                
                logger.error(f"[Job {job_id}] ❌ Failed {interview_path.name}: {e}")
                
                # Save error details
                if result['interview_id']:
                    error_file = self.metadata_dir / f"{result['interview_id']}_error.json"
                    with open(error_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            "job_id": job_id,
                            "error": str(e),
                            "traceback": traceback.format_exc(),
                            "file_path": str(interview_path),
                            "timestamp": datetime.now().isoformat(),
                            "retries_attempted": result['retries']
                        }, f, indent=2, ensure_ascii=False)
            
            return result
    
    async def monitor_progress(self, total_files: int):
        """Real-time progress monitoring for parallel jobs."""
        while True:
            await asyncio.sleep(10)  # Update every 10 seconds
            
            status = self.progress.get_status()
            
            if status['completed'] + status['failed'] >= total_files:
                break  # All jobs finished
            
            logger.info(
                f"📊 Progress: {status['completed']}/{total_files} completed, "
                f"{status['in_progress']} in progress, {status['failed']} failed | "
                f"${status['total_cost']:.3f} spent | "
                f"{status['success_rate']:.1f}% success | "
                f"ETA: {status['estimated_remaining']/60:.1f}min"
            )
    
    async def process_all_interviews(self) -> Dict[str, Any]:
        """
        Process all discovered interviews with parallel processing.
        
        Returns:
            Complete processing report
        """
        logger.info("🚀 Starting parallel annotation of all interviews")
        logger.info(f"Budget: ${self.budget_limit}, Concurrency: {self.max_concurrent}")
        
        # Discover interviews
        interview_files = self.discover_interviews()
        total_files = len(interview_files)
        
        if total_files == 0:
            raise RuntimeError("No interview files found to process")
        
        # Initialize progress tracking
        self.progress.total_jobs = total_files
        self.progress.start_time = datetime.now()
        
        logger.info(f"Processing {total_files} interviews with {self.max_concurrent} parallel workers")
        
        # Create all job tasks
        tasks = []
        for i, interview_path in enumerate(interview_files):
            task = asyncio.create_task(
                self.process_single_interview(interview_path, job_id=i+1)
            )
            tasks.append(task)
        
        # Start progress monitoring
        monitor_task = asyncio.create_task(self.monitor_progress(total_files))
        
        # Wait for all annotation jobs to complete
        logger.info("⚡ Starting parallel processing...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Cancel monitoring
        monitor_task.cancel()
        
        # Process results and handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Task {i+1} failed with exception: {result}")
                processed_results.append({
                    'job_id': i+1,
                    'success': False,
                    'error': str(result),
                    'file_path': str(interview_files[i]) if i < len(interview_files) else 'unknown'
                })
            else:
                processed_results.append(result)
        
        # Get final status
        final_status = self.progress.get_status()
        total_time = final_status['elapsed_time']
        
        # Create comprehensive report
        report = {
            "production_summary": {
                "total_files_found": total_files,
                "files_processed": len(processed_results),
                "successful": final_status['completed'],
                "failed": final_status['failed'],
                "success_rate": final_status['success_rate'],
                "total_cost": final_status['total_cost'],
                "budget_limit": self.budget_limit,
                "budget_utilization": (final_status['total_cost'] / self.budget_limit) * 100,
                "total_processing_time": total_time,
                "avg_time_per_interview": total_time / max(final_status['completed'], 1),
                "avg_cost_per_interview": final_status['avg_cost'],
                "max_concurrent_jobs": self.max_concurrent,
                "processing_approach": "parallel_async"
            },
            "file_results": processed_results,
            "quality_summary": self._generate_quality_summary(processed_results),
            "rate_limiting": {
                "consecutive_rate_limits_peak": self.rate_limiter.consecutive_rate_limits,
                "last_rate_limit": self.rate_limiter.last_rate_limit.isoformat() if self.rate_limiter.last_rate_limit else None
            },
            "timestamp": datetime.now().isoformat(),
            "system_info": {
                "model": "gpt-4.1-nano",
                "annotation_approach": "multipass_comprehensive_parallel",
                "turns_per_batch": 6,
                "script_version": "parallel_v2.0",
                "max_concurrency": self.max_concurrent
            }
        }
        
        # Save comprehensive report
        report_file = self.output_dir / f"parallel_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n🎯 PARALLEL ANNOTATION COMPLETE")
        logger.info(f"   Processed: {final_status['completed']}/{total_files} interviews")
        logger.info(f"   Total cost: ${final_status['total_cost']:.4f}")
        logger.info(f"   Success rate: {final_status['success_rate']:.1f}%")
        logger.info(f"   Processing time: {total_time/60:.1f} minutes")
        logger.info(f"   Speedup: ~{total_files * 1.5 / (total_time/60):.1f}x vs sequential")
        logger.info(f"   Report saved: {report_file}")
        
        return report
    
    def _estimate_interview_cost(self, word_count: int) -> float:
        """Estimate cost based on word count and multi-pass structure."""
        # Based on validation: ~$0.006 per interview regardless of size
        # Add small buffer for safety
        return 0.008
    
    def _validate_annotation_quality(self, annotation_data: Dict, metadata: Dict) -> Dict[str, Any]:
        """Validate annotation quality against production standards."""
        issues = []
        
        # Check turn coverage (must be 100%)
        coverage_pct = metadata['turn_coverage']['coverage_percentage']
        if coverage_pct < 100:
            issues.append(f"Turn coverage only {coverage_pct:.1f}% (expected 100%)")
        
        # Check overall confidence
        overall_confidence = annotation_data.get('annotation_metadata', {}).get('overall_confidence', 0)
        if overall_confidence < 0.7:
            issues.append(f"Low overall confidence: {overall_confidence}")
        
        # Check for required data sections
        required_sections = ['priority_analysis', 'conversation_analysis', 'narrative_features']
        for section in required_sections:
            if section not in annotation_data:
                issues.append(f"Missing required section: {section}")
        
        # Check priorities
        national_priorities = annotation_data.get('priority_analysis', {}).get('national_priorities', [])
        local_priorities = annotation_data.get('priority_analysis', {}).get('local_priorities', [])
        
        if len(national_priorities) < 3:
            issues.append(f"Insufficient national priorities: {len(national_priorities)} (expected 3)")
        
        if len(local_priorities) < 3:
            issues.append(f"Insufficient local priorities: {len(local_priorities)} (expected 3)")
        
        return {
            "passed": len(issues) == 0,
            "issues": issues,
            "quality_score": 1.0 if len(issues) == 0 else max(0.0, 1.0 - (len(issues) * 0.2)),
            "validation_timestamp": datetime.now().isoformat()
        }
    
    def _generate_quality_summary(self, results: List[Dict]) -> Dict[str, Any]:
        """Generate quality summary across all processed interviews."""
        successful_results = [r for r in results if r['success']]
        
        if not successful_results:
            return {"error": "No successful annotations to analyze"}
        
        # Calculate quality metrics
        total_turns = sum(r['turn_coverage'].get('total_turns', 0) for r in successful_results)
        analyzed_turns = sum(r['turn_coverage'].get('analyzed_turns', 0) for r in successful_results)
        
        coverage_rates = [r['turn_coverage'].get('coverage_percentage', 0) for r in successful_results]
        
        return {
            "total_interviews_analyzed": len(successful_results),
            "total_conversation_turns": total_turns,
            "total_turns_analyzed": analyzed_turns,
            "overall_coverage_rate": (analyzed_turns / total_turns) * 100 if total_turns > 0 else 0,
            "perfect_coverage_interviews": sum(1 for rate in coverage_rates if rate >= 99.9),
            "average_coverage_rate": sum(coverage_rates) / len(coverage_rates) if coverage_rates else 0,
            "min_coverage_rate": min(coverage_rates) if coverage_rates else 0,
            "max_coverage_rate": max(coverage_rates) if coverage_rates else 0
        }


async def main():
    """Main parallel processing function."""
    logger.info("🎯 URUGUAY INTERVIEWS - PARALLEL ANNOTATION")
    logger.info("Multi-pass system with async parallelization and dynamic backoff")
    logger.info("Expected: 100% turn coverage, ~$0.006 per interview, 4x speedup")
    
    try:
        # Create parallel processor
        processor = ParallelAnnotationProcessor(
            budget_limit=1.00,
            max_concurrent=4,  # Adjust based on rate limits
            base_delay=2.0
        )
        
        # Process all interviews in parallel
        report = await processor.process_all_interviews()
        
        # Print final summary
        summary = report['production_summary']
        print(f"\n" + "="*70)
        print(f"🎯 PARALLEL ANNOTATION COMPLETE")
        print(f"="*70)
        print(f"Files processed: {summary['files_processed']}")
        print(f"Successful: {summary['successful']}")
        print(f"Failed: {summary['failed']}")
        print(f"Success rate: {summary['success_rate']:.1f}%")
        print(f"Total cost: ${summary['total_cost']:.4f}")
        print(f"Budget utilization: {summary['budget_utilization']:.1f}%")
        print(f"Processing time: {summary['total_processing_time']/60:.1f} minutes")
        print(f"Average cost per interview: ${summary['avg_cost_per_interview']:.4f}")
        print(f"Concurrency used: {summary['max_concurrent_jobs']} parallel jobs")
        
        # Rate limiting info
        rate_info = report.get('rate_limiting', {})
        if rate_info.get('consecutive_rate_limits_peak', 0) > 0:
            print(f"\n⚡ Rate Limiting:")
            print(f"Max consecutive rate limits: {rate_info['consecutive_rate_limits_peak']}")
            print(f"Last rate limit: {rate_info.get('last_rate_limit', 'None')}")
        
        # Quality summary
        quality = report['quality_summary']
        if 'error' not in quality:
            print(f"\n📊 Quality Summary:")
            print(f"Total turns analyzed: {quality['total_turns_analyzed']:,}")
            print(f"Overall coverage: {quality['overall_coverage_rate']:.1f}%")
            print(f"Perfect coverage interviews: {quality['perfect_coverage_interviews']}/{summary['successful']}")
        
        # Success criteria
        time_minutes = summary['total_processing_time'] / 60
        if (summary['success_rate'] >= 95 and 
            summary['total_cost'] <= 0.30 and 
            time_minutes <= 25):  # Should be much faster with parallelization
            print(f"\n✅ PARALLEL PROCESSING SUCCESS!")
            print(f"   ⚡ Achieved ~{(summary['files_processed'] * 1.5) / time_minutes:.1f}x speedup vs sequential")
            print(f"   💰 Cost efficiency: ${summary['total_cost']:.4f} total")
            print(f"   🎯 Quality: {quality.get('overall_coverage_rate', 0):.1f}% turn coverage")
        else:
            print(f"\n⚠️  Processing completed with issues - Review report")
            if summary['success_rate'] < 95:
                print(f"     Low success rate: {summary['success_rate']:.1f}%")
            if summary['total_cost'] > 0.30:
                print(f"     High cost: ${summary['total_cost']:.4f}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Parallel processing failed: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Run production annotation
    success = asyncio.run(main())
    sys.exit(0 if success else 1)