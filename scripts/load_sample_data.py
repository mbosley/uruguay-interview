#!/usr/bin/env python3
"""
Load sample data into the database for dashboard testing
"""
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.database.connection import DatabaseConnection
from src.database.models import Interview, Annotation, Priority, Theme
from src.config.config_loader import get_config
from src.pipeline.extraction.data_extractor import DataExtractor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_sample_data():
    """Load existing XML annotation into database."""
    config = get_config()
    db = DatabaseConnection(config.database.url)
    extractor = DataExtractor()
    
    # Path to existing XML annotation
    xml_path = Path("data/processed/annotations/xml/058_annotation.xml")
    
    if not xml_path.exists():
        logger.error(f"XML file not found: {xml_path}")
        return False
    
    try:
        # Extract data from XML
        logger.info(f"Extracting data from {xml_path}")
        extracted_data = extractor.extract_from_xml(xml_path)
        
        with db.get_session() as session:
            # Create interview record
            interview = Interview(
                interview_id=extracted_data.interview_id,
                date=extracted_data.interview_date,
                time=extracted_data.interview_time,
                location=extracted_data.location,
                department=extracted_data.department or "Río Negro",
                participant_count=extracted_data.participant_count,
                file_path=str(xml_path),
                file_type="xml",
                word_count=8548,  # From the XML metadata
                status="completed",
                processed_at=datetime.utcnow()
            )
            session.add(interview)
            session.flush()
            
            # Create annotation record
            annotation = Annotation(
                interview_id=interview.id,
                model_provider=extracted_data.model_used.split('/')[0] if '/' in extracted_data.model_used else "openai",
                model_name=extracted_data.model_used.split('/')[-1] if '/' in extracted_data.model_used else extracted_data.model_used,
                temperature=0.3,
                xml_content=xml_path.read_text(),
                dominant_emotion=extracted_data.dominant_emotion,
                overall_sentiment=extracted_data.overall_sentiment,
                confidence_score=extracted_data.confidence_score,
                annotation_completeness=extracted_data.annotation_completeness,
                has_validation_errors=extracted_data.has_validation_errors,
                processing_time=52.2  # From XML metadata
            )
            session.add(annotation)
            session.flush()
            
            # Add priorities
            for p in extracted_data.national_priorities:
                priority = Priority(
                    interview_id=interview.id,
                    scope="national",
                    rank=p.rank,
                    category=p.category,
                    subcategory=p.subcategory,
                    description=p.description,
                    sentiment=p.sentiment,
                    evidence_type=p.evidence_type,
                    confidence=p.confidence
                )
                session.add(priority)
            
            for p in extracted_data.local_priorities:
                priority = Priority(
                    interview_id=interview.id,
                    scope="local",
                    rank=p.rank,
                    category=p.category,
                    subcategory=p.subcategory,
                    description=p.description,
                    sentiment=p.sentiment,
                    evidence_type=p.evidence_type,
                    confidence=p.confidence
                )
                session.add(priority)
            
            # Add themes
            for theme_name in extracted_data.themes:
                theme = Theme(
                    interview_id=interview.id,
                    theme=theme_name,
                    frequency=1
                )
                session.add(theme)
            
            session.commit()
            logger.info(f"Successfully loaded interview {extracted_data.interview_id} into database")
            
            # Verify data was loaded
            interview_count = session.query(Interview).count()
            priority_count = session.query(Priority).count()
            theme_count = session.query(Theme).count()
            
            logger.info(f"Database now contains:")
            logger.info(f"  - {interview_count} interviews")
            logger.info(f"  - {priority_count} priorities")
            logger.info(f"  - {theme_count} themes")
            
        return True
        
    except Exception as e:
        logger.error(f"Failed to load sample data: {e}")
        return False

if __name__ == "__main__":
    success = load_sample_data()
    sys.exit(0 if success else 1)