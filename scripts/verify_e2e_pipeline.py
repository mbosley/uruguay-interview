#!/usr/bin/env python3
"""
End-to-end pipeline verification script.
Tests the complete pipeline flow on a small subset of interview data.
"""
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.pipeline.full_pipeline import FullPipeline
from src.database.connection import DatabaseConnection
from src.database.models import Interview, Turn, Annotation, Priority, Theme
from src.config.config_loader import get_config

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class PipelineVerifier:
    """Verifies end-to-end pipeline functionality."""
    
    def __init__(self):
        self.config = get_config()
        self.pipeline = FullPipeline()
        self.db = DatabaseConnection(self.config.database.url)
        self.results = {
            'files_processed': 0,
            'files_successful': 0,
            'files_failed': 0,
            'errors': [],
            'verifications': []
        }
    
    def find_test_files(self, limit: int = 2) -> List[Path]:
        """Find a small subset of interview files for testing."""
        interview_dir = Path("data/processed/interviews_txt")
        
        if not interview_dir.exists():
            raise FileNotFoundError(f"Interview directory not found: {interview_dir}")
        
        # Get interview files
        files = list(interview_dir.glob("*.txt"))
        
        if not files:
            raise FileNotFoundError(f"No interview files found in {interview_dir}")
        
        # Return first N files for testing
        test_files = files[:limit]
        logger.info(f"Selected {len(test_files)} files for testing: {[f.name for f in test_files]}")
        
        return test_files
    
    def process_files(self, files: List[Path]) -> None:
        """Process files through the pipeline."""
        logger.info("=== STEP 1: Processing Files Through Pipeline ===")
        
        for file_path in files:
            logger.info(f"Processing: {file_path.name}")
            self.results['files_processed'] += 1
            
            try:
                # Process through pipeline
                result = self.pipeline.process_interview(file_path, save_to_db=True)
                
                if result['success']:
                    self.results['files_successful'] += 1
                    logger.info(f"✓ Successfully processed {file_path.name}")
                    logger.info(f"  - Steps completed: {result['steps_completed']}")
                    logger.info(f"  - Processing time: {result.get('total_time', 0):.2f}s")
                else:
                    self.results['files_failed'] += 1
                    self.results['errors'].append(f"{file_path.name}: {result['errors']}")
                    logger.error(f"✗ Failed to process {file_path.name}: {result['errors']}")
                    
            except Exception as e:
                self.results['files_failed'] += 1
                self.results['errors'].append(f"{file_path.name}: {str(e)}")
                logger.error(f"✗ Exception processing {file_path.name}: {e}")
    
    def verify_database_storage(self) -> None:
        """Verify that data was correctly stored in the database."""
        logger.info("=== STEP 2: Verifying Database Storage ===")
        
        with self.db.get_session() as session:
            # Check interviews
            interviews = session.query(Interview).all()
            logger.info(f"Interviews in database: {len(interviews)}")
            
            for interview in interviews[-self.results['files_processed']:]:  # Check recent interviews
                verification = {
                    'interview_id': interview.interview_id,
                    'location': interview.location,
                    'checks': {}
                }
                
                # Check basic interview data
                verification['checks']['has_raw_text'] = bool(interview.raw_text)
                verification['checks']['has_word_count'] = bool(interview.word_count)
                verification['checks']['word_count'] = interview.word_count
                
                # Check annotations
                annotations = session.query(Annotation).filter_by(interview_id=interview.id).all()
                verification['checks']['annotations_count'] = len(annotations)
                verification['checks']['has_xml_content'] = any(a.xml_content for a in annotations)
                
                # Check priorities
                priorities = session.query(Priority).filter_by(interview_id=interview.id).all()
                verification['checks']['priorities_count'] = len(priorities)
                national_priorities = [p for p in priorities if p.scope == 'national']
                local_priorities = [p for p in priorities if p.scope == 'local']
                verification['checks']['national_priorities'] = len(national_priorities)
                verification['checks']['local_priorities'] = len(local_priorities)
                
                # Check themes
                themes = session.query(Theme).filter_by(interview_id=interview.id).all()
                verification['checks']['themes_count'] = len(themes)
                
                # Check conversation turns
                turns = session.query(Turn).filter_by(interview_id=interview.id).all()
                verification['checks']['turns_count'] = len(turns)
                if turns:
                    verification['checks']['unique_speakers'] = len(set(t.speaker for t in turns))
                    verification['checks']['total_turn_words'] = sum(t.word_count for t in turns)
                
                self.results['verifications'].append(verification)
                
                # Log verification results
                logger.info(f"Interview {interview.interview_id} ({interview.location}):")
                logger.info(f"  ✓ Raw text: {verification['checks']['has_raw_text']} ({verification['checks']['word_count']} words)")
                logger.info(f"  ✓ Annotations: {verification['checks']['annotations_count']}")
                logger.info(f"  ✓ Priorities: {verification['checks']['priorities_count']} (N:{verification['checks']['national_priorities']}, L:{verification['checks']['local_priorities']})")
                logger.info(f"  ✓ Themes: {verification['checks']['themes_count']}")
                logger.info(f"  ✓ Conversation turns: {verification['checks']['turns_count']} turns, {verification['checks'].get('unique_speakers', 0)} speakers")
    
    def check_data_integrity(self) -> None:
        """Check data integrity and relationships."""
        logger.info("=== STEP 3: Data Integrity Checks ===")
        
        with self.db.get_session() as session:
            integrity_issues = []
            
            # Check for interviews without raw text
            interviews_no_text = session.query(Interview).filter(
                (Interview.raw_text.is_(None)) | (Interview.raw_text == '')
            ).count()
            if interviews_no_text > 0:
                integrity_issues.append(f"{interviews_no_text} interviews missing raw text")
            
            # Check for interviews without annotations
            interviews_no_annotations = session.query(Interview).outerjoin(Annotation).filter(
                Annotation.id.is_(None)
            ).count()
            if interviews_no_annotations > 0:
                integrity_issues.append(f"{interviews_no_annotations} interviews missing annotations")
            
            # Check for annotations without XML content
            annotations_no_xml = session.query(Annotation).filter(
                (Annotation.xml_content.is_(None)) | (Annotation.xml_content == '')
            ).count()
            if annotations_no_xml > 0:
                integrity_issues.append(f"{annotations_no_xml} annotations missing XML content")
            
            # Check for interviews without turns
            interviews_no_turns = session.query(Interview).outerjoin(Turn).filter(
                Turn.id.is_(None)
            ).count()
            if interviews_no_turns > 0:
                integrity_issues.append(f"{interviews_no_turns} interviews missing conversation turns")
            
            if integrity_issues:
                logger.warning("Data integrity issues found:")
                for issue in integrity_issues:
                    logger.warning(f"  ⚠ {issue}")
            else:
                logger.info("✓ No data integrity issues found")
    
    def print_summary(self) -> None:
        """Print verification summary."""
        logger.info("=== PIPELINE VERIFICATION SUMMARY ===")
        logger.info(f"Files processed: {self.results['files_processed']}")
        logger.info(f"Successful: {self.results['files_successful']}")
        logger.info(f"Failed: {self.results['files_failed']}")
        
        if self.results['errors']:
            logger.error("Errors encountered:")
            for error in self.results['errors']:
                logger.error(f"  - {error}")
        
        success_rate = (self.results['files_successful'] / self.results['files_processed']) * 100 if self.results['files_processed'] > 0 else 0
        logger.info(f"Success rate: {success_rate:.1f}%")
        
        if success_rate == 100.0:
            logger.info("🎉 END-TO-END PIPELINE VERIFICATION PASSED!")
        else:
            logger.warning("⚠️  Pipeline verification completed with issues")
    
    def run_verification(self, limit: int = 2) -> bool:
        """Run complete end-to-end verification."""
        try:
            # Find test files
            test_files = self.find_test_files(limit)
            
            # Process files
            self.process_files(test_files)
            
            # Verify database storage
            self.verify_database_storage()
            
            # Check data integrity
            self.check_data_integrity()
            
            # Print summary
            self.print_summary()
            
            return self.results['files_failed'] == 0
            
        except Exception as e:
            logger.error(f"Verification failed with exception: {e}")
            return False


def main():
    """Main verification function."""
    logger.info("Starting end-to-end pipeline verification...")
    
    verifier = PipelineVerifier()
    
    # Run verification on 2 files by default
    success = verifier.run_verification(limit=2)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()