#!/usr/bin/env python3
"""
Production annotation script with MFT (6 dimensions).
This replaces the old annotation script to include moral foundations.
"""

import asyncio
import argparse
import json
import logging
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.pipeline.ingestion.document_processor import DocumentProcessor
from src.pipeline.annotation.multipass_annotator import MultiPassAnnotator
from src.pipeline.annotation.moral_foundations_analyzer import MoralFoundationsAnalyzer
from src.database.connection import get_db_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/production_mft_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ProductionAnnotator:
    """Production annotation with MFT integrated."""
    
    def __init__(self, max_workers=4, budget_limit=1.0, output_dir=None):
        self.max_workers = max_workers
        self.budget_limit = budget_limit
        self.output_dir = Path(output_dir or "data/processed/annotations/production")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.total_cost = 0.0
        self.processed_count = 0
        self.failed_interviews = []
        
    async def process_interview(self, file_path: Path) -> dict:
        """Process a single interview with MFT annotation."""
        interview_id = file_path.stem
        output_file = self.output_dir / f"{interview_id}_final_annotation.json"
        
        # Skip if already processed
        if output_file.exists():
            logger.info(f"Skipping {interview_id} - already processed")
            return {'status': 'skipped', 'interview_id': interview_id}
        
        # Check budget
        if self.total_cost >= self.budget_limit:
            logger.warning(f"Budget limit reached (${self.total_cost:.2f})")
            return {'status': 'budget_exceeded', 'interview_id': interview_id}
        
        try:
            # Load interview
            processor = DocumentProcessor()
            interview = processor.process_interview(file_path)
            
            # Create annotator with MFT support
            annotator = MultiPassAnnotator(
                model_name="gpt-4o-mini",
                temperature=0.1,
                turns_per_batch=6
            )
            
            # Run annotation
            logger.info(f"Annotating {interview_id} with 6 dimensions (including MFT)...")
            start_time = time.time()
            annotation_data, metadata = await annotator.annotate_interview(interview)
            processing_time = time.time() - start_time
            
            # Update cost tracking
            self.total_cost += metadata['total_cost']
            self.processed_count += 1
            
            # Add MFT summary to metadata
            turns = annotation_data['conversation_analysis']['turns']
            mft_count = sum(1 for t in turns 
                          if t.get('moral_foundations_analysis', {}).get('dominant_foundation', 'none') != 'none')
            metadata['mft_turns'] = mft_count
            metadata['dimensions_analyzed'] = 6  # Including MFT
            
            # Save to file
            output_data = {
                'interview_id': interview_id,
                'annotation_data': annotation_data,
                'metadata': metadata,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            # Store in database
            self._store_in_database(interview_id, annotation_data)
            
            logger.info(f"✓ Completed {interview_id} in {processing_time:.1f}s (${metadata['total_cost']:.4f}, {mft_count} MFT turns)")
            
            return {
                'status': 'success',
                'interview_id': interview_id,
                'cost': metadata['total_cost'],
                'time': processing_time,
                'mft_turns': mft_count
            }
            
        except Exception as e:
            logger.error(f"Failed to process {interview_id}: {str(e)}")
            self.failed_interviews.append(interview_id)
            return {
                'status': 'failed',
                'interview_id': interview_id,
                'error': str(e)
            }
    
    def _store_in_database(self, interview_id: str, annotation_data: dict):
        """Store annotation data including MFT in database."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Store turn-level MFT data
            turns = annotation_data['conversation_analysis']['turns']
            for turn in turns:
                if 'moral_foundations_analysis' not in turn:
                    continue
                
                # Get turn ID from database
                cursor.execute("""
                    SELECT id FROM turns 
                    WHERE interview_id = ? AND turn_number = ?
                """, (interview_id, turn['turn_id']))
                
                result = cursor.fetchone()
                if not result:
                    continue
                
                turn_db_id = result[0]
                mft = turn['moral_foundations_analysis']
                
                # Insert MFT data
                cursor.execute("""
                    INSERT OR REPLACE INTO turn_moral_foundations (
                        turn_id, reasoning, care_harm, fairness_cheating,
                        loyalty_betrayal, authority_subversion, sanctity_degradation,
                        liberty_oppression, dominant_foundation, foundations_narrative,
                        mft_confidence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    turn_db_id,
                    mft.get('reasoning', ''),
                    mft.get('care_harm', 0.0),
                    mft.get('fairness_cheating', 0.0),
                    mft.get('loyalty_betrayal', 0.0),
                    mft.get('authority_subversion', 0.0),
                    mft.get('sanctity_degradation', 0.0),
                    mft.get('liberty_oppression', 0.0),
                    mft.get('dominant_foundation', 'none'),
                    mft.get('foundations_narrative', ''),
                    mft.get('mft_confidence', 0.0)
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Database storage error for {interview_id}: {e}")
    
    async def run(self):
        """Run production annotation on all interviews."""
        # Get all interview files
        txt_dir = project_root / "data" / "processed" / "interviews_txt"
        interview_files = sorted(txt_dir.glob("*.txt"))
        
        logger.info(f"Starting production annotation with MFT")
        logger.info(f"Found {len(interview_files)} interviews")
        logger.info(f"Budget limit: ${self.budget_limit}")
        logger.info(f"Max workers: {self.max_workers}")
        
        # Process interviews
        tasks = []
        for file_path in interview_files:
            task = self.process_interview(file_path)
            tasks.append(task)
        
        # Run with concurrency limit
        results = []
        for i in range(0, len(tasks), self.max_workers):
            batch = tasks[i:i + self.max_workers]
            batch_results = await asyncio.gather(*batch)
            results.extend(batch_results)
            
            # Check budget after each batch
            if self.total_cost >= self.budget_limit:
                logger.warning(f"Budget limit reached after {self.processed_count} interviews")
                break
        
        # Summary
        successful = [r for r in results if r['status'] == 'success']
        skipped = [r for r in results if r['status'] == 'skipped']
        failed = [r for r in results if r['status'] == 'failed']
        
        logger.info("\n" + "="*60)
        logger.info("PRODUCTION ANNOTATION SUMMARY")
        logger.info("="*60)
        logger.info(f"Total interviews: {len(interview_files)}")
        logger.info(f"Successfully processed: {len(successful)}")
        logger.info(f"Skipped (already done): {len(skipped)}")
        logger.info(f"Failed: {len(failed)}")
        logger.info(f"Total cost: ${self.total_cost:.2f}")
        logger.info(f"Total MFT turns: {sum(r.get('mft_turns', 0) for r in successful)}")
        
        if failed:
            logger.error(f"Failed interviews: {[r['interview_id'] for r in failed]}")
        
        # Save summary
        summary_file = self.output_dir / f"annotation_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_interviews': len(interview_files),
                'successful': len(successful),
                'skipped': len(skipped),
                'failed': len(failed),
                'total_cost': self.total_cost,
                'dimensions': 6,
                'includes_mft': True,
                'results': results
            }, f, indent=2)
        
        logger.info(f"\nSummary saved to: {summary_file}")


def main():
    parser = argparse.ArgumentParser(description='Production annotation with MFT')
    parser.add_argument('--max-workers', type=int, default=4, help='Max concurrent workers')
    parser.add_argument('--budget-limit', type=float, default=1.0, help='Budget limit in USD')
    parser.add_argument('--output-dir', type=str, help='Output directory')
    parser.add_argument('--log-file', type=str, help='Log file path')
    
    args = parser.parse_args()
    
    # Setup logging if custom log file specified
    if args.log_file:
        file_handler = logging.FileHandler(args.log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)
    
    # Run annotation
    annotator = ProductionAnnotator(
        max_workers=args.max_workers,
        budget_limit=args.budget_limit,
        output_dir=args.output_dir
    )
    
    asyncio.run(annotator.run())


if __name__ == "__main__":
    main()