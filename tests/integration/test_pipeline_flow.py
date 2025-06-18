"""
Integration tests for pipeline components working together.
"""
import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import tempfile

from src.pipeline.ingestion.document_processor import DocumentProcessor
from src.pipeline.parsing.conversation_parser import ConversationParser
from src.database.repository import ExtractedDataRepository
from src.pipeline.extraction.data_extractor import ExtractedData


class TestPipelineIntegration:
    """Integration tests for pipeline components."""
    
    @pytest.fixture
    def sample_complete_interview(self):
        """Complete interview text for integration testing."""
        return """
Id Agenda: 58

ORGANIZACIÓN: Directiva del Centro Esperanza Young (CEY)
Localidad: Young, Río Negro
Fecha de la entrevista: 28/05/2025
Entrevistadores: Claudia Rodríguez (CR), Mauricio Serviansky (MS)
Entrevistados: Antonela Merica (AM), Silvia Lafluf (SL), Juan Poggio (JP)

___

[AM]
Nos han contactado a ver si podríamos recibir desde Paysandú también
porque en la zona es el único centro referente que hay.

[CR]
¿Y hace cuánto que está el centro?

[JP]
25 años. Sí, el año pasado festejamos 25 años.
En todas las entrevistas que hemos tenido digo que se ponga hincapié en
este tipo de instituciones que hace tanto que están.

[CR]
Tanto tiempo que están en los territorios.

[JP]
Exacto. Por algo hace tanto que están y se mantienen.
Es una necesidad y yo traigo el apoyo que tienen que tener este tipo de
instituciones.

[MS]
Le quería preguntar, ¿Cómo es el financiamiento acá?

[JP]
Es una ONG, o sea, hay una comisión directiva que hace beneficio, y
bueno, ahí nosotros tenemos las H y las BPS, que no se cobran por todo,
porque nosotros cobramos por 22 actualmente.
"""
    
    def test_document_to_conversation_flow(self, sample_complete_interview):
        """Test document processing followed by conversation parsing."""
        # Step 1: Document processing
        processor = DocumentProcessor()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(sample_complete_interview)
            temp_path = Path(f.name)
        
        try:
            interview_doc = processor.process_interview(temp_path)
            
            # Verify document processing
            assert interview_doc.id == "58"
            assert interview_doc.location == "Young, Río Negro"
            assert "AM" in interview_doc.text
            
            # Step 2: Conversation parsing
            parser = ConversationParser()
            turns = parser.parse_conversation(interview_doc.text)
            
            # Verify conversation parsing
            assert len(turns) > 0
            speakers = set(turn.speaker for turn in turns)
            assert "AM" in speakers
            assert "CR" in speakers
            assert "JP" in speakers
            assert "MS" in speakers
            
            # Verify turn content
            am_turns = [t for t in turns if t.speaker == "AM"]
            assert len(am_turns) >= 1
            assert "Paysandú" in am_turns[0].text
            
            jp_turns = [t for t in turns if t.speaker == "JP"]
            assert len(jp_turns) >= 2
            assert any("25 años" in turn.text for turn in jp_turns)
            
        finally:
            temp_path.unlink()
    
    @patch('src.database.repository.ConversationRepository')
    def test_conversation_to_database_flow(self, mock_conv_repo, sample_complete_interview, mock_db_session):
        """Test conversation parsing followed by database storage."""
        # Parse conversation
        parser = ConversationParser()
        turns = parser.parse_conversation(sample_complete_interview)
        
        # Mock ExtractedData
        mock_extracted_data = Mock(spec=ExtractedData)
        mock_extracted_data.interview_id = "58"
        mock_extracted_data.interview_date = "2025-05-28"
        mock_extracted_data.interview_time = "09:00"
        mock_extracted_data.location = "Young, Río Negro"
        mock_extracted_data.department = "Río Negro"
        mock_extracted_data.participant_count = 4
        
        # Mock repository
        mock_conv_repo_instance = Mock()
        mock_conv_repo.return_value = mock_conv_repo_instance
        
        repo = ExtractedDataRepository(mock_db_session)
        
        # This should trigger conversation parsing and storage
        repo.save_extracted_data(
            mock_extracted_data, 
            xml_content="<test></test>",
            raw_text=sample_complete_interview
        )
        
        # Verify conversation repository was called
        mock_conv_repo.assert_called_once_with(mock_db_session)
        mock_conv_repo_instance.save_conversation_turns.assert_called_once()
        
        # Verify the turns data structure
        call_args = mock_conv_repo_instance.save_conversation_turns.call_args
        interview_id, turn_dicts = call_args[0]
        
        assert len(turn_dicts) == len(turns)
        assert all('turn_number' in td for td in turn_dicts)
        assert all('speaker' in td for td in turn_dicts)
        assert all('text' in td for td in turn_dicts)
        assert all('word_count' in td for td in turn_dicts)
    
    def test_metadata_consistency(self, sample_complete_interview):
        """Test that metadata is consistent across pipeline components."""
        # Document processing
        processor = DocumentProcessor()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(sample_complete_interview)
            temp_path = Path(f.name)
        
        try:
            interview_doc = processor.process_interview(temp_path)
            
            # Conversation parsing
            parser = ConversationParser()
            turns = parser.parse_conversation(interview_doc.text)
            summary = parser.get_conversation_summary(turns)
            
            # Verify consistency
            assert interview_doc.participant_count >= summary['unique_speakers']
            
            # Word count should be approximately consistent
            # (allowing for differences in counting methods)
            doc_words = interview_doc.metadata['word_count']
            turn_words = summary['total_words']
            
            # Turn words should be less than doc words (excludes metadata)
            assert turn_words < doc_words
            assert turn_words > 0
            
        finally:
            temp_path.unlink()
    
    def test_speaker_identification_accuracy(self, sample_complete_interview):
        """Test that speaker identification is accurate across components."""
        # Document processing for participant count
        processor = DocumentProcessor()
        participant_count = processor._count_participants(sample_complete_interview)
        
        # Conversation parsing for detailed speaker analysis
        parser = ConversationParser()
        turns = parser.parse_conversation(sample_complete_interview)
        summary = parser.get_conversation_summary(turns)
        
        # We should identify the main speakers: AM, CR, JP, MS
        expected_speakers = {"AM", "CR", "JP", "MS"}
        actual_speakers = {s['speaker'] for s in summary['speakers']}
        
        # All expected speakers should be found
        assert expected_speakers.issubset(actual_speakers)
        
        # Participant count should be reasonable
        assert participant_count >= len(expected_speakers)
    
    def test_error_handling_integration(self):
        """Test error handling when components work together."""
        processor = DocumentProcessor()
        parser = ConversationParser()
        
        # Test with malformed file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("Invalid content without proper structure")
            temp_path = Path(f.name)
        
        try:
            # Document processing should still work
            interview_doc = processor.process_interview(temp_path)
            assert interview_doc is not None
            
            # Conversation parsing should handle gracefully
            turns = parser.parse_conversation(interview_doc.text)
            # Should return empty list or minimal turns
            assert isinstance(turns, list)
            
        finally:
            temp_path.unlink()


class TestDataStructureCompatibility:
    """Test that data structures are compatible across components."""
    
    def test_turn_data_database_compatibility(self):
        """Test that ConversationTurn can be converted to database format."""
        from src.pipeline.parsing.conversation_parser import ConversationTurn
        
        # Create sample turn
        turn = ConversationTurn(
            turn_number=1,
            speaker="AM",
            speaker_id=None,
            text="Sample text for testing",
            word_count=4,
            start_line=10,
            end_line=12
        )
        
        # Convert to database format
        turn_dict = {
            'turn_number': turn.turn_number,
            'speaker': turn.speaker,
            'speaker_id': turn.speaker_id,
            'text': turn.text,
            'word_count': turn.word_count,
            'start_time': None,
            'end_time': None
        }
        
        # Verify all required fields are present
        required_fields = [
            'turn_number', 'speaker', 'speaker_id', 'text', 
            'word_count', 'start_time', 'end_time'
        ]
        
        for field in required_fields:
            assert field in turn_dict
    
    def test_interview_document_extraction_compatibility(self, sample_interview_text):
        """Test InterviewDocument compatibility with extraction components."""
        processor = DocumentProcessor()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(sample_interview_text)
            temp_path = Path(f.name)
        
        try:
            interview_doc = processor.process_interview(temp_path)
            
            # Verify structure needed for extraction
            assert hasattr(interview_doc, 'id')
            assert hasattr(interview_doc, 'text')
            assert hasattr(interview_doc, 'date')
            assert hasattr(interview_doc, 'time')
            assert hasattr(interview_doc, 'location')
            assert hasattr(interview_doc, 'participant_count')
            
            # Verify data types
            assert isinstance(interview_doc.id, str)
            assert isinstance(interview_doc.text, str)
            assert isinstance(interview_doc.participant_count, int)
            
        finally:
            temp_path.unlink()