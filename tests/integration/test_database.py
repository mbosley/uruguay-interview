"""
Database integration tests.
Tests database schema creation, data storage, and querying.
"""
import pytest
import tempfile
import sqlite3
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.database.models import Base, Interview, Turn, Annotation, Priority as PriorityModel, Theme
from src.database.repository import ExtractedDataRepository, ConversationRepository
from src.pipeline.parsing.conversation_parser import ConversationParser
from src.pipeline.extraction.data_extractor import ExtractedData, Priority as PriorityData


class TestDatabaseSchema:
    """Test database schema creation and basic operations."""
    
    @pytest.fixture
    def temp_db_url(self):
        """Create a temporary SQLite database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db_url = f"sqlite:///{db_path}"
        yield db_url
        
        # Cleanup
        Path(db_path).unlink(missing_ok=True)
    
    @pytest.fixture
    def db_engine(self, temp_db_url):
        """Create database engine with schema."""
        engine = create_engine(temp_db_url)
        Base.metadata.create_all(engine)
        return engine
    
    @pytest.fixture
    def db_session(self, db_engine):
        """Create database session."""
        Session = sessionmaker(bind=db_engine)
        session = Session()
        yield session
        session.close()
    
    def test_database_schema_creation(self, db_engine):
        """Test that all tables are created correctly."""
        # Check that all expected tables exist
        inspector = None
        try:
            from sqlalchemy import inspect
            inspector = inspect(db_engine)
            table_names = inspector.get_table_names()
        except ImportError:
            # Fallback for older SQLAlchemy versions
            with db_engine.connect() as conn:
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
                table_names = [row[0] for row in result]
        
        expected_tables = [
            'interviews', 'annotations', 'priorities', 'themes', 'emotions',
            'concerns', 'suggestions', 'geographic_mentions', 'demographic_indicators',
            'turns', 'processing_logs', 'daily_summaries'
        ]
        
        for table in expected_tables:
            assert table in table_names, f"Table {table} not found in database"
    
    def test_interview_crud_operations(self, db_session):
        """Test basic CRUD operations on Interview model."""
        # Create
        interview = Interview(
            interview_id="TEST_001",
            date="2025-06-16",
            time="10:00",
            location="Test Location",
            department="Test Department",
            participant_count=3,
            raw_text="Sample interview text for testing",
            word_count=6,
            status="completed"
        )
        db_session.add(interview)
        db_session.commit()
        
        # Read
        retrieved = db_session.query(Interview).filter_by(interview_id="TEST_001").first()
        assert retrieved is not None
        assert retrieved.location == "Test Location"
        assert retrieved.word_count == 6
        assert retrieved.raw_text == "Sample interview text for testing"
        
        # Update
        retrieved.status = "processed"
        db_session.commit()
        
        updated = db_session.query(Interview).filter_by(interview_id="TEST_001").first()
        assert updated.status == "processed"
        
        # Delete
        db_session.delete(updated)
        db_session.commit()
        
        deleted = db_session.query(Interview).filter_by(interview_id="TEST_001").first()
        assert deleted is None
    
    def test_conversation_turns_storage(self, db_session):
        """Test storing and retrieving conversation turns."""
        # Create interview
        interview = Interview(
            interview_id="CONV_001",
            date="2025-06-16",
            time="10:00",
            location="Test Location",
            department="Test Department",
            participant_count=2,
            raw_text="[AM] Hello [CR] Hi there",
            word_count=4,
            status="completed"
        )
        db_session.add(interview)
        db_session.flush()
        
        # Create turns
        turns = [
            Turn(
                interview_id=interview.id,
                turn_number=1,
                speaker="AM",
                text="Hello",
                word_count=1
            ),
            Turn(
                interview_id=interview.id,
                turn_number=2,
                speaker="CR", 
                text="Hi there",
                word_count=2
            )
        ]
        
        for turn in turns:
            db_session.add(turn)
        db_session.commit()
        
        # Retrieve and verify
        retrieved_turns = db_session.query(Turn).filter_by(interview_id=interview.id).order_by(Turn.turn_number).all()
        assert len(retrieved_turns) == 2
        assert retrieved_turns[0].speaker == "AM"
        assert retrieved_turns[0].text == "Hello"
        assert retrieved_turns[1].speaker == "CR"
        assert retrieved_turns[1].text == "Hi there"
        
        # Test relationship
        interview_with_turns = db_session.query(Interview).filter_by(interview_id="CONV_001").first()
        assert len(interview_with_turns.turns) == 2
    
    def test_priorities_and_themes_storage(self, db_session):
        """Test storing priorities and themes."""
        # Create interview
        interview = Interview(
            interview_id="PRIO_001",
            date="2025-06-16",
            time="10:00",
            location="Test Location",
            department="Test Department",
            participant_count=1,
            raw_text="Priorities discussion",
            word_count=2,
            status="completed"
        )
        db_session.add(interview)
        db_session.flush()
        
        # Create priorities
        priorities = [
            PriorityModel(
                interview_id=interview.id,
                scope="national",
                rank=1,
                category="education",
                description="Improve education system",
                sentiment="positive",
                confidence=0.9
            ),
            PriorityModel(
                interview_id=interview.id,
                scope="local",
                rank=1,
                category="infrastructure",
                description="Fix local roads",
                sentiment="neutral",
                confidence=0.8
            )
        ]
        
        for priority in priorities:
            db_session.add(priority)
        
        # Create themes
        themes = [
            Theme(
                interview_id=interview.id,
                theme="education",
                frequency=3
            ),
            Theme(
                interview_id=interview.id,
                theme="infrastructure",
                frequency=2
            )
        ]
        
        for theme in themes:
            db_session.add(theme)
        
        db_session.commit()
        
        # Verify storage
        interview_priorities = db_session.query(PriorityModel).filter_by(interview_id=interview.id).all()
        assert len(interview_priorities) == 2
        
        national_priorities = [p for p in interview_priorities if p.scope == "national"]
        local_priorities = [p for p in interview_priorities if p.scope == "local"]
        assert len(national_priorities) == 1
        assert len(local_priorities) == 1
        
        interview_themes = db_session.query(Theme).filter_by(interview_id=interview.id).all()
        assert len(interview_themes) == 2


class TestRepositoryIntegration:
    """Test repository pattern with real database."""
    
    @pytest.fixture
    def temp_db_url(self):
        """Create a temporary SQLite database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db_url = f"sqlite:///{db_path}"
        yield db_url
        
        # Cleanup
        Path(db_path).unlink(missing_ok=True)
    
    @pytest.fixture
    def db_session(self, temp_db_url):
        """Create database session with schema."""
        engine = create_engine(temp_db_url)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()
    
    def test_conversation_repository(self, db_session):
        """Test ConversationRepository operations."""
        # Create interview
        interview = Interview(
            interview_id="REPO_001",
            date="2025-06-16",
            time="10:00",
            location="Test Location",
            department="Test Department",
            participant_count=2,
            raw_text="Sample conversation",
            word_count=2,
            status="completed"
        )
        db_session.add(interview)
        db_session.flush()
        
        # Test conversation repository
        conv_repo = ConversationRepository(db_session)
        
        # Save turns
        turn_dicts = [
            {
                'turn_number': 1,
                'speaker': 'AM',
                'speaker_id': None,
                'text': 'Hello everyone',
                'word_count': 2,
                'start_time': None,
                'end_time': None
            },
            {
                'turn_number': 2,
                'speaker': 'CR',
                'speaker_id': None,
                'text': 'Hi there',
                'word_count': 2,
                'start_time': None,
                'end_time': None
            }
        ]
        
        conv_repo.save_conversation_turns(interview.id, turn_dicts)
        db_session.commit()
        
        # Retrieve turns
        retrieved_turns = conv_repo.get_conversation_turns(interview.id)
        assert len(retrieved_turns) == 2
        assert retrieved_turns[0].turn_number == 1
        assert retrieved_turns[0].speaker == 'AM'
        
        # Get speaker statistics
        stats = conv_repo.get_speaker_statistics(interview.id)
        assert stats['total_turns'] == 2
        assert stats['unique_speakers'] == 2
        assert stats['total_words'] == 4
    
    def test_extracted_data_repository(self, db_session):
        """Test ExtractedDataRepository with conversation parsing."""
        # Create sample extracted data
        from datetime import datetime
        extracted_data = ExtractedData(
            interview_id="EXTRACT_001",
            interview_date="2025-06-16",
            interview_time="10:00",
            location="Test Location",
            department="Test Department",
            participant_count=2,
            annotation_timestamp=datetime.now(),
            model_used="test-model",
            confidence_score=0.85,
            national_priorities=[
                PriorityData(
                    rank=1,
                    category="education",
                    subcategory="primary",
                    description="Improve primary education",
                    sentiment="positive",
                    evidence_type="personal_experience",
                    confidence=0.9
                )
            ],
            local_priorities=[],
            themes=["education", "children"],
            emotions=[],
            concerns=[],
            suggestions=[],
            geographic_mentions=["Test Location"],
            dominant_emotion="hopeful",
            overall_sentiment="positive",
            annotation_completeness=0.95,
            has_validation_errors=False,
            inferred_age_group="30-40",
            inferred_socioeconomic="middle"
        )
        
        # Sample raw text with conversation
        raw_text = """
        [AM]
        We need better education for our children.
        
        [CR]
        I agree. What specific improvements do you suggest?
        
        [AM]
        More funding for primary schools and teacher training.
        """
        
        # Save using repository
        repo = ExtractedDataRepository(db_session)
        repo.save_extracted_data(extracted_data, xml_content="<test></test>", raw_text=raw_text)
        
        # Verify interview was created
        interview = db_session.query(Interview).filter_by(interview_id="EXTRACT_001").first()
        assert interview is not None
        assert interview.raw_text == raw_text
        assert interview.word_count == len(raw_text.split())
        
        # Verify priorities were created
        priorities = db_session.query(PriorityModel).filter_by(interview_id=interview.id).all()
        assert len(priorities) == 1
        assert priorities[0].category == "education"
        
        # Verify conversation turns were created
        turns = db_session.query(Turn).filter_by(interview_id=interview.id).all()
        assert len(turns) > 0  # Should have parsed conversation turns
        
        # Verify themes were created
        themes = db_session.query(Theme).filter_by(interview_id=interview.id).all()
        assert len(themes) == 2  # "education" and "children"


class TestDatabaseQueries:
    """Test complex database queries and aggregations."""
    
    @pytest.fixture
    def populated_db(self):
        """Create a database with sample data."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db_url = f"sqlite:///{db_path}"
        engine = create_engine(db_url)
        Base.metadata.create_all(engine)
        
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Create sample interviews
        interviews = [
            Interview(
                interview_id="QUERY_001",
                date="2025-06-16",
                time="10:00",
                location="Montevideo",
                department="Montevideo",
                participant_count=3,
                raw_text="Sample interview 1",
                word_count=10,
                status="completed"
            ),
            Interview(
                interview_id="QUERY_002", 
                date="2025-06-16",
                time="14:00",
                location="Canelones",
                department="Canelones",
                participant_count=2,
                raw_text="Sample interview 2",
                word_count=15,
                status="completed"
            )
        ]
        
        for interview in interviews:
            session.add(interview)
        session.flush()
        
        # Add priorities
        priorities = [
            PriorityModel(interview_id=interviews[0].id, scope="national", rank=1, category="education", description="Education priority"),
            PriorityModel(interview_id=interviews[0].id, scope="local", rank=1, category="infrastructure", description="Infrastructure priority"),
            PriorityModel(interview_id=interviews[1].id, scope="national", rank=1, category="healthcare", description="Healthcare priority"),
            PriorityModel(interview_id=interviews[1].id, scope="local", rank=1, category="transportation", description="Transportation priority")
        ]
        
        for priority in priorities:
            session.add(priority)
        
        session.commit()
        session.close()
        
        yield db_url
        
        # Cleanup
        Path(db_path).unlink(missing_ok=True)
    
    def test_interview_aggregations(self, populated_db):
        """Test aggregation queries on interview data."""
        engine = create_engine(populated_db)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # Count interviews by department
            from sqlalchemy import func
            department_counts = session.query(
                Interview.department,
                func.count(Interview.id).label('count')
            ).group_by(Interview.department).all()
            
            assert len(department_counts) == 2
            departments = {row[0]: row[1] for row in department_counts}
            assert departments['Montevideo'] == 1
            assert departments['Canelones'] == 1
            
            # Total word count
            total_words = session.query(func.sum(Interview.word_count)).scalar()
            assert total_words == 25  # 10 + 15
            
            # Average participant count
            avg_participants = session.query(func.avg(Interview.participant_count)).scalar()
            assert avg_participants == 2.5  # (3 + 2) / 2
            
        finally:
            session.close()
    
    def test_priority_analysis_queries(self, populated_db):
        """Test priority analysis queries."""
        engine = create_engine(populated_db)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            from sqlalchemy import func
            
            # Top priority categories
            priority_counts = session.query(
                PriorityModel.category,
                func.count(PriorityModel.id).label('count')
            ).group_by(PriorityModel.category).order_by(
                func.count(PriorityModel.id).desc()
            ).all()
            
            assert len(priority_counts) == 4
            categories = [row[0] for row in priority_counts]
            assert 'education' in categories
            assert 'healthcare' in categories
            assert 'infrastructure' in categories
            assert 'transportation' in categories
            
            # National vs Local priorities
            scope_counts = session.query(
                PriorityModel.scope,
                func.count(PriorityModel.id).label('count')
            ).group_by(PriorityModel.scope).all()
            
            scope_dict = {row[0]: row[1] for row in scope_counts}
            assert scope_dict['national'] == 2
            assert scope_dict['local'] == 2
            
        finally:
            session.close()
    
    def test_interview_priority_joins(self, populated_db):
        """Test joins between interviews and priorities."""
        engine = create_engine(populated_db) 
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # Get interviews with their priorities
            results = session.query(Interview, PriorityModel).join(
                PriorityModel, Interview.id == PriorityModel.interview_id
            ).filter(PriorityModel.scope == 'national').all()
            
            assert len(results) == 2
            
            # Verify join results
            interview_priorities = {}
            for interview, priority in results:
                if interview.interview_id not in interview_priorities:
                    interview_priorities[interview.interview_id] = []
                interview_priorities[interview.interview_id].append(priority.category)
            
            assert 'education' in interview_priorities['QUERY_001']
            assert 'healthcare' in interview_priorities['QUERY_002']
            
        finally:
            session.close()