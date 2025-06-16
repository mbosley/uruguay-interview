"""
Structured data extraction from XML annotations (Layer 2).
Extracts quantitative insights from qualitative annotations.
"""
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Priority:
    """Represents a citizen priority."""
    rank: int
    category: str
    subcategory: Optional[str]
    description: str
    sentiment: Optional[str] = None
    evidence_type: Optional[str] = None
    confidence: float = 1.0


@dataclass
class Emotion:
    """Represents an emotional expression."""
    type: str
    intensity: str  # low, medium, high
    target: Optional[str] = None
    context: str = ""


@dataclass
class ExtractedData:
    """Structured data extracted from an interview annotation."""
    # Interview metadata
    interview_id: str
    interview_date: str
    interview_time: str
    location: str
    department: Optional[str]
    participant_count: int
    
    # Processing metadata
    annotation_timestamp: datetime
    model_used: str
    confidence_score: float
    
    # Interview-level data
    dominant_emotion: Optional[str] = None
    overall_sentiment: str = "neutral"  # positive, negative, neutral, mixed
    
    # Priorities
    national_priorities: List[Priority] = field(default_factory=list)
    local_priorities: List[Priority] = field(default_factory=list)
    
    # Thematic content
    themes: List[str] = field(default_factory=list)
    concerns: List[Dict[str, Any]] = field(default_factory=list)
    suggestions: List[Dict[str, Any]] = field(default_factory=list)
    
    # Emotional analysis
    emotions: List[Emotion] = field(default_factory=list)
    
    # Evidence and argumentation
    evidence_types: Dict[str, int] = field(default_factory=dict)
    
    # Geographic references
    geographic_mentions: List[str] = field(default_factory=list)
    
    # Demographic indicators (inferred)
    inferred_age_group: Optional[str] = None
    inferred_socioeconomic: Optional[str] = None
    
    # Quality metrics
    annotation_completeness: float = 0.0
    has_validation_errors: bool = False
    validation_notes: List[str] = field(default_factory=list)


class DataExtractor:
    """Extracts structured data from XML annotations."""
    
    def __init__(self):
        """Initialize the data extractor."""
        self.priority_categories = {
            "security": ["crime", "safety", "police", "violence"],
            "education": ["schools", "teachers", "students", "university"],
            "healthcare": ["hospital", "doctors", "health", "medical"],
            "economy": ["jobs", "employment", "wages", "cost of living"],
            "infrastructure": ["roads", "transport", "utilities", "housing"],
            "social": ["inequality", "poverty", "assistance", "community"],
            "environment": ["pollution", "climate", "waste", "parks"],
            "governance": ["corruption", "transparency", "participation"]
        }
    
    def extract_from_xml(self, xml_path: Path) -> ExtractedData:
        """
        Extract structured data from an XML annotation file.
        
        Args:
            xml_path: Path to the XML annotation file
            
        Returns:
            ExtractedData object with all extracted information
        """
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # Extract metadata
            metadata = self._extract_metadata(root)
            
            # Create base extracted data
            extracted = ExtractedData(
                interview_id=metadata.get("id", "unknown"),
                interview_date=metadata.get("date", ""),
                interview_time=metadata.get("time", ""),
                location=metadata.get("location", ""),
                department=metadata.get("department"),
                participant_count=metadata.get("participant_count", 1),
                annotation_timestamp=datetime.now(),
                model_used=metadata.get("model", "unknown"),
                confidence_score=metadata.get("confidence", 0.0)
            )
            
            # Extract interview-level analysis
            self._extract_interview_level(root, extracted)
            
            # Extract priorities
            self._extract_priorities(root, extracted)
            
            # Extract themes and concerns
            self._extract_themes(root, extracted)
            
            # Extract emotions
            self._extract_emotions(root, extracted)
            
            # Extract evidence types
            self._extract_evidence(root, extracted)
            
            # Extract geographic references
            self._extract_geography(root, extracted)
            
            # Infer demographics
            self._infer_demographics(root, extracted)
            
            # Calculate quality metrics
            self._calculate_quality_metrics(root, extracted)
            
            return extracted
            
        except Exception as e:
            logger.error(f"Failed to extract data from {xml_path}: {e}")
            raise
    
    def _extract_metadata(self, root: ET.Element) -> Dict[str, Any]:
        """Extract metadata from XML."""
        metadata = {}
        
        # Interview metadata
        interview_elem = root.find(".//interview_metadata")
        if interview_elem is not None:
            for child in interview_elem:
                metadata[child.tag] = child.text
        
        # Processing metadata
        processing_elem = root.find(".//processing_metadata")
        if processing_elem is not None:
            for child in processing_elem:
                metadata[child.tag] = child.text
        
        # Try to extract from other locations
        if not metadata.get("id"):
            id_elem = root.find(".//interview_id")
            if id_elem is not None:
                metadata["id"] = id_elem.text
        
        return metadata
    
    def _extract_interview_level(self, root: ET.Element, data: ExtractedData) -> None:
        """Extract interview-level analysis."""
        interview_analysis = root.find(".//interview_level_analysis")
        if interview_analysis is None:
            return
        
        # Dominant emotion
        emotion_elem = interview_analysis.find(".//dominant_emotion")
        if emotion_elem is not None and emotion_elem.text:
            data.dominant_emotion = emotion_elem.text.strip()
        
        # Overall sentiment
        sentiment_elem = interview_analysis.find(".//overall_sentiment")
        if sentiment_elem is not None and sentiment_elem.text:
            data.overall_sentiment = sentiment_elem.text.strip().lower()
    
    def _extract_priorities(self, root: ET.Element, data: ExtractedData) -> None:
        """Extract national and local priorities."""
        # National priorities
        national_elem = root.find(".//national_priorities")
        if national_elem is not None:
            for i, priority_elem in enumerate(national_elem.findall(".//priority")):
                priority = self._parse_priority(priority_elem, i + 1)
                if priority:
                    data.national_priorities.append(priority)
        
        # Local priorities
        local_elem = root.find(".//local_priorities")
        if local_elem is not None:
            for i, priority_elem in enumerate(local_elem.findall(".//priority")):
                priority = self._parse_priority(priority_elem, i + 1)
                if priority:
                    data.local_priorities.append(priority)
    
    def _parse_priority(self, elem: ET.Element, default_rank: int) -> Optional[Priority]:
        """Parse a single priority element."""
        description = elem.find(".//description")
        if description is None or not description.text:
            return None
        
        # Determine category
        desc_text = description.text.lower()
        category = "other"
        subcategory = None
        
        for cat, keywords in self.priority_categories.items():
            if any(keyword in desc_text for keyword in keywords):
                category = cat
                # Find specific subcategory
                for keyword in keywords:
                    if keyword in desc_text:
                        subcategory = keyword
                        break
                break
        
        priority = Priority(
            rank=int(elem.get("rank", default_rank)),
            category=category,
            subcategory=subcategory,
            description=description.text.strip()
        )
        
        # Extract additional attributes
        sentiment_elem = elem.find(".//sentiment")
        if sentiment_elem is not None:
            priority.sentiment = sentiment_elem.text
        
        evidence_elem = elem.find(".//evidence_type")
        if evidence_elem is not None:
            priority.evidence_type = evidence_elem.text
        
        confidence_elem = elem.find(".//confidence")
        if confidence_elem is not None:
            try:
                priority.confidence = float(confidence_elem.text)
            except (ValueError, TypeError):
                pass
        
        return priority
    
    def _extract_themes(self, root: ET.Element, data: ExtractedData) -> None:
        """Extract themes, concerns, and suggestions."""
        # Main themes
        themes_elem = root.find(".//main_themes")
        if themes_elem is not None:
            for theme in themes_elem.findall(".//theme"):
                if theme.text:
                    data.themes.append(theme.text.strip())
        
        # Concerns
        concerns_elem = root.find(".//concerns")
        if concerns_elem is not None:
            for concern in concerns_elem.findall(".//concern"):
                concern_data = {
                    "description": concern.text.strip() if concern.text else "",
                    "category": concern.get("category", "general"),
                    "severity": concern.get("severity", "medium")
                }
                data.concerns.append(concern_data)
        
        # Suggestions
        suggestions_elem = root.find(".//suggestions")
        if suggestions_elem is not None:
            for suggestion in suggestions_elem.findall(".//suggestion"):
                suggestion_data = {
                    "description": suggestion.text.strip() if suggestion.text else "",
                    "target": suggestion.get("target", "general"),
                    "feasibility": suggestion.get("feasibility", "unknown")
                }
                data.suggestions.append(suggestion_data)
    
    def _extract_emotions(self, root: ET.Element, data: ExtractedData) -> None:
        """Extract emotional expressions."""
        emotions_elem = root.find(".//emotions")
        if emotions_elem is not None:
            for emotion_elem in emotions_elem.findall(".//emotion"):
                emotion = Emotion(
                    type=emotion_elem.get("type", "unknown"),
                    intensity=emotion_elem.get("intensity", "medium"),
                    target=emotion_elem.get("target"),
                    context=emotion_elem.text.strip() if emotion_elem.text else ""
                )
                data.emotions.append(emotion)
    
    def _extract_evidence(self, root: ET.Element, data: ExtractedData) -> None:
        """Extract evidence types used in arguments."""
        evidence_elem = root.find(".//evidence_types")
        if evidence_elem is not None:
            for evidence in evidence_elem.findall(".//evidence"):
                ev_type = evidence.get("type", "other")
                count = int(evidence.get("count", 1))
                data.evidence_types[ev_type] = data.evidence_types.get(ev_type, 0) + count
    
    def _extract_geography(self, root: ET.Element, data: ExtractedData) -> None:
        """Extract geographic mentions."""
        geo_elem = root.find(".//geographic_references")
        if geo_elem is not None:
            for location in geo_elem.findall(".//location"):
                if location.text:
                    data.geographic_mentions.append(location.text.strip())
    
    def _infer_demographics(self, root: ET.Element, data: ExtractedData) -> None:
        """Infer demographic information from content."""
        # This is a simplified version - real implementation would use
        # more sophisticated NLP and pattern matching
        
        demographics = root.find(".//inferred_demographics")
        if demographics is not None:
            age_elem = demographics.find(".//age_group")
            if age_elem is not None and age_elem.text:
                data.inferred_age_group = age_elem.text
            
            socio_elem = demographics.find(".//socioeconomic")
            if socio_elem is not None and socio_elem.text:
                data.inferred_socioeconomic = socio_elem.text
    
    def _calculate_quality_metrics(self, root: ET.Element, data: ExtractedData) -> None:
        """Calculate annotation quality metrics."""
        # Count filled sections
        total_sections = 10
        filled_sections = 0
        
        required_sections = [
            ".//interview_level_analysis",
            ".//national_priorities",
            ".//local_priorities",
            ".//main_themes",
            ".//emotions",
            ".//evidence_types"
        ]
        
        for section in required_sections:
            elem = root.find(section)
            if elem is not None and len(elem) > 0:
                filled_sections += 1
        
        data.annotation_completeness = filled_sections / len(required_sections)
        
        # Check for validation errors
        errors_elem = root.find(".//validation_errors")
        if errors_elem is not None:
            data.has_validation_errors = True
            for error in errors_elem.findall(".//error"):
                if error.text:
                    data.validation_notes.append(error.text)
    
    def extract_batch(self, xml_dir: Path) -> List[ExtractedData]:
        """
        Extract data from multiple XML files.
        
        Args:
            xml_dir: Directory containing XML annotation files
            
        Returns:
            List of ExtractedData objects
        """
        extracted_data = []
        xml_files = list(xml_dir.glob("*.xml"))
        
        logger.info(f"Extracting data from {len(xml_files)} XML files")
        
        for xml_file in xml_files:
            try:
                data = self.extract_from_xml(xml_file)
                extracted_data.append(data)
            except Exception as e:
                logger.error(f"Failed to extract from {xml_file}: {e}")
                continue
        
        logger.info(f"Successfully extracted {len(extracted_data)} annotations")
        return extracted_data
    
    def to_dataframe(self, extracted_data: List[ExtractedData]) -> Any:
        """
        Convert extracted data to pandas DataFrame for analysis.
        
        Args:
            extracted_data: List of ExtractedData objects
            
        Returns:
            pandas DataFrame with structured data
        """
        import pandas as pd
        
        # Flatten data for DataFrame
        rows = []
        for data in extracted_data:
            row = {
                # Metadata
                "interview_id": data.interview_id,
                "date": data.interview_date,
                "time": data.interview_time,
                "location": data.location,
                "department": data.department,
                "participant_count": data.participant_count,
                
                # Analysis
                "dominant_emotion": data.dominant_emotion,
                "overall_sentiment": data.overall_sentiment,
                
                # Priorities
                "n_national_priorities": len(data.national_priorities),
                "n_local_priorities": len(data.local_priorities),
                "top_national_priority": data.national_priorities[0].category if data.national_priorities else None,
                "top_local_priority": data.local_priorities[0].category if data.local_priorities else None,
                
                # Themes
                "n_themes": len(data.themes),
                "n_concerns": len(data.concerns),
                "n_suggestions": len(data.suggestions),
                
                # Emotions
                "n_emotions": len(data.emotions),
                "emotion_intensity": max([e.intensity for e in data.emotions], default="low"),
                
                # Evidence
                "evidence_types": len(data.evidence_types),
                "total_evidence": sum(data.evidence_types.values()),
                
                # Demographics
                "inferred_age_group": data.inferred_age_group,
                "inferred_socioeconomic": data.inferred_socioeconomic,
                
                # Quality
                "annotation_completeness": data.annotation_completeness,
                "has_validation_errors": data.has_validation_errors,
                "confidence_score": data.confidence_score
            }
            rows.append(row)
        
        return pd.DataFrame(rows)
    
    def export_to_json(self, extracted_data: ExtractedData, output_path: Path) -> None:
        """Export extracted data to JSON format."""
        # Convert to dictionary
        data_dict = {
            "metadata": {
                "interview_id": extracted_data.interview_id,
                "date": extracted_data.interview_date,
                "time": extracted_data.interview_time,
                "location": extracted_data.location,
                "department": extracted_data.department,
                "participant_count": extracted_data.participant_count,
                "annotation_timestamp": extracted_data.annotation_timestamp.isoformat(),
                "model_used": extracted_data.model_used,
                "confidence_score": extracted_data.confidence_score
            },
            "analysis": {
                "dominant_emotion": extracted_data.dominant_emotion,
                "overall_sentiment": extracted_data.overall_sentiment,
                "themes": extracted_data.themes,
                "concerns": extracted_data.concerns,
                "suggestions": extracted_data.suggestions
            },
            "priorities": {
                "national": [
                    {
                        "rank": p.rank,
                        "category": p.category,
                        "subcategory": p.subcategory,
                        "description": p.description,
                        "sentiment": p.sentiment,
                        "evidence_type": p.evidence_type,
                        "confidence": p.confidence
                    }
                    for p in extracted_data.national_priorities
                ],
                "local": [
                    {
                        "rank": p.rank,
                        "category": p.category,
                        "subcategory": p.subcategory,
                        "description": p.description,
                        "sentiment": p.sentiment,
                        "evidence_type": p.evidence_type,
                        "confidence": p.confidence
                    }
                    for p in extracted_data.local_priorities
                ]
            },
            "emotions": [
                {
                    "type": e.type,
                    "intensity": e.intensity,
                    "target": e.target,
                    "context": e.context
                }
                for e in extracted_data.emotions
            ],
            "evidence_types": extracted_data.evidence_types,
            "geographic_mentions": extracted_data.geographic_mentions,
            "demographics": {
                "inferred_age_group": extracted_data.inferred_age_group,
                "inferred_socioeconomic": extracted_data.inferred_socioeconomic
            },
            "quality_metrics": {
                "annotation_completeness": extracted_data.annotation_completeness,
                "has_validation_errors": extracted_data.has_validation_errors,
                "validation_notes": extracted_data.validation_notes
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data_dict, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    # Test the extractor
    extractor = DataExtractor()
    
    # Example usage
    xml_path = Path("data/processed/annotations/test_annotation.xml")
    if xml_path.exists():
        extracted = extractor.extract_from_xml(xml_path)
        print(f"Extracted data for interview {extracted.interview_id}")
        print(f"National priorities: {len(extracted.national_priorities)}")
        print(f"Local priorities: {len(extracted.local_priorities)}")
        print(f"Themes: {extracted.themes}")
        print(f"Overall sentiment: {extracted.overall_sentiment}")
        
        # Export to JSON
        json_path = xml_path.with_suffix('.json')
        extractor.export_to_json(extracted, json_path)
        print(f"Exported to {json_path}")