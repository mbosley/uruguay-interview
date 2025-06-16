"""
Full end-to-end pipeline for interview processing.
Combines ingestion, annotation, extraction, and database storage.
"""
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.config.config_loader import get_config
from src.pipeline.ingestion.document_processor import DocumentProcessor, InterviewDocument
from src.pipeline.annotation.annotation_engine import AnnotationEngine
from src.pipeline.extraction.data_extractor import DataExtractor
from src.database.connection import get_session
from src.database.repository import ExtractedDataRepository, ProcessingLog

logger = logging.getLogger(__name__)


class FullPipeline:
    """
    Orchestrates the complete interview analysis pipeline.
    """
    
    def __init__(self):
        """Initialize pipeline components."""
        self.config = get_config()
        self.document_processor = DocumentProcessor()
        self.annotation_engine = AnnotationEngine()
        self.data_extractor = DataExtractor()
        
        logger.info(f"Pipeline initialized with {self.config.ai.provider}/{self.config.ai.model}")
    
    def process_interview(self, file_path: Path, save_to_db: bool = True) -> Dict[str, Any]:
        """
        Process a single interview through the full pipeline.
        
        Args:
            file_path: Path to interview file
            save_to_db: Whether to save results to database
            
        Returns:
            Dictionary with processing results
        """
        start_time = datetime.now()
        results = {
            'success': False,
            'interview_id': None,
            'steps_completed': [],
            'errors': []
        }
        
        try:
            # Step 1: Document Ingestion
            logger.info(f"Processing document: {file_path}")
            interview = self.document_processor.process_interview(file_path)
            results['interview_id'] = interview.id
            results['steps_completed'].append('ingestion')
            
            # Step 2: AI Annotation
            logger.info(f"Annotating interview {interview.id}")
            annotation_xml, metadata = self.annotation_engine.annotate_interview(interview)
            results['steps_completed'].append('annotation')
            results['annotation_metadata'] = metadata
            
            # Save XML annotation if configured
            if self.config.annotation.save_xml:
                xml_path = self._save_annotation_xml(interview.id, annotation_xml)
                results['xml_path'] = str(xml_path)
            
            # Step 3: Data Extraction
            logger.info(f"Extracting structured data for {interview.id}")
            # Save XML temporarily for extraction
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as tmp:
                annotation_xml.write(tmp.file, encoding='unicode')
                tmp_path = Path(tmp.name)
            
            extracted_data = self.data_extractor.extract_from_xml(tmp_path)
            tmp_path.unlink()  # Clean up temp file
            
            results['steps_completed'].append('extraction')
            results['extracted_data'] = {
                'n_national_priorities': len(extracted_data.national_priorities),
                'n_local_priorities': len(extracted_data.local_priorities),
                'n_themes': len(extracted_data.themes),
                'sentiment': extracted_data.overall_sentiment,
                'confidence': extracted_data.confidence_score
            }
            
            # Save JSON if configured
            if self.config.annotation.save_json:
                json_path = self._save_extracted_json(interview.id, extracted_data)
                results['json_path'] = str(json_path)
            
            # Step 4: Database Storage
            if save_to_db:
                logger.info(f"Saving to database for {interview.id}")
                with get_session() as session:
                    repo = ExtractedDataRepository(session)
                    
                    # Convert XML to string for storage
                    import xml.etree.ElementTree as ET
                    xml_string = ET.tostring(annotation_xml, encoding='unicode')
                    
                    repo.save_extracted_data(extracted_data, xml_content=xml_string)
                    
                    # Log processing
                    log_entry = ProcessingLog(
                        interview_id=interview.id,
                        activity_type='full_pipeline',
                        status='completed',
                        details={
                            'file_path': str(file_path),
                            'model': self.config.ai.model,
                            'processing_time': metadata.get('processing_time'),
                            'confidence': extracted_data.confidence_score
                        },
                        duration=(datetime.now() - start_time).total_seconds(),
                        started_at=start_time,
                        completed_at=datetime.now()
                    )
                    session.add(log_entry)
                    session.commit()
                
                results['steps_completed'].append('database')
            
            results['success'] = True
            results['total_time'] = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Successfully processed {interview.id} in {results['total_time']:.2f}s")
            
        except Exception as e:
            logger.error(f"Pipeline failed for {file_path}: {e}")
            results['errors'].append(str(e))
            
            # Log failure to database
            if save_to_db and results['interview_id']:
                try:
                    with get_session() as session:
                        log_entry = ProcessingLog(
                            interview_id=results['interview_id'],
                            activity_type='full_pipeline',
                            status='failed',
                            error_message=str(e),
                            duration=(datetime.now() - start_time).total_seconds(),
                            started_at=start_time
                        )
                        session.add(log_entry)
                        session.commit()
                except Exception as db_error:
                    logger.error(f"Failed to log error to database: {db_error}")
        
        return results
    
    def process_batch(self, input_dir: Path, limit: Optional[int] = None,
                     save_to_db: bool = True) -> Dict[str, Any]:
        """
        Process multiple interviews in batch.
        
        Args:
            input_dir: Directory containing interview files
            limit: Maximum number of files to process
            save_to_db: Whether to save results to database
            
        Returns:
            Dictionary with batch processing results
        """
        start_time = datetime.now()
        
        # Find interview files
        files = []
        for pattern in ['*.txt', '*.docx', '*.odt']:
            files.extend(input_dir.glob(pattern))
        
        if limit:
            files = files[:limit]
        
        logger.info(f"Found {len(files)} interview files to process")
        
        # Process each file
        results = {
            'total_files': len(files),
            'successful': 0,
            'failed': 0,
            'files_processed': [],
            'errors': []
        }
        
        for i, file_path in enumerate(files, 1):
            logger.info(f"Processing file {i}/{len(files)}: {file_path.name}")
            
            file_result = self.process_interview(file_path, save_to_db)
            
            if file_result['success']:
                results['successful'] += 1
            else:
                results['failed'] += 1
                results['errors'].append({
                    'file': str(file_path),
                    'errors': file_result['errors']
                })
            
            results['files_processed'].append({
                'file': str(file_path),
                'interview_id': file_result['interview_id'],
                'success': file_result['success'],
                'time': file_result.get('total_time', 0)
            })
        
        results['total_time'] = (datetime.now() - start_time).total_seconds()
        results['avg_time_per_file'] = results['total_time'] / len(files) if files else 0
        
        logger.info(f"Batch processing complete: {results['successful']}/{len(files)} successful")
        
        return results
    
    def _save_annotation_xml(self, interview_id: str, annotation_xml) -> Path:
        """Save XML annotation to file."""
        output_dir = Path(self.config.processing.output_dir) / "annotations" / "xml"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        xml_path = output_dir / f"{interview_id}_annotation.xml"
        annotation_xml.write(str(xml_path), encoding='utf-8', xml_declaration=True)
        
        return xml_path
    
    def _save_extracted_json(self, interview_id: str, extracted_data) -> Path:
        """Save extracted data as JSON."""
        output_dir = Path(self.config.processing.output_dir) / "annotations" / "json"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        json_path = output_dir / f"{interview_id}_extracted.json"
        self.data_extractor.export_to_json(extracted_data, json_path)
        
        return json_path
    
    def calculate_batch_cost(self, input_dir: Path, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Calculate estimated cost for processing a batch of interviews.
        
        Args:
            input_dir: Directory containing interview files
            limit: Maximum number of files to consider
            
        Returns:
            Cost estimation details
        """
        # Find interview files
        files = []
        for pattern in ['*.txt', '*.docx', '*.odt']:
            files.extend(input_dir.glob(pattern))
        
        if limit:
            files = files[:limit]
        
        if not files:
            return {'error': 'No interview files found'}
        
        # Sample first few files for estimation
        sample_size = min(5, len(files))
        sample_files = files[:sample_size]
        
        total_words = 0
        costs_per_interview = []
        
        for file_path in sample_files:
            try:
                interview = self.document_processor.process_interview(file_path)
                word_count = len(interview.text.split())
                total_words += word_count
                
                # Get cost for this interview
                cost_data = self.annotation_engine.calculate_annotation_cost(interview)
                provider_key = f"{self.config.ai.provider}_{self.config.ai.model.replace('-', '_').replace('.', '_')}"
                
                # Find matching cost entry
                for key, data in cost_data.items():
                    if self.config.ai.provider in key:
                        costs_per_interview.append(data['total_cost'])
                        break
                
            except Exception as e:
                logger.warning(f"Failed to process sample file {file_path}: {e}")
        
        if not costs_per_interview:
            return {'error': 'Failed to calculate costs'}
        
        avg_cost = sum(costs_per_interview) / len(costs_per_interview)
        avg_words = total_words / sample_size
        
        return {
            'total_files': len(files),
            'sample_size': sample_size,
            'avg_words_per_interview': avg_words,
            'avg_cost_per_interview': avg_cost,
            'estimated_total_cost': avg_cost * len(files),
            'provider': self.config.ai.provider,
            'model': self.config.ai.model
        }


if __name__ == "__main__":
    # Test the pipeline
    pipeline = FullPipeline()
    
    # Process a single file
    test_file = Path("data/processed/interviews_txt/20250528_0900_058.txt")
    if test_file.exists():
        result = pipeline.process_interview(test_file, save_to_db=False)
        print(f"Processing result: {result}")
    else:
        print(f"Test file not found: {test_file}")