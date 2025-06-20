#!/usr/bin/env python3
"""
Robust annotation pipeline with resumption and error recovery.
Production-grade implementation for Makefile integration.
"""
import asyncio
import json
import logging
import sys
import argparse
import signal
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Set
import traceback

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.pipeline.annotation.multipass_annotator import MultiPassAnnotator
from src.pipeline.ingestion.document_processor import DocumentProcessor

class RobustAnnotationPipeline:
    """Production-grade annotation pipeline with fault tolerance."""
    
    def __init__(self, 
                 max_workers: int = 6,
                 budget_limit: float = 1.00,
                 output_dir: Path = None,
                 log_file: Path = None):
        """
        Initialize robust pipeline.
        
        Args:
            max_workers: Maximum concurrent workers
            budget_limit: Budget safety limit
            output_dir: Output directory for annotations
            log_file: Log file path
        """
        self.max_workers = max_workers
        self.budget_limit = budget_limit
        self.output_dir = output_dir or Path("data/processed/annotations/production")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.setup_logging(log_file)
        
        # State tracking
        self.total_cost = 0.0
        self.completed_count = 0
        self.failed_count = 0
        self.start_time = None
        self.shutdown_requested = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.logger.info(f"Robust pipeline initialized: {max_workers} workers, ${budget_limit} budget")
    
    def setup_logging(self, log_file: Path = None):
        """Setup comprehensive logging."""
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        handlers = [logging.StreamHandler()]
        if log_file:
            handlers.append(logging.FileHandler(log_file))
        
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=handlers,
            force=True
        )
        
        self.logger = logging.getLogger(__name__)
        
        # Silence noisy libraries
        logging.getLogger('httpx').setLevel(logging.WARNING)
        logging.getLogger('src.pipeline.annotation.multipass_annotator').setLevel(logging.WARNING)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.logger.warning(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_requested = True
    
    def get_completed_interviews(self) -> Set[str]:
        """Get set of already completed interview IDs."""
        completed = set()
        
        for file_path in self.output_dir.glob("*_final_annotation.json"):
            interview_id = file_path.stem.replace("_final_annotation", "")
            completed.add(interview_id)
        
        return completed
    
    def get_pending_interviews(self) -> List[Dict[str, Any]]:
        """Get list of pending interviews with metadata."""
        txt_dir = Path("data/processed/interviews_txt")
        completed = self.get_completed_interviews()
        
        pending = []
        for txt_file in txt_dir.glob("*.txt"):
            # Extract interview ID
            parts = txt_file.stem.split("_")
            interview_id = parts[2] if len(parts) >= 3 else txt_file.stem
            
            if interview_id not in completed:
                # Get file metadata
                try:
                    with open(txt_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    word_count = len(content.split())
                except Exception as e:
                    self.logger.warning(f"Could not read {txt_file}: {e}")
                    word_count = 0
                
                pending.append({
                    'interview_id': interview_id,
                    'file_path': txt_file,
                    'word_count': word_count,
                    'estimated_difficulty': self.estimate_difficulty(word_count)
                })
        
        # Sort by difficulty (easiest first for faster initial progress)
        pending.sort(key=lambda x: x['word_count'])
        return pending
    
    def estimate_difficulty(self, word_count: int) -> str:
        """Estimate processing difficulty."""
        if word_count < 3000:
            return "easy"
        elif word_count < 6000:
            return "medium"
        elif word_count < 10000:
            return "hard"
        else:
            return "very_hard"
    
    async def process_single_interview(self, interview_info: Dict[str, Any], job_id: int) -> Dict[str, Any]:
        """Process one interview with comprehensive error handling."""
        start_time = time.time()
        interview_id = interview_info['interview_id']
        file_path = interview_info['file_path']
        
        result = {
            'job_id': job_id,
            'interview_id': interview_id,
            'file_path': str(file_path),
            'success': False,
            'cost': 0.0,
            'processing_time': 0.0,
            'turn_coverage': 0,
            'error': None,
            'retry_count': 0
        }
        
        # Check for shutdown
        if self.shutdown_requested:
            result['error'] = "Shutdown requested"
            return result
        
        # Budget check
        if self.total_cost >= self.budget_limit:
            result['error'] = f"Budget limit ${self.budget_limit} reached"
            return result
        
        try:
            self.logger.info(f"[{job_id:2d}] Starting {interview_id} ({interview_info['word_count']:,} words)")
            
            # Load interview
            processor = DocumentProcessor()
            interview = processor.process_interview(file_path)
            
            # Create annotator
            annotator = MultiPassAnnotator(
                model_name="gpt-4.1-nano",
                temperature=0.1,
                turns_per_batch=6
            )
            
            # Retry logic
            max_retries = 3
            for attempt in range(max_retries):
                if self.shutdown_requested:
                    result['error'] = "Shutdown requested during processing"
                    return result
                
                try:
                    # Annotate with timeout
                    annotation_data, metadata = await asyncio.wait_for(
                        annotator.annotate_interview(interview),
                        timeout=300  # 5 minute timeout per interview
                    )
                    
                    # Success
                    result['cost'] = metadata['total_cost']
                    result['processing_time'] = time.time() - start_time
                    result['turn_coverage'] = metadata['turn_coverage']['coverage_percentage']
                    result['api_calls'] = metadata['total_api_calls']
                    result['retry_count'] = attempt
                    
                    # Save annotation
                    output_file = self.output_dir / f"{interview_id}_final_annotation.json"
                    annotation_output = {
                        "annotation_data": annotation_data,
                        "processing_metadata": metadata,
                        "production_info": {
                            "job_id": job_id,
                            "processed_at": datetime.now().isoformat(),
                            "processing_time": result['processing_time'],
                            "retry_count": attempt,
                            "pipeline_version": "robust_v1.0"
                        }
                    }
                    
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(annotation_output, f, indent=2, ensure_ascii=False)
                    
                    result['success'] = True
                    self.total_cost += result['cost']
                    self.completed_count += 1
                    
                    self.logger.info(
                        f"[{job_id:2d}] ✅ {interview_id}: "
                        f"{result['turn_coverage']:.0f}% coverage, "
                        f"${result['cost']:.4f}, "
                        f"{result['processing_time']:.1f}s"
                    )
                    break
                    
                except asyncio.TimeoutError:
                    self.logger.warning(f"[{job_id:2d}] Timeout on attempt {attempt + 1} for {interview_id}")
                    if attempt == max_retries - 1:
                        result['error'] = "Annotation timed out after retries"
                    else:
                        await asyncio.sleep(5)  # Brief delay before retry
                        continue
                        
                except Exception as e:
                    error_msg = str(e)
                    self.logger.warning(f"[{job_id:2d}] Error on attempt {attempt + 1} for {interview_id}: {error_msg}")
                    
                    # Check if it's a rate limit or recoverable error
                    if "rate limit" in error_msg.lower() or "429" in error_msg:
                        if attempt < max_retries - 1:
                            delay = (2 ** attempt) + 5  # Exponential backoff
                            self.logger.info(f"Rate limit detected, waiting {delay}s before retry...")
                            await asyncio.sleep(delay)
                            continue
                    
                    if attempt == max_retries - 1:
                        result['error'] = f"Failed after {max_retries} attempts: {error_msg}"
                    
        except Exception as e:
            result['error'] = f"Fatal error: {str(e)}"
            self.logger.error(f"[{job_id:2d}] Fatal error for {interview_id}: {e}")
        
        if not result['success']:
            result['processing_time'] = time.time() - start_time
            self.failed_count += 1
            self.logger.error(f"[{job_id:2d}] ❌ {interview_id}: {result['error']}")
        
        return result
    
    async def run_annotation_pipeline(self) -> Dict[str, Any]:
        """Run the complete annotation pipeline."""
        self.start_time = time.time()
        self.logger.info("🚀 Starting robust annotation pipeline")
        
        # Get pending interviews
        pending_interviews = self.get_pending_interviews()
        total_pending = len(pending_interviews)
        
        if total_pending == 0:
            self.logger.info("✅ No pending interviews - all annotations complete")
            return {"status": "complete", "message": "No work remaining"}
        
        self.logger.info(f"📄 Found {total_pending} pending interviews")
        
        # Estimate costs and time
        estimated_cost = total_pending * 0.010
        estimated_time = total_pending * 1.5 / self.max_workers
        
        self.logger.info(f"📊 Estimates: ${estimated_cost:.2f} cost, {estimated_time:.1f} min with {self.max_workers} workers")
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def controlled_process(interview_info, job_id):
            async with semaphore:
                return await self.process_single_interview(interview_info, job_id)
        
        # Start progress monitoring
        monitor_task = asyncio.create_task(self.monitor_progress(total_pending))
        
        # Create and run all tasks
        tasks = []
        for i, interview_info in enumerate(pending_interviews):
            if self.shutdown_requested:
                break
            
            task = asyncio.create_task(
                controlled_process(interview_info, i + 1)
            )
            tasks.append(task)
        
        # Wait for completion or shutdown
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            self.logger.error(f"Pipeline execution error: {e}")
            results = []
        finally:
            monitor_task.cancel()
        
        # Process results
        successful_results = []
        failed_results = []
        
        for result in results:
            if isinstance(result, Exception):
                failed_results.append({'error': str(result)})
            elif isinstance(result, dict):
                if result.get('success'):
                    successful_results.append(result)
                else:
                    failed_results.append(result)
        
        # Generate summary
        total_time = time.time() - self.start_time
        
        summary = {
            "pipeline_summary": {
                "total_pending": total_pending,
                "successful": len(successful_results),
                "failed": len(failed_results),
                "success_rate": (len(successful_results) / total_pending) * 100 if total_pending > 0 else 0,
                "total_cost": self.total_cost,
                "total_time_minutes": total_time / 60,
                "shutdown_requested": self.shutdown_requested
            },
            "detailed_results": successful_results + failed_results,
            "timestamp": datetime.now().isoformat()
        }
        
        # Save summary
        summary_file = self.output_dir / f"pipeline_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"📊 Pipeline complete: {len(successful_results)}/{total_pending} successful, ${self.total_cost:.4f} cost")
        
        return summary
    
    async def monitor_progress(self, total_pending: int):
        """Monitor and log progress."""
        while not self.shutdown_requested:
            await asyncio.sleep(30)  # Update every 30 seconds
            
            elapsed = time.time() - self.start_time
            rate = self.completed_count / elapsed if elapsed > 0 else 0
            remaining = total_pending - self.completed_count - self.failed_count
            eta = remaining / rate if rate > 0 else 0
            
            self.logger.info(
                f"📊 Progress: {self.completed_count}/{total_pending} done, "
                f"{self.failed_count} failed | "
                f"${self.total_cost:.3f} | "
                f"{rate * 60:.1f}/min | "
                f"ETA: {eta / 60:.1f}min"
            )
            
            if remaining <= 0:
                break

def main():
    """Main function with argument parsing."""
    parser = argparse.ArgumentParser(description="Robust annotation pipeline")
    parser.add_argument("--max-workers", type=int, default=6, help="Maximum concurrent workers")
    parser.add_argument("--budget-limit", type=float, default=1.00, help="Budget limit in dollars")
    parser.add_argument("--output-dir", type=Path, help="Output directory")
    parser.add_argument("--log-file", type=Path, help="Log file path")
    
    args = parser.parse_args()
    
    # Create pipeline
    pipeline = RobustAnnotationPipeline(
        max_workers=args.max_workers,
        budget_limit=args.budget_limit,
        output_dir=args.output_dir,
        log_file=args.log_file
    )
    
    try:
        # Run pipeline
        summary = asyncio.run(pipeline.run_annotation_pipeline())
        
        # Print final status
        pipeline_summary = summary.get("pipeline_summary", {})
        success_rate = pipeline_summary.get("success_rate", 0)
        
        if success_rate >= 95:
            print("✅ Pipeline completed successfully")
            return True
        else:
            print(f"⚠️  Pipeline completed with {success_rate:.1f}% success rate")
            return False
            
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)