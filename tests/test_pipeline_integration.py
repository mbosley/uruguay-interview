"""
Integration tests for the full pipeline.
"""
import os
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET
from unittest.mock import Mock, patch

import pytest

from src.pipeline.full_pipeline import FullPipeline
from src.pipeline.ingestion.document_processor import InterviewDocument
from src.pipeline.extraction.data_extractor import ExtractedData, Priority


@pytest.fixture
def sample_interview():
    """Create a sample interview document."""
    return InterviewDocument(
        id="TEST_001",
        date="2025-01-15",
        time="14:00",
        location="Montevideo",
        department="Montevideo",
        participant_count=3,
        text="""
        Interviewer: What do you think are the main national priorities?
        
        Participant 1: I think security is the biggest issue. We need more police presence
        in our neighborhoods. The crime rate has increased significantly.
        
        Participant 2: For me, education is critical. Our schools lack resources and 
        teachers are underpaid. My children deserve better opportunities.
        
        Participant 3: Healthcare access is my main concern. The waiting times at public
        hospitals are too long, and many people can't afford private care.
        
        Interviewer: And what about local priorities in your community?
        
        Participant 1: We need better street lighting and road maintenance. It's dangerous
        to walk at night.
        
        Participant 2: More recreational spaces for children. There's only one small park
        in our area.
        
        Participant 3: Public transportation needs improvement. The buses are always late
        and overcrowded.
        """,
        metadata={"source": "test"},
        file_path="test_interview.txt"
    )


@pytest.fixture
def mock_annotation_response():
    """Create a mock XML annotation response."""
    xml_str = """<?xml version="1.0" encoding="UTF-8"?>
    <annotation>
        <interview_metadata>
            <id>TEST_001</id>
            <date>2025-01-15</date>
            <time>14:00</time>
            <location>Montevideo</location>
            <participant_count>3</participant_count>
        </interview_metadata>
        
        <interview_level_analysis>
            <dominant_emotion>concern</dominant_emotion>
            <overall_sentiment>negative</overall_sentiment>
        </interview_level_analysis>
        
        <national_priorities>
            <priority rank="1">
                <description>Security and crime prevention</description>
                <category>security</category>
                <sentiment>negative</sentiment>
                <evidence_type>personal_experience</evidence_type>
                <confidence>0.9</confidence>
            </priority>
            <priority rank="2">
                <description>Education quality and resources</description>
                <category>education</category>
                <sentiment>negative</sentiment>
                <evidence_type>personal_experience</evidence_type>
                <confidence>0.85</confidence>
            </priority>
            <priority rank="3">
                <description>Healthcare access and quality</description>
                <category>healthcare</category>
                <sentiment>negative</sentiment>
                <evidence_type>personal_experience</evidence_type>
                <confidence>0.87</confidence>
            </priority>
        </national_priorities>
        
        <local_priorities>
            <priority rank="1">
                <description>Street lighting and road maintenance</description>
                <category>infrastructure</category>
                <sentiment>negative</sentiment>
                <confidence>0.88</confidence>
            </priority>
            <priority rank="2">
                <description>Recreational spaces for children</description>
                <category>social</category>
                <sentiment>negative</sentiment>
                <confidence>0.82</confidence>
            </priority>
        </local_priorities>
        
        <main_themes>
            <theme>Public safety</theme>
            <theme>Education quality</theme>
            <theme>Healthcare access</theme>
            <theme>Infrastructure</theme>
            <theme>Community spaces</theme>
        </main_themes>
        
        <emotions>
            <emotion type="concern" intensity="high" target="security">
                Crime rate has increased significantly
            </emotion>
            <emotion type="frustration" intensity="medium" target="education">
                Teachers are underpaid
            </emotion>
        </emotions>
        
        <processing_metadata>
            <model>test_model</model>
            <confidence>0.85</confidence>
            <processing_time>2.5</processing_time>
        </processing_metadata>
    </annotation>"""
    
    return ET.fromstring(xml_str)


class TestFullPipeline:
    """Test the full pipeline integration."""
    
    def test_pipeline_initialization(self):
        """Test pipeline can be initialized."""
        pipeline = FullPipeline()
        assert pipeline.config is not None
        assert pipeline.document_processor is not None
        assert pipeline.annotation_engine is not None
        assert pipeline.data_extractor is not None
    
    @patch('src.pipeline.annotation.annotation_engine.AnnotationEngine.annotate_interview')
    def test_process_single_interview(self, mock_annotate, sample_interview, mock_annotation_response):
        """Test processing a single interview."""
        # Setup mock
        mock_annotate.return_value = (mock_annotation_response, {
            'processing_time': 2.5,
            'confidence': 0.85
        })
        
        # Create pipeline
        pipeline = FullPipeline()
        
        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(sample_interview.text)
            temp_path = Path(f.name)
        
        try:
            # Process interview (without database)
            result = pipeline.process_interview(temp_path, save_to_db=False)
            
            # Verify results
            assert result['success'] is True
            assert result['interview_id'] is not None
            assert 'ingestion' in result['steps_completed']
            assert 'annotation' in result['steps_completed']
            assert 'extraction' in result['steps_completed']
            
            # Check extracted data
            extracted = result['extracted_data']
            assert extracted['n_national_priorities'] == 3
            assert extracted['n_local_priorities'] == 2
            assert extracted['sentiment'] == 'negative'
            assert extracted['confidence'] == 0.85
            
        finally:
            # Cleanup
            temp_path.unlink()
    
    def test_calculate_batch_cost(self, sample_interview):
        """Test batch cost calculation."""
        pipeline = FullPipeline()
        
        # Create temp directory with files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a few test files
            for i in range(3):
                file_path = temp_path / f"interview_{i}.txt"
                file_path.write_text(sample_interview.text)
            
            # Calculate cost
            cost_est = pipeline.calculate_batch_cost(temp_path)
            
            assert 'error' not in cost_est
            assert cost_est['total_files'] == 3
            assert cost_est['avg_words_per_interview'] > 0
            assert cost_est['estimated_total_cost'] > 0
            assert cost_est['provider'] == pipeline.config.ai.provider
            assert cost_est['model'] == pipeline.config.ai.model
    
    def test_data_extraction(self, mock_annotation_response):
        """Test data extraction from XML."""
        from src.pipeline.extraction.data_extractor import DataExtractor
        
        extractor = DataExtractor()
        
        # Save XML to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(ET.tostring(mock_annotation_response, encoding='unicode'))
            temp_path = Path(f.name)
        
        try:
            # Extract data
            extracted = extractor.extract_from_xml(temp_path)
            
            # Verify extraction
            assert extracted.interview_id == "TEST_001"
            assert extracted.dominant_emotion == "concern"
            assert extracted.overall_sentiment == "negative"
            
            # Check priorities
            assert len(extracted.national_priorities) == 3
            assert extracted.national_priorities[0].category == "security"
            assert extracted.national_priorities[0].sentiment == "negative"
            
            assert len(extracted.local_priorities) == 2
            assert extracted.local_priorities[0].category == "infrastructure"
            
            # Check themes
            assert len(extracted.themes) == 5
            assert "Public safety" in extracted.themes
            
            # Check emotions
            assert len(extracted.emotions) == 2
            assert extracted.emotions[0].type == "concern"
            assert extracted.emotions[0].intensity == "high"
            
        finally:
            temp_path.unlink()
    
    def test_pipeline_error_handling(self):
        """Test pipeline handles errors gracefully."""
        pipeline = FullPipeline()
        
        # Try to process non-existent file
        result = pipeline.process_interview(Path("non_existent.txt"), save_to_db=False)
        
        assert result['success'] is False
        assert len(result['errors']) > 0
        assert 'ingestion' not in result['steps_completed']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])