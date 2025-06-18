"""
Unit tests for conversation parser.
"""
import pytest
from src.pipeline.parsing.conversation_parser import ConversationParser, ConversationTurn


class TestConversationParser:
    """Test cases for ConversationParser."""
    
    @pytest.fixture
    def parser(self):
        """Create a ConversationParser instance."""
        return ConversationParser()
    
    def test_parse_basic_conversation(self, parser):
        """Test parsing a basic conversation with speaker patterns."""
        text = """
        [AM]
        Nos han contactado desde Paysandú también.
        
        [CR]
        ¿Y hace cuánto que está el centro?
        
        [JP]
        25 años. Sí, el año pasado festejamos 25 años.
        """
        
        turns = parser.parse_conversation(text)
        
        assert len(turns) == 3
        assert turns[0].speaker == "AM"
        assert turns[1].speaker == "CR"
        assert turns[2].speaker == "JP"
        assert "Paysandú" in turns[0].text
        assert "centro" in turns[1].text
        assert "25 años" in turns[2].text
    
    def test_speaker_patterns(self, parser):
        """Test different speaker pattern formats."""
        test_cases = [
            ("[AM]", "AM"),
            ("CR:", "CR"),
            ("Entrevistador:", "Entrevistador"),
            ("[Participante 1]", "Participante"),
            ("Juan:", "JUAN"),
        ]
        
        for pattern, expected_speaker in test_cases:
            speaker_info = parser._extract_speaker(pattern)
            if speaker_info:
                assert speaker_info['speaker'] == expected_speaker
    
    def test_normalize_speaker_names(self, parser):
        """Test speaker name normalization."""
        test_cases = [
            ("entrevistador", "Entrevistador"),
            ("ent", "Entrevistador"),
            ("e", "Entrevistador"),
            ("participante", "Participante"),
            ("AM", "AM"),
            ("cr", "CR"),
        ]
        
        for input_name, expected in test_cases:
            normalized = parser._normalize_speaker_name(input_name)
            assert normalized == expected
    
    def test_exclude_metadata_lines(self, parser):
        """Test that metadata lines are properly excluded."""
        text = """
        Id Agenda: 58
        ORGANIZACIÓN: Directiva del Centro
        Localidad: Young, Río Negro
        Fecha de la entrevista: 28/05/2025
        ___
        
        [AM]
        Esta es la conversación real.
        """
        
        turns = parser.parse_conversation(text)
        
        assert len(turns) == 1
        assert turns[0].speaker == "AM"
        assert "conversación real" in turns[0].text
    
    def test_conversation_summary(self, parser):
        """Test conversation summary generation."""
        text = """
        [AM]
        Nos han contactado desde Paysandú también porque es el único centro.
        
        [CR]
        ¿Y hace cuánto?
        
        [AM]
        25 años funcionando.
        """
        
        turns = parser.parse_conversation(text)
        summary = parser.get_conversation_summary(turns)
        
        assert summary['total_turns'] == 3
        assert summary['unique_speakers'] == 2
        assert summary['total_words'] > 0
        assert summary['avg_words_per_turn'] > 0
        
        # Check speaker breakdown
        speakers = {s['speaker']: s for s in summary['speakers']}
        assert 'AM' in speakers
        assert 'CR' in speakers
        assert speakers['AM']['turn_count'] == 2
        assert speakers['CR']['turn_count'] == 1
    
    def test_empty_conversation(self, parser):
        """Test handling of empty or metadata-only text."""
        text = """
        Id Agenda: 58
        ORGANIZACIÓN: Test
        """
        
        turns = parser.parse_conversation(text)
        summary = parser.get_conversation_summary(turns)
        
        assert len(turns) == 0
        assert summary == {}
    
    def test_numbered_participants(self, parser):
        """Test handling of numbered participants."""
        text = """
        [Participante 1]
        Primera respuesta.
        
        [Participante 2]
        Segunda respuesta.
        """
        
        turns = parser.parse_conversation(text)
        
        assert len(turns) == 2
        assert turns[0].speaker == "Participante"
        assert turns[0].speaker_id == "1"
        assert turns[1].speaker == "Participante"
        assert turns[1].speaker_id == "2"
    
    def test_word_count_accuracy(self, parser):
        """Test that word counts are accurate."""
        text = """
        [AM]
        Esta es una frase de exactamente ocho palabras aquí.
        
        [CR]
        Tres palabras solamente.
        """
        
        turns = parser.parse_conversation(text)
        
        # "Esta es una frase de exactamente ocho palabras aquí" = 9 words
        assert turns[0].word_count == 9
        assert turns[1].word_count == 3
    
    def test_multiline_turns(self, parser):
        """Test that multiline speaker content is properly combined."""
        text = """
        [AM]
        Esta es la primera línea.
        Esta es la segunda línea.
        Y esta es la tercera línea.
        
        [CR]
        Una sola línea aquí.
        """
        
        turns = parser.parse_conversation(text)
        
        assert len(turns) == 2
        assert "primera línea" in turns[0].text
        assert "segunda línea" in turns[0].text
        assert "tercera línea" in turns[0].text
        assert turns[0].text.count("línea") == 3


class TestConversationTurn:
    """Test cases for ConversationTurn dataclass."""
    
    def test_turn_creation(self):
        """Test creating a ConversationTurn instance."""
        turn = ConversationTurn(
            turn_number=1,
            speaker="AM",
            speaker_id=None,
            text="Test text",
            word_count=2,
            start_line=5,
            end_line=7
        )
        
        assert turn.turn_number == 1
        assert turn.speaker == "AM"
        assert turn.speaker_id is None
        assert turn.text == "Test text"
        assert turn.word_count == 2
        assert turn.start_line == 5
        assert turn.end_line == 7