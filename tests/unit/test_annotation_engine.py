"""
Unit tests for annotation engine components.
"""
import pytest
import xml.etree.ElementTree as ET
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.pipeline.annotation.prompt_manager import PromptManager
from src.pipeline.annotation.annotation_engine import AnnotationEngine
from src.pipeline.ingestion.document_processor import InterviewDocument


class TestPromptManager:
    """Test suite for PromptManager class."""
    
    @pytest.fixture
    def prompt_manager(self):
        """Create a PromptManager instance."""
        # Use the actual schema file
        return PromptManager()
    
    @pytest.fixture
    def sample_interview_metadata(self):
        """Sample interview metadata."""
        return {
            "id": "058",
            "date": "2025-05-28",
            "location": "Young, Río Negro",
            "department": "Río Negro",
            "participant_count": 3
        }
    
    def test_schema_loading(self, prompt_manager):
        """Test that XML schema loads correctly."""
        assert prompt_manager.schema_root is not None
        assert prompt_manager.schema_root.tag == "annotation_schema"
        assert prompt_manager.schema_root.get("version") == "1.0"
    
    def test_create_annotation_prompt(self, prompt_manager, sample_interview_metadata):
        """Test annotation prompt creation."""
        interview_text = "Test interview content..."
        prompt = prompt_manager.create_annotation_prompt(interview_text, sample_interview_metadata)
        
        assert len(prompt) > 0
        assert "annotation_schema" in prompt
        assert interview_text in prompt
        assert sample_interview_metadata["id"] in prompt
        assert "<annotation_result>" in prompt
        assert "</annotation_result>" in prompt
    
    def test_create_empty_annotation_template(self, prompt_manager):
        """Test creating empty annotation template."""
        template = prompt_manager.create_empty_annotation_template("test_001")
        
        assert template.tag == "annotation_result"
        assert template.get("schema_version") == "1.0"
        
        # Check main sections exist
        interview_level = template.find("interview_level")
        assert interview_level is not None
        
        sections = [
            "metadata", "participant_profile", "uncertainty_tracking",
            "priority_summary", "narrative_features", "key_narratives",
            "analytical_notes", "interview_dynamics"
        ]
        
        for section in sections:
            elem = interview_level.find(section)
            assert elem is not None, f"Missing section: {section}"
    
    def test_parse_annotation_response_valid(self, prompt_manager):
        """Test parsing valid XML annotation response."""
        xml_response = """
        Some preamble text...
        <annotation_result schema_version="1.0">
            <interview_level>
                <metadata>
                    <interview_id>test_001</interview_id>
                </metadata>
            </interview_level>
        </annotation_result>
        Some trailing text...
        """
        
        annotation = prompt_manager.parse_annotation_response(xml_response)
        assert annotation.tag == "annotation_result"
        assert annotation.find(".//interview_id").text == "test_001"
    
    def test_parse_annotation_response_invalid(self, prompt_manager):
        """Test parsing invalid XML response."""
        xml_response = "This is not valid XML"
        
        with pytest.raises(ValueError, match="No valid annotation_result found"):
            prompt_manager.parse_annotation_response(xml_response)
    
    def test_validate_annotation_complete(self, prompt_manager):
        """Test validation of complete annotation."""
        # Create a minimal valid annotation
        annotation = ET.Element("annotation_result")
        interview_level = ET.SubElement(annotation, "interview_level")
        
        # Add metadata
        metadata = ET.SubElement(interview_level, "metadata")
        ET.SubElement(metadata, "interview_id").text = "001"
        ET.SubElement(metadata, "date").text = "2025-05-28"
        location = ET.SubElement(metadata, "location")
        ET.SubElement(location, "municipality").text = "Young"
        
        # Add priorities
        priority_summary = ET.SubElement(interview_level, "priority_summary")
        national = ET.SubElement(priority_summary, "national_priorities")
        priority = ET.SubElement(national, "priority")
        priority.set("rank", "1")
        ET.SubElement(priority, "theme").text = "seguridad"
        
        local = ET.SubElement(priority_summary, "local_priorities")
        priority = ET.SubElement(local, "priority")
        priority.set("rank", "1")
        ET.SubElement(priority, "theme").text = "iluminación"
        
        # Add confidence
        uncertainty = ET.SubElement(interview_level, "uncertainty_tracking")
        ET.SubElement(uncertainty, "overall_confidence").text = "0.85"
        
        is_valid, errors = prompt_manager.validate_annotation(annotation)
        assert is_valid
        assert len(errors) == 0
    
    def test_validate_annotation_missing_sections(self, prompt_manager):
        """Test validation catches missing sections."""
        annotation = ET.Element("annotation_result")
        # Missing interview_level
        
        is_valid, errors = prompt_manager.validate_annotation(annotation)
        assert not is_valid
        assert "Missing interview_level element" in errors
    
    def test_extract_key_data(self, prompt_manager):
        """Test extracting key data from annotation."""
        # Create annotation with key data
        annotation = ET.Element("annotation_result")
        interview_level = ET.SubElement(annotation, "interview_level")
        
        metadata = ET.SubElement(interview_level, "metadata")
        ET.SubElement(metadata, "interview_id").text = "058"
        ET.SubElement(metadata, "date").text = "2025-05-28"
        
        priority_summary = ET.SubElement(interview_level, "priority_summary")
        national = ET.SubElement(priority_summary, "national_priorities")
        priority = ET.SubElement(national, "priority")
        priority.set("rank", "1")
        ET.SubElement(priority, "theme").text = "seguridad"
        ET.SubElement(priority, "narrative_elaboration").text = "Security is crucial..."
        
        data = prompt_manager.extract_key_data(annotation)
        
        assert data["interview_id"] == "058"
        assert data["date"] == "2025-05-28"
        assert len(data["national_priorities"]) == 1
        assert data["national_priorities"][0]["theme"] == "seguridad"
        assert data["national_priorities"][0]["rank"] == 1


class TestAnnotationEngine:
    """Test suite for AnnotationEngine class."""
    
    @pytest.fixture
    def mock_interview(self):
        """Create a mock interview document."""
        return InterviewDocument(
            id="test_001",
            date="2025-05-28",
            time="09:00",
            location="Montevideo",
            department="Montevideo",
            participant_count=2,
            text="Sample interview text about priorities...",
            metadata={"word_count": 100},
            file_path="/tmp/test.txt"
        )
    
    @pytest.fixture
    def mock_openai_response(self):
        """Mock OpenAI API response."""
        return """
        <annotation_result schema_version="1.0">
            <interview_level>
                <metadata>
                    <interview_id>test_001</interview_id>
                    <date>2025-05-28</date>
                    <location>
                        <municipality>Montevideo</municipality>
                    </location>
                </metadata>
                <uncertainty_tracking>
                    <overall_confidence>0.85</overall_confidence>
                </uncertainty_tracking>
                <priority_summary>
                    <national_priorities>
                        <priority rank="1">
                            <theme>seguridad</theme>
                        </priority>
                    </national_priorities>
                    <local_priorities>
                        <priority rank="1">
                            <theme>transporte</theme>
                        </priority>
                    </local_priorities>
                </priority_summary>
            </interview_level>
        </annotation_result>
        """
    
    @patch('os.getenv')
    @patch('openai.OpenAI')
    def test_annotation_engine_initialization(self, mock_openai_class, mock_getenv):
        """Test annotation engine initialization."""
        mock_getenv.return_value = "fake-api-key"
        engine = AnnotationEngine(model_provider="openai")
        
        assert engine.model_provider == "openai"
        assert engine.model_name == "gpt-4-turbo-preview"
        mock_openai_class.assert_called_once()
    
    @patch('os.getenv')
    @patch('openai.OpenAI')
    def test_annotate_interview_success(self, mock_openai_class, mock_getenv, mock_interview, mock_openai_response):
        """Test successful interview annotation."""
        # Setup mocks
        mock_getenv.return_value = "fake-api-key"
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_completion = Mock()
        mock_completion.choices = [Mock(message=Mock(content=mock_openai_response))]
        mock_client.chat.completions.create.return_value = mock_completion
        
        # Create engine and annotate
        engine = AnnotationEngine(model_provider="openai")
        annotation, metadata = engine.annotate_interview(mock_interview)
        
        # Assertions
        assert annotation.tag == "annotation_result"
        assert metadata["model_provider"] == "openai"
        assert metadata["confidence"] == 0.85
        assert metadata["interview_word_count"] == 100
        
        # Check API was called
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('os.getenv')
    @patch('openai.OpenAI')
    def test_annotate_interview_retry_on_error(self, mock_openai_class, mock_getenv, mock_interview):
        """Test retry mechanism on API errors."""
        mock_getenv.return_value = "fake-api-key"
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # First call fails, second succeeds
        mock_client.chat.completions.create.side_effect = [
            Exception("API Error"),
            Mock(choices=[Mock(message=Mock(content="<annotation_result></annotation_result>"))])
        ]
        
        engine = AnnotationEngine(model_provider="openai")
        
        with pytest.raises(RuntimeError):  # Will fail validation
            engine.annotate_interview(mock_interview, max_retries=2)
        
        # Should have tried twice
        assert mock_client.chat.completions.create.call_count == 2
    
    def test_calculate_annotation_cost(self, mock_interview):
        """Test cost calculation for annotation."""
        engine = AnnotationEngine(model_provider="openai")
        costs = engine.calculate_annotation_cost(mock_interview)
        
        assert "openai_gpt4" in costs
        assert "anthropic_claude3" in costs
        
        # Check cost structure
        for provider, cost_data in costs.items():
            assert "prompt_tokens" in cost_data
            assert "output_tokens" in cost_data
            assert "total_cost" in cost_data
            assert cost_data["total_cost"] > 0
    
    @patch('os.getenv')
    @patch('openai.OpenAI')
    def test_batch_annotate(self, mock_openai_class, mock_getenv, mock_interview, mock_openai_response):
        """Test batch annotation of multiple interviews."""
        mock_getenv.return_value = "fake-api-key"
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_completion = Mock()
        mock_completion.choices = [Mock(message=Mock(content=mock_openai_response))]
        mock_client.chat.completions.create.return_value = mock_completion
        
        engine = AnnotationEngine(model_provider="openai")
        
        # Create multiple interviews
        interviews = [mock_interview, mock_interview]
        
        results = engine.batch_annotate(interviews)
        
        assert len(results) == 2
        assert all(success for _, success, _ in results)
        assert mock_client.chat.completions.create.call_count == 2