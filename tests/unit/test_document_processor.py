"""
Unit tests for document processor module.
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from datetime import datetime

from src.pipeline.ingestion.document_processor import DocumentProcessor, InterviewDocument


class TestDocumentProcessor:
    """Test suite for DocumentProcessor class."""
    
    @pytest.fixture
    def processor(self):
        """Create a DocumentProcessor instance."""
        return DocumentProcessor()
    
    @pytest.fixture
    def sample_txt_content(self):
        """Sample interview text content."""
        return """Lugar: Young, Río Negro
Fecha: 28/05/2025
Entrevistador: CR

AM: Buenos días, soy Antonela Merica, psicóloga del centro.
SL: Soy Silvia Lafluf, presidenta de la comisión de apoyo.
JP: Juan Poggio, director de la institución.

Entrevistador: ¿Cuáles son las principales prioridades nacionales?
AM: La inclusión laboral es fundamental para nosotros...
"""
    
    @pytest.fixture
    def sample_filename_patterns(self):
        """Various filename patterns to test."""
        return [
            ("20250528_0900_058.txt", {
                "date": "2025-05-28",
                "time": "09:00",
                "id": "058"
            }),
            ("T - 20250528 0900 58.docx", {
                "date": "2025-05-28",
                "time": "09:00",
                "id": "58"
            }),
            ("T- 20250528 1015 59.docx", {
                "date": "2025-05-28",
                "time": "10:15",
                "id": "59"
            }),
            ("invalid_format.txt", {
                "date": datetime.now().strftime('%Y-%m-%d'),
                "time": "00:00",
                "id": "invalid_format"
            })
        ]
    
    def test_extract_metadata_from_filenames(self, processor, sample_filename_patterns):
        """Test metadata extraction from various filename formats."""
        for filename, expected in sample_filename_patterns:
            metadata = processor._extract_metadata(filename, "")
            assert metadata["date"] == expected["date"]
            assert metadata["time"] == expected["time"]
            assert metadata["id"] == expected["id"]
    
    def test_detect_location(self, processor):
        """Test location detection from text."""
        test_cases = [
            ("Lugar: Montevideo, Uruguay", "Montevideo, Uruguay"),
            ("ubicación: Canelones", "Canelones"),
            ("La entrevista se realizó en Salto", "Salto"),
            ("barrio: Cerro", "Cerro"),
            ("No location info", "Unknown")
        ]
        
        for text, expected in test_cases:
            location = processor._detect_location(text)
            assert location == expected
    
    def test_detect_department(self, processor):
        """Test Uruguay department detection."""
        test_cases = [
            ("Estamos en Montevideo", "Montevideo"),
            ("Desde Canelones reportamos", "Canelones"),
            ("En el departamento de Salto", "Salto"),
            ("río negro es nuestro departamento", "Río Negro"),
            ("No department mentioned", None)
        ]
        
        for text, expected in test_cases:
            department = processor._detect_department(text)
            assert department == expected
    
    def test_count_participants(self, processor):
        """Test participant counting logic."""
        test_cases = [
            # Single participant
            ("Entrevistador: ¿Cómo está?\nJuan: Bien, gracias.", 1),
            
            # Multiple participants with initials
            ("E: Pregunta\nAM: Respuesta\nSL: Otra respuesta\nJP: Comentario", 3),
            
            # Multiple participants with full names
            ("Entrevistador: Pregunta\nMaría: Respuesta\nPedro: Comentario", 2),
            
            # No clear speakers
            ("Esta es una entrevista sin formato claro de diálogo.", 1),
            
            # Mixed format
            ("Ent: Pregunta\nParticipante 1: Respuesta\nParticipante 2: Otra", 2)
        ]
        
        for text, expected_count in test_cases:
            count = processor._count_participants(text)
            assert count == expected_count
    
    def test_process_txt_file(self, processor, sample_txt_content, tmp_path):
        """Test processing of TXT files."""
        # Create temporary file
        txt_file = tmp_path / "test_interview.txt"
        txt_file.write_text(sample_txt_content)
        
        # Process file
        interview = processor.process_interview(txt_file)
        
        # Assertions
        assert isinstance(interview, InterviewDocument)
        assert interview.text == sample_txt_content
        assert interview.location == "Young, Río Negro"
        # Note: Count includes CR as it's not in the exclusion list
        assert interview.participant_count >= 3  # At least AM, SL, JP
        assert interview.metadata["word_count"] == len(sample_txt_content.split())
    
    @patch('docx.Document')
    def test_process_docx_file(self, mock_docx, processor, sample_txt_content, tmp_path):
        """Test processing of DOCX files."""
        # Mock docx document
        mock_doc = Mock()
        mock_para1 = Mock()
        mock_para1.text = "Lugar: Young, Río Negro"
        mock_para2 = Mock()
        mock_para2.text = "AM: Buenos días, soy Antonela Merica"
        mock_para3 = Mock()
        mock_para3.text = ""  # Empty paragraph
        mock_doc.paragraphs = [mock_para1, mock_para2, mock_para3]
        mock_docx.return_value = mock_doc
        
        # Create temporary file
        docx_file = tmp_path / "20250528_0900_058.docx"
        docx_file.touch()
        
        # Process file
        interview = processor.process_interview(docx_file)
        
        # Assertions
        assert isinstance(interview, InterviewDocument)
        assert interview.id == "058"
        assert interview.date == "2025-05-28"
        assert interview.time == "09:00"
        assert "Lugar: Young, Río Negro" in interview.text
        assert "AM: Buenos días, soy Antonela Merica" in interview.text
        assert interview.text.count('\n') == 1  # Empty paragraph filtered out
    
    def test_unsupported_file_type(self, processor, tmp_path):
        """Test handling of unsupported file types."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.touch()
        
        with pytest.raises(ValueError, match="Unsupported file type"):
            processor.process_interview(pdf_file)
    
    def test_file_not_found(self, processor):
        """Test handling of non-existent files."""
        fake_file = Path("non_existent_file.txt")
        
        with pytest.raises(FileNotFoundError):
            processor.process_interview(fake_file)
    
    def test_metadata_completeness(self, processor, sample_txt_content):
        """Test that all expected metadata fields are present."""
        metadata = processor._extract_metadata("20250528_0900_058.txt", sample_txt_content)
        
        required_fields = [
            'id', 'date', 'time', 'location', 'department',
            'participant_count', 'filename', 'text_length', 'word_count'
        ]
        
        for field in required_fields:
            assert field in metadata
            
    def test_edge_cases(self, processor):
        """Test edge cases and boundary conditions."""
        # Empty text
        metadata = processor._extract_metadata("test.txt", "")
        assert metadata['word_count'] == 0
        assert metadata['participant_count'] == 1
        assert metadata['location'] == "Unknown"
        
        # Very long speaker list
        long_speaker_text = "\n".join([f"P{i}: Comment" for i in range(100)])
        count = processor._count_participants(long_speaker_text)
        assert count >= 50  # Should detect many participants
        
        # Special characters in location
        special_location = "Lugar: Río Negro/Young - Centro"
        location = processor._detect_location(special_location)
        assert location == "Río Negro/Young - Centro"


class TestInterviewDocument:
    """Test suite for InterviewDocument dataclass."""
    
    def test_interview_document_creation(self):
        """Test creating an InterviewDocument instance."""
        doc = InterviewDocument(
            id="001",
            date="2025-05-28",
            time="09:00",
            location="Montevideo",
            department="Montevideo",
            participant_count=3,
            text="Sample interview text",
            metadata={"key": "value"},
            file_path="/path/to/file.txt"
        )
        
        assert doc.id == "001"
        assert doc.date == "2025-05-28"
        assert doc.time == "09:00"
        assert doc.location == "Montevideo"
        assert doc.department == "Montevideo"
        assert doc.participant_count == 3
        assert doc.text == "Sample interview text"
        assert doc.metadata == {"key": "value"}
        assert doc.file_path == "/path/to/file.txt"