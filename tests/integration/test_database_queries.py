"""
Integration tests for database querying capabilities.
Tests accessing individual interviews, turns with conditions, and complex queries.
"""
import pytest
import tempfile
from pathlib import Path
from sqlalchemy import create_engine, and_, or_, func
from sqlalchemy.orm import sessionmaker, joinedload

from src.database.models import Base, Interview, Turn, Priority, Theme


@pytest.fixture
def populated_database():
    """Create a database populated with realistic test data."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Create sample interviews with conversations
        interviews = [
            Interview(
                interview_id="INT_001",
                date="2025-05-28",
                time="09:00",
                location="Montevideo Centro",
                department="Montevideo",
                participant_count=3,
                raw_text="[AM] Buenos días. [CR] Hola, ¿cómo están? [JP] Muy bien, gracias.",
                word_count=12,
                status="completed"
            ),
            Interview(
                interview_id="INT_002", 
                date="2025-05-28",
                time="14:00",
                location="Canelones Norte",
                department="Canelones",
                participant_count=2,
                raw_text="[Entrevistador] ¿Cuáles son sus prioridades? [Participante] La educación es lo más importante.",
                word_count=15,
                status="completed"
            ),
            Interview(
                interview_id="INT_003",
                date="2025-05-29", 
                time="10:30",
                location="Paysandú Centro",
                department="Paysandú",
                participant_count=4,
                raw_text="[MOD] Hablemos de seguridad. [P1] Es un tema complicado. [P2] Necesitamos más policías.",
                word_count=16,
                status="completed"
            )
        ]
        
        for interview in interviews:
            session.add(interview)
        session.flush()
        
        # Create conversation turns
        turns_data = [
            # Interview 1 turns
            (interviews[0].id, 1, "AM", "Buenos días.", 2),
            (interviews[0].id, 2, "CR", "Hola, ¿cómo están?", 3),
            (interviews[0].id, 3, "JP", "Muy bien, gracias.", 3),
            (interviews[0].id, 4, "AM", "¿Cuáles son las prioridades más importantes para ustedes?", 9),
            (interviews[0].id, 5, "CR", "La educación de nuestros hijos es fundamental.", 8),
            
            # Interview 2 turns
            (interviews[1].id, 1, "Entrevistador", "¿Cuáles son sus prioridades?", 5),
            (interviews[1].id, 2, "Participante", "La educación es lo más importante.", 6),
            (interviews[1].id, 3, "Entrevistador", "¿Y en el ámbito local?", 5),
            (interviews[1].id, 4, "Participante", "Mejorar la infraestructura vial.", 4),
            
            # Interview 3 turns  
            (interviews[2].id, 1, "MOD", "Hablemos de seguridad.", 3),
            (interviews[2].id, 2, "P1", "Es un tema complicado.", 4),
            (interviews[2].id, 3, "P2", "Necesitamos más policías.", 3),
            (interviews[2].id, 4, "MOD", "¿Qué otras soluciones proponen?", 5),
            (interviews[2].id, 5, "P1", "Mayor iluminación en las calles.", 5),
        ]
        
        for interview_id, turn_num, speaker, text, word_count in turns_data:
            turn = Turn(
                interview_id=interview_id,
                turn_number=turn_num,
                speaker=speaker,
                text=text,
                word_count=word_count
            )
            session.add(turn)
        
        # Create priorities
        priorities = [
            Priority(interview_id=interviews[0].id, scope="national", rank=1, category="education", 
                    description="Mejorar la educación pública", sentiment="positive", confidence=0.9),
            Priority(interview_id=interviews[0].id, scope="local", rank=1, category="infrastructure",
                    description="Arreglar calles del barrio", sentiment="neutral", confidence=0.8),
            
            Priority(interview_id=interviews[1].id, scope="national", rank=1, category="education",
                    description="Acceso universal a educación", sentiment="positive", confidence=0.95),
            Priority(interview_id=interviews[1].id, scope="local", rank=1, category="infrastructure", 
                    description="Mejorar carreteras locales", sentiment="neutral", confidence=0.7),
            
            Priority(interview_id=interviews[2].id, scope="national", rank=1, category="security",
                    description="Aumentar seguridad ciudadana", sentiment="negative", confidence=0.85),
            Priority(interview_id=interviews[2].id, scope="local", rank=1, category="security",
                    description="Más patrullaje nocturno", sentiment="negative", confidence=0.8),
        ]
        
        for priority in priorities:
            session.add(priority)
        
        # Create themes
        themes = [
            Theme(interview_id=interviews[0].id, theme="education", frequency=3),
            Theme(interview_id=interviews[0].id, theme="children", frequency=2),
            Theme(interview_id=interviews[1].id, theme="education", frequency=2),
            Theme(interview_id=interviews[1].id, theme="infrastructure", frequency=1),
            Theme(interview_id=interviews[2].id, theme="security", frequency=4),
            Theme(interview_id=interviews[2].id, theme="policing", frequency=2),
        ]
        
        for theme in themes:
            session.add(theme)
        
        session.commit()
        yield session
        
    finally:
        session.close()
        Path(db_path).unlink(missing_ok=True)


class TestIndividualInterviewAccess:
    """Test accessing individual interviews with various filters."""
    
    def test_get_interview_by_id(self, populated_database):
        """Test retrieving a specific interview by ID."""
        session = populated_database
        
        interview = session.query(Interview).filter(
            Interview.interview_id == "INT_001"
        ).first()
        
        assert interview is not None
        assert interview.interview_id == "INT_001"
        assert interview.location == "Montevideo Centro"
        assert interview.department == "Montevideo"
    
    def test_get_interviews_by_date(self, populated_database):
        """Test filtering interviews by date."""
        session = populated_database
        
        may_28_interviews = session.query(Interview).filter(
            Interview.date == "2025-05-28"
        ).all()
        
        assert len(may_28_interviews) == 2
        interview_ids = [i.interview_id for i in may_28_interviews]
        assert "INT_001" in interview_ids
        assert "INT_002" in interview_ids
    
    def test_get_interviews_by_department(self, populated_database):
        """Test filtering interviews by department."""
        session = populated_database
        
        montevideo_interviews = session.query(Interview).filter(
            Interview.department == "Montevideo"
        ).all()
        
        assert len(montevideo_interviews) == 1
        assert montevideo_interviews[0].interview_id == "INT_001"
    
    def test_get_interviews_by_participant_count(self, populated_database):
        """Test filtering by participant count."""
        session = populated_database
        
        # Interviews with 3+ participants
        large_interviews = session.query(Interview).filter(
            Interview.participant_count >= 3
        ).all()
        
        assert len(large_interviews) == 2
        interview_ids = [i.interview_id for i in large_interviews]
        assert "INT_001" in interview_ids
        assert "INT_003" in interview_ids


class TestTurnAccessWithConditions:
    """Test accessing turns with various conditions and filters."""
    
    def test_get_turns_for_specific_interview(self, populated_database):
        """Test retrieving all turns for a specific interview."""
        session = populated_database
        
        interview = session.query(Interview).filter(
            Interview.interview_id == "INT_001"
        ).first()
        
        turns = session.query(Turn).filter(
            Turn.interview_id == interview.id
        ).order_by(Turn.turn_number).all()
        
        assert len(turns) == 5
        assert turns[0].speaker == "AM"
        assert turns[0].text == "Buenos días."
        assert turns[4].speaker == "CR"
        assert "educación" in turns[4].text
    
    def test_get_turns_by_speaker(self, populated_database):
        """Test filtering turns by speaker."""
        session = populated_database
        
        am_turns = session.query(Turn).filter(Turn.speaker == "AM").all()
        assert len(am_turns) == 2
        
        participant_turns = session.query(Turn).filter(
            Turn.speaker == "Participante"
        ).all()
        assert len(participant_turns) == 2
    
    def test_get_turns_by_word_count(self, populated_database):
        """Test filtering turns by word count."""
        session = populated_database
        
        # Long turns (5+ words)
        long_turns = session.query(Turn).filter(Turn.word_count >= 5).all()
        assert len(long_turns) >= 5
        
        # Short turns (3 or fewer words)
        short_turns = session.query(Turn).filter(Turn.word_count <= 3).all()
        assert len(short_turns) >= 3
    
    def test_get_turns_with_keywords(self, populated_database):
        """Test filtering turns containing specific keywords."""
        session = populated_database
        
        education_turns = session.query(Turn).filter(
            Turn.text.contains("educación")
        ).all()
        assert len(education_turns) == 2
        
        security_turns = session.query(Turn).filter(
            Turn.text.contains("seguridad")
        ).all()
        assert len(security_turns) == 1
    
    def test_get_turns_with_complex_conditions(self, populated_database):
        """Test turns with complex multi-condition filters."""
        session = populated_database
        
        # Participant turns in specific interview
        participant_turns_int002 = session.query(Turn).join(Interview).filter(
            and_(
                Interview.interview_id == "INT_002",
                Turn.speaker == "Participante"
            )
        ).all()
        
        assert len(participant_turns_int002) == 2
        
        # Long turns by interviewers
        interviewer_long_turns = session.query(Turn).filter(
            and_(
                or_(
                    Turn.speaker == "Entrevistador",
                    Turn.speaker == "MOD",
                    Turn.speaker == "AM"
                ),
                Turn.word_count >= 5
            )
        ).all()
        
        assert len(interviewer_long_turns) >= 2


class TestInterviewTurnRelationships:
    """Test relationships between interviews and turns."""
    
    def test_interview_turns_relationship(self, populated_database):
        """Test accessing turns through interview relationship."""
        session = populated_database
        
        interview = session.query(Interview).options(
            joinedload(Interview.turns)
        ).filter(Interview.interview_id == "INT_003").first()
        
        assert len(interview.turns) == 5
        assert interview.turns[0].turn_number == 1
        assert interview.turns[0].speaker == "MOD"
    
    def test_turn_interview_backref(self, populated_database):
        """Test accessing interview from turn via backref."""
        session = populated_database
        
        turn = session.query(Turn).filter(
            Turn.text.contains("seguridad")
        ).first()
        
        assert turn.interview.interview_id == "INT_003"
        assert turn.interview.department == "Paysandú"
    
    def test_turn_statistics_per_interview(self, populated_database):
        """Test aggregating turn statistics by interview."""
        session = populated_database
        
        stats = session.query(
            Interview.interview_id,
            func.count(Turn.id).label('turn_count'),
            func.sum(Turn.word_count).label('total_words'),
            func.avg(Turn.word_count).label('avg_words_per_turn')
        ).join(Turn).group_by(Interview.id).all()
        
        assert len(stats) == 3
        
        # Find INT_001 stats
        int_001_stats = next(s for s in stats if s[0] == "INT_001")
        assert int_001_stats[1] == 5  # turn_count
        assert int_001_stats[2] == 25  # total_words (2+3+3+9+8)


class TestComplexQueries:
    """Test complex multi-table queries and joins."""
    
    def test_interviews_with_priorities_and_themes(self, populated_database):
        """Test loading interviews with related priorities and themes."""
        session = populated_database
        
        interviews = session.query(Interview).options(
            joinedload(Interview.priorities),
            joinedload(Interview.themes),
            joinedload(Interview.turns)
        ).all()
        
        assert len(interviews) == 3
        
        # Check that each interview has expected related data
        for interview in interviews:
            assert len(interview.priorities) == 2  # Each has national + local
            assert len(interview.themes) >= 2
            assert len(interview.turns) >= 4
    
    def test_education_related_interviews(self, populated_database):
        """Test finding interviews related to education."""
        session = populated_database
        
        # Interviews with education priorities OR turns mentioning education
        education_interviews = session.query(Interview).filter(
            or_(
                Interview.id.in_(
                    session.query(Priority.interview_id).filter(
                        Priority.category == "education"
                    )
                ),
                Interview.id.in_(
                    session.query(Turn.interview_id).filter(
                        Turn.text.contains("educación")
                    )
                )
            )
        ).distinct().all()
        
        assert len(education_interviews) == 2  # INT_001 and INT_002
    
    def test_speaker_participation_analysis(self, populated_database):
        """Test analyzing speaker participation across interviews."""
        session = populated_database
        
        speaker_stats = session.query(
            Turn.speaker,
            func.count(Turn.id).label('total_turns'),
            func.count(func.distinct(Turn.interview_id)).label('interviews_participated'),
            func.sum(Turn.word_count).label('total_words')
        ).group_by(Turn.speaker).all()
        
        # Should have stats for AM, CR, JP, Entrevistador, Participante, MOD, P1, P2
        assert len(speaker_stats) >= 6
        
        # Find AM's stats (appears in INT_001)
        am_stats = next((s for s in speaker_stats if s[0] == "AM"), None)
        assert am_stats is not None
        assert am_stats[1] == 2  # total_turns
        assert am_stats[2] == 1  # interviews_participated


class TestAdvancedFilteringAndAggregation:
    """Test advanced filtering and aggregation capabilities."""
    
    def test_department_statistics(self, populated_database):
        """Test aggregating statistics by department."""
        session = populated_database
        
        dept_stats = session.query(
            Interview.department,
            func.count(Interview.id).label('interview_count'),
            func.sum(Interview.participant_count).label('total_participants'),
            func.avg(Interview.word_count).label('avg_words')
        ).group_by(Interview.department).all()
        
        assert len(dept_stats) == 3  # Montevideo, Canelones, Paysandú
        
        # Find Montevideo stats
        montevideo_stats = next(s for s in dept_stats if s[0] == "Montevideo")
        assert montevideo_stats[1] == 1  # interview_count
        assert montevideo_stats[2] == 3  # total_participants
    
    def test_priority_frequency_analysis(self, populated_database):
        """Test analyzing priority frequency by category and scope."""
        session = populated_database
        
        priority_freq = session.query(
            Priority.category,
            Priority.scope,
            func.count(Priority.id).label('count')
        ).group_by(Priority.category, Priority.scope).all()
        
        # Should have education (national), education (local), etc.
        education_national = next((p for p in priority_freq 
                                 if p[0] == "education" and p[1] == "national"), None)
        assert education_national is not None
        assert education_national[2] == 2  # Two interviews have national education priorities
    
    def test_high_confidence_priority_filtering(self, populated_database):
        """Test filtering by priority confidence levels."""
        session = populated_database
        
        # High confidence priorities (>= 0.9)
        high_confidence = session.query(Priority).filter(
            Priority.confidence >= 0.9
        ).all()
        
        assert len(high_confidence) >= 2
        
        # Interviews with high confidence priorities
        high_conf_interviews = session.query(Interview).join(Priority).filter(
            Priority.confidence >= 0.9
        ).distinct().all()
        
        assert len(high_conf_interviews) >= 2
    
    def test_turn_sequence_analysis(self, populated_database):
        """Test analyzing turn sequences and patterns."""
        session = populated_database
        
        # Get consecutive turns by the same speaker in an interview
        int_001_turns = session.query(Turn).join(Interview).filter(
            Interview.interview_id == "INT_001"
        ).order_by(Turn.turn_number).all()
        
        # Check for speaker transitions
        speaker_changes = 0
        prev_speaker = None
        for turn in int_001_turns:
            if prev_speaker and turn.speaker != prev_speaker:
                speaker_changes += 1
            prev_speaker = turn.speaker
        
        assert speaker_changes >= 3  # Should have multiple speaker changes
    
    def test_date_range_filtering(self, populated_database):
        """Test filtering across date ranges."""
        session = populated_database
        
        # All interviews in date range
        date_range_interviews = session.query(Interview).filter(
            Interview.date.between("2025-05-28", "2025-05-29")
        ).all()
        
        assert len(date_range_interviews) == 3  # All test interviews
        
        # Turns from specific date
        may_28_turns = session.query(Turn).join(Interview).filter(
            Interview.date == "2025-05-28"
        ).all()
        
        assert len(may_28_turns) == 9  # 5 from INT_001 + 4 from INT_002