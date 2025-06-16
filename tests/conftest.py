"""
Shared pytest fixtures for all tests.
"""
import pytest
from pathlib import Path
import tempfile
import shutil
from typing import Dict, Any

from src.pipeline.ingestion.document_processor import InterviewDocument


@pytest.fixture
def test_data_dir():
    """Path to test data directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_interview_document():
    """Create a sample InterviewDocument for testing."""
    return InterviewDocument(
        id="test_001",
        date="2025-05-28",
        time="09:00",
        location="Montevideo",
        department="Montevideo",
        participant_count=2,
        text="""Lugar: Montevideo
        
Entrevistador: ¿Cuáles son las principales prioridades para usted?
Participante: Para mí, la seguridad es lo más importante. También la educación de los niños.
""",
        metadata={
            "filename": "test_interview.txt",
            "text_length": 150,
            "word_count": 25
        },
        file_path="/tmp/test_interview.txt"
    )


@pytest.fixture
def sample_annotation() -> Dict[str, Any]:
    """Create a sample annotation for testing."""
    return {
        "interview_id": "test_001",
        "metadata": {
            "date": "2025-05-28",
            "location": "Montevideo",
            "participant_count": 2
        },
        "national_priorities": [
            {
                "rank": 1,
                "theme": "seguridad",
                "confidence": 0.9,
                "narrative": "La seguridad es fundamental para el bienestar"
            },
            {
                "rank": 2,
                "theme": "educación",
                "confidence": 0.85,
                "narrative": "La educación de los niños es el futuro"
            }
        ],
        "local_priorities": [
            {
                "rank": 1,
                "theme": "iluminación",
                "confidence": 0.8,
                "narrative": "Las calles necesitan mejor iluminación"
            }
        ],
        "themes": [
            {
                "name": "seguridad",
                "emotional_intensity": 0.8,
                "frequency": 3
            },
            {
                "name": "educación",
                "emotional_intensity": 0.6,
                "frequency": 2
            }
        ],
        "processing_metadata": {
            "model": "gpt-4",
            "timestamp": "2025-05-28T09:30:00",
            "confidence": 0.87
        }
    }


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    class MockChoice:
        class MockMessage:
            content = '{"priorities": [], "themes": []}'
        message = MockMessage()
    
    class MockResponse:
        choices = [MockChoice()]
    
    return MockResponse()


@pytest.fixture
def sample_interview_text():
    """Sample interview text for testing."""
    return """Lugar: Young, Río Negro
Fecha: 28 de mayo de 2025
Participantes: Centro Esperanza Young

Entrevistador: Buenos días. ¿Pueden presentarse?

AM: Buenos días. Soy Antonela Merica, psicóloga del Centro Esperanza Young. 
Trabajo en el equipo técnico brindando apoyo a personas con discapacidad.

SL: Soy Silvia Lafluf, presidenta de la comisión de apoyo del centro. 
Llevamos 25 años trabajando por la inclusión.

JP: Juan Poggio, director de la institución. Coordinamos servicios para 
50 personas con discapacidad intelectual.

Entrevistador: ¿Cuáles consideran que son las principales prioridades 
nacionales en este momento?

AM: Sin duda, la inclusión laboral de personas con discapacidad es 
fundamental. Las inserciones laborales que logramos duran máximo seis 
meses porque no hay acompañamiento sostenido.

SL: Exacto. Necesitamos que el Estado garantice apoyos profesionales 
en los lugares de trabajo. No basta con cumplir cuotas, hay que 
asegurar la permanencia.

JP: También es crítico el tema del financiamiento. Necesitamos 700 mil 
pesos mensuales para funcionar, pero los AYEX apenas cubren 150 mil. 
Sobrevivimos vendiendo tortas fritas.

Entrevistador: ¿Y a nivel local?

AM: La continuidad de las políticas departamentales. Cada vez que 
cambia el gobierno, volvemos a empezar de cero.

SL: Y la exoneración de servicios públicos. Pagamos luz y agua como 
cualquier empresa privada, siendo que le solucionamos un problema 
al Estado.
"""