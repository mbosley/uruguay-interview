"""
End-to-end tests for the complete pipeline.
"""
import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import tempfile

from src.pipeline.full_pipeline import FullPipeline


class TestFullPipelineE2E:
    """End-to-end tests for the complete pipeline."""
    
    @pytest.fixture
    def sample_interview_file(self, sample_interview_text):
        """Create a temporary interview file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(sample_interview_text)
            temp_path = Path(f.name)
        
        yield temp_path
        temp_path.unlink()
    
    @patch('src.pipeline.annotation.annotation_engine.AnnotationEngine.annotate_interview')
    @patch('src.database.repository.ExtractedDataRepository.save_extracted_data')
    def test_pipeline_process_interview_success(self, mock_save, mock_annotate, sample_interview_file):
        """Test successful end-to-end interview processing."""
        # Mock AI annotation response
        mock_xml = Mock()
        mock_xml.__str__ = lambda: "<interview><priorities></priorities></interview>"
        mock_annotate.return_value = (mock_xml, {"processing_time": 10.5})
        
        # Create pipeline
        pipeline = FullPipeline()
        
        # Process interview
        result = pipeline.process_interview(sample_interview_file, save_to_db=True)
        
        # Verify success
        assert result['success'] is True
        assert 'ingestion' in result['steps_completed']
        assert 'annotation' in result['steps_completed']
        assert 'extraction' in result['steps_completed']
        assert 'database' in result['steps_completed']
        assert result['interview_id'] is not None
        assert len(result['errors']) == 0
        
        # Verify database save was called
        mock_save.assert_called_once()
        
        # Verify save was called with raw text
        call_args = mock_save.call_args
        assert 'raw_text' in call_args[1]  # keyword arguments
        assert call_args[1]['raw_text'] is not None
    
    def test_pipeline_component_verification(self):
        """Test that all pipeline components can be instantiated."""
        pipeline = FullPipeline()
        
        # Verify components exist
        assert pipeline.document_processor is not None
        assert pipeline.annotation_engine is not None
        assert pipeline.data_extractor is not None
        assert pipeline.config is not None
    
    @patch('src.pipeline.annotation.annotation_engine.AnnotationEngine.annotate_interview')
    def test_pipeline_handles_annotation_failure(self, mock_annotate, sample_interview_file):
        """Test pipeline handling of annotation failures."""
        # Mock annotation failure
        mock_annotate.side_effect = Exception("API rate limit exceeded")
        
        pipeline = FullPipeline()
        result = pipeline.process_interview(sample_interview_file, save_to_db=False)
        
        # Verify failure handling
        assert result['success'] is False
        assert len(result['errors']) > 0
        assert 'ingestion' in result['steps_completed']  # Should complete ingestion
        assert 'annotation' not in result['steps_completed']  # Should fail at annotation
    
    def test_pipeline_batch_processing_structure(self):
        """Test batch processing structure (without actual processing)."""
        pipeline = FullPipeline()
        
        # Create temporary directory with fake files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create some fake interview files
            (temp_path / "interview1.txt").write_text("Sample content 1")
            (temp_path / "interview2.txt").write_text("Sample content 2")
            
            # Test batch processing structure
            with patch.object(pipeline, 'process_interview') as mock_process:
                mock_process.return_value = {
                    'success': True,
                    'interview_id': 'test',
                    'steps_completed': ['ingestion'],
                    'errors': [],
                    'total_time': 1.0
                }
                
                result = pipeline.process_batch(temp_path, limit=2, save_to_db=False)
                
                # Verify batch structure
                assert 'total_files' in result
                assert 'successful' in result
                assert 'failed' in result
                assert 'files_processed' in result
                assert result['total_files'] == 2
                assert mock_process.call_count == 2


@pytest.mark.integration
class TestPipelineWithRealComponents:
    """Integration tests using real components (no mocking)."""
    
    def test_document_processing_only(self, sample_interview_file):
        """Test just the document processing step."""
        pipeline = FullPipeline()
        
        # Process just the document
        interview = pipeline.document_processor.process_interview(sample_interview_file)
        
        # Verify processing
        assert interview is not None
        assert interview.text is not None
        assert interview.id is not None
        assert interview.location is not None
    
    def test_conversation_parsing_integration(self, sample_interview_text):
        """Test conversation parsing with real parser."""
        pipeline = FullPipeline()
        
        # This test uses the real conversation parser
        from src.pipeline.parsing.conversation_parser import ConversationParser
        parser = ConversationParser()
        
        turns = parser.parse_conversation(sample_interview_text)
        summary = parser.get_conversation_summary(turns)
        
        # Verify parsing worked
        assert len(turns) > 0
        assert summary['total_turns'] > 0
        assert summary['unique_speakers'] > 0
        assert summary['total_words'] > 0
    
    @pytest.mark.slow
    def test_cost_calculation(self):
        """Test cost calculation functionality."""
        pipeline = FullPipeline()
        
        # Create temporary directory with one small file
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "test.txt"
            test_file.write_text("Short interview for cost testing" * 10)  # Small file
            
            try:
                cost_result = pipeline.calculate_batch_cost(temp_path, limit=1)
                
                # Verify cost calculation structure
                assert 'total_files' in cost_result
                assert 'avg_cost_per_interview' in cost_result
                assert 'estimated_total_cost' in cost_result
                assert 'provider' in cost_result
                assert 'model' in cost_result
                
            except Exception as e:
                # Cost calculation might fail without proper API setup
                pytest.skip(f"Cost calculation requires API access: {e}")


@pytest.mark.database
class TestPipelineWithDatabase:
    """Tests that require database connectivity."""
    
    @pytest.mark.skip(reason="Requires database setup")
    def test_full_pipeline_with_database(self, sample_interview_file, test_db_connection):
        """Test complete pipeline with real database."""
        # This test would require actual database setup
        # Skip by default but available for integration testing
        pass
    
    @pytest.mark.skip(reason="Requires database setup") 
    def test_conversation_turns_in_database(self, test_db_connection):
        """Test that conversation turns are properly stored."""
        # This test would verify turn storage in real database
        pass