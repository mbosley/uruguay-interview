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
    
    # Demographic indicators (from participant_profile)
    inferred_age_group: Optional[str] = None
    inferred_socioeconomic: Optional[str] = None
    inferred_gender: Optional[str] = None
    organizational_affiliation: Optional[str] = None
    occupation_sector: Optional[str] = None
    political_stance: Optional[str] = None
    
    # Narrative features
    dominant_frame: Optional[str] = None
    temporal_orientation: Optional[str] = None
    government_responsibility: Optional[float] = None
    individual_responsibility: Optional[float] = None
    structural_factors: Optional[float] = None
    solution_orientation: Optional[str] = None
    
    # Key narratives
    identity_narrative: Optional[str] = None
    problem_narrative: Optional[str] = None
    hope_narrative: Optional[str] = None
    memorable_quotes: List[str] = field(default_factory=list)
    
    # Interview dynamics
    rapport: Optional[str] = None
    participant_engagement: Optional[str] = None
    coherence: Optional[str] = None
    
    # Uncertainty tracking
    overall_confidence: Optional[float] = None
    uncertainty_flags: List[str] = field(default_factory=list)
    uncertainty_narrative: Optional[str] = None
    contextual_gaps: List[Dict[str, str]] = field(default_factory=list)
    
    # Analytical insights
    tensions_contradictions: Optional[str] = None
    silences_omissions: Optional[str] = None
    interviewer_reflections: Optional[str] = None
    broader_connections: Optional[str] = None
    
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
        """Extract metadata from XML (handles AI-generated structure)."""
        metadata = {}
        
        # AI-generated structure: <interview_level><metadata>
        interview_level = root.find(".//interview_level")
        if interview_level is not None:
            metadata_elem = interview_level.find("metadata")
            if metadata_elem is not None:
                # Extract interview_id
                id_elem = metadata_elem.find("interview_id")
                if id_elem is not None:
                    metadata["id"] = id_elem.text
                
                # Extract date
                date_elem = metadata_elem.find("date")
                if date_elem is not None:
                    metadata["date"] = date_elem.text
                
                # Extract location info
                location_elem = metadata_elem.find("location")
                if location_elem is not None:
                    municipality = location_elem.find("municipality")
                    department = location_elem.find("department")
                    if municipality is not None:
                        metadata["location"] = municipality.text
                    if department is not None:
                        metadata["department"] = department.text
        
        # Extract confidence from uncertainty_tracking
        uncertainty_elem = root.find(".//uncertainty_tracking")
        if uncertainty_elem is not None:
            confidence_elem = uncertainty_elem.find("overall_confidence")
            if confidence_elem is not None:
                try:
                    metadata["confidence"] = float(confidence_elem.text)
                except (ValueError, TypeError):
                    metadata["confidence"] = 0.0
        
        # Fallback: try old structure for backward compatibility
        if not metadata.get("id"):
            old_interview_elem = root.find(".//interview_metadata")
            if old_interview_elem is not None:
                for child in old_interview_elem:
                    metadata[child.tag] = child.text
        
        return metadata
    
    def _extract_interview_level(self, root: ET.Element, data: ExtractedData) -> None:
        """Extract interview-level analysis (handles AI-generated structure)."""
        # AI-generated structure: <narrative_features>
        narrative_features = root.find(".//narrative_features")
        if narrative_features is not None:
            # Extract dominant frame
            frame_elem = narrative_features.find("dominant_frame")
            if frame_elem is not None and frame_elem.text:
                data.dominant_frame = frame_elem.text.strip()
                data.dominant_emotion = frame_elem.text.strip()  # Keep for backward compatibility
            
            # Extract temporal orientation
            temporal_elem = narrative_features.find("temporal_orientation")
            if temporal_elem is not None and temporal_elem.text:
                data.temporal_orientation = temporal_elem.text.strip()
                # Map temporal orientation to sentiment
                temporal = temporal_elem.text.strip().lower()
                if "past" in temporal:
                    data.overall_sentiment = "negative"
                elif "future" in temporal:
                    data.overall_sentiment = "positive"
                else:
                    data.overall_sentiment = "neutral"
            
            # Extract agency attribution
            agency_elem = narrative_features.find("agency_attribution")
            if agency_elem is not None:
                gov_resp = agency_elem.find("government_responsibility")
                if gov_resp is not None and gov_resp.text:
                    try:
                        data.government_responsibility = float(gov_resp.text)
                    except (ValueError, TypeError):
                        pass
                
                ind_resp = agency_elem.find("individual_responsibility")
                if ind_resp is not None and ind_resp.text:
                    try:
                        data.individual_responsibility = float(ind_resp.text)
                    except (ValueError, TypeError):
                        pass
                
                struct_factors = agency_elem.find("structural_factors")
                if struct_factors is not None and struct_factors.text:
                    try:
                        data.structural_factors = float(struct_factors.text)
                    except (ValueError, TypeError):
                        pass
            
            # Extract solution orientation
            solution_elem = narrative_features.find("solution_orientation")
            if solution_elem is not None and solution_elem.text:
                data.solution_orientation = solution_elem.text.strip()
        
        # Extract key narratives
        self._extract_key_narratives(root, data)
        
        # Extract interview dynamics
        self._extract_interview_dynamics(root, data)
        
        # Extract analytical insights
        self._extract_analytical_insights(root, data)
        
        # Fallback: try old structure for backward compatibility
        interview_analysis = root.find(".//interview_level_analysis")
        if interview_analysis is not None:
            emotion_elem = interview_analysis.find(".//dominant_emotion")
            if emotion_elem is not None and emotion_elem.text:
                data.dominant_emotion = emotion_elem.text.strip()
            
            sentiment_elem = interview_analysis.find(".//overall_sentiment")
            if sentiment_elem is not None and sentiment_elem.text:
                data.overall_sentiment = sentiment_elem.text.strip().lower()
    
    def _extract_priorities(self, root: ET.Element, data: ExtractedData) -> None:
        """Extract national and local priorities (handles AI-generated structure)."""
        # AI-generated structure: <priority_summary><national_priorities>
        priority_summary = root.find(".//priority_summary")
        if priority_summary is not None:
            # National priorities
            national_elem = priority_summary.find("national_priorities")
            if national_elem is not None:
                for priority_elem in national_elem.findall("priority"):
                    priority = self._parse_ai_priority(priority_elem, "national")
                    if priority:
                        data.national_priorities.append(priority)
            
            # Local priorities
            local_elem = priority_summary.find("local_priorities")
            if local_elem is not None:
                for priority_elem in local_elem.findall("priority"):
                    priority = self._parse_ai_priority(priority_elem, "local")
                    if priority:
                        data.local_priorities.append(priority)
        
        # Fallback: try old structure for backward compatibility
        if not data.national_priorities and not data.local_priorities:
            national_elem = root.find(".//national_priorities")
            if national_elem is not None:
                for i, priority_elem in enumerate(national_elem.findall(".//priority")):
                    priority = self._parse_priority(priority_elem, i + 1)
                    if priority:
                        data.national_priorities.append(priority)
            
            local_elem = root.find(".//local_priorities")
            if local_elem is not None:
                for i, priority_elem in enumerate(local_elem.findall(".//priority")):
                    priority = self._parse_priority(priority_elem, i + 1)
                    if priority:
                        data.local_priorities.append(priority)
    
    def _parse_ai_priority(self, elem: ET.Element, scope: str) -> Optional[Priority]:
        """Parse a priority element from AI-generated XML."""
        # AI structure: <priority rank="1"><theme>Theme</theme><specific_issues>...</specific_issues><narrative_elaboration>...</narrative_elaboration>
        theme_elem = elem.find("theme")
        narrative_elem = elem.find("narrative_elaboration")
        issues_elem = elem.find("specific_issues")
        
        if theme_elem is None or not theme_elem.text:
            return None
        
        theme_text = theme_elem.text.strip()
        description = narrative_elem.text.strip() if narrative_elem is not None and narrative_elem.text else theme_text
        
        # Parse specific issues using robust parser
        specific_issues = self._parse_specific_issues(issues_elem)
        
        # Map theme to category
        category = self._map_theme_to_category(theme_text.lower())
        
        priority = Priority(
            rank=int(elem.get("rank", 1)),
            category=category,
            subcategory=specific_issues[0] if specific_issues else None,  # Use first issue as subcategory
            description=description
        )
        
        # Set confidence (default to high for AI-extracted priorities)
        priority.confidence = 0.8
        
        return priority
    
    def _map_theme_to_category(self, theme: str) -> str:
        """Map AI-generated theme to our category system."""
        theme_mapping = {
            "inclusion": "social",
            "state support": "governance",
            "training": "education",
            "infrastructure": "infrastructure",
            "community awareness": "social",
            "employment": "economy",
            "health": "healthcare",
            "safety": "security",
            "education": "education",
            "environment": "environment"
        }
        
        for key, category in theme_mapping.items():
            if key in theme:
                return category
        
        return "other"
    
    def _parse_priority(self, elem: ET.Element, default_rank: int) -> Optional[Priority]:
        """Parse a single priority element (legacy format)."""
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
    
    def _parse_specific_issues(self, elem: ET.Element) -> List[str]:
        """Parse specific_issues element handling multiple formats."""
        if elem is None:
            return []
        
        # Format 1: Bracket notation like "[employment, disability support]"
        if elem.text and elem.text.strip().startswith('[') and elem.text.strip().endswith(']'):
            text = elem.text.strip()[1:-1]  # Remove brackets
            return [item.strip() for item in text.split(',') if item.strip()]
        
        # Format 2: Value tags
        values = elem.findall('value')
        if values:
            return [v.text.strip() for v in values if v.text and v.text.strip()]
        
        # Format 3: Plain text with commas
        if elem.text and elem.text.strip():
            return [item.strip() for item in elem.text.split(',') if item.strip()]
        
        return []
    
    def _extract_key_narratives(self, root: ET.Element, data: ExtractedData) -> None:
        """Extract key narratives from AI annotation."""
        key_narratives = root.find(".//key_narratives")
        if key_narratives is not None:
            # Identity narrative
            identity_elem = key_narratives.find("identity_narrative")
            if identity_elem is not None and identity_elem.text:
                data.identity_narrative = identity_elem.text.strip()
            
            # Problem narrative
            problem_elem = key_narratives.find("problem_narrative") 
            if problem_elem is not None and problem_elem.text:
                data.problem_narrative = problem_elem.text.strip()
            
            # Hope narrative
            hope_elem = key_narratives.find("hope_narrative")
            if hope_elem is not None and hope_elem.text:
                data.hope_narrative = hope_elem.text.strip()
            
            # Memorable quotes
            quotes_elem = key_narratives.find("memorable_quotes")
            if quotes_elem is not None and quotes_elem.text:
                # Parse quotes - could be comma-separated or quote-delimited
                quotes_text = quotes_elem.text.strip()
                if quotes_text.startswith('"') or quotes_text.count('"') >= 2:
                    # Extract quoted strings
                    import re
                    quotes = re.findall(r'"([^"]*)"', quotes_text)
                    data.memorable_quotes = [q.strip() for q in quotes if q.strip()]
                else:
                    # Comma-separated
                    data.memorable_quotes = [q.strip() for q in quotes_text.split(',') if q.strip()]
    
    def _extract_interview_dynamics(self, root: ET.Element, data: ExtractedData) -> None:
        """Extract interview dynamics information."""
        dynamics = root.find(".//interview_dynamics")
        if dynamics is not None:
            # Rapport
            rapport_elem = dynamics.find("rapport")
            if rapport_elem is not None and rapport_elem.text:
                data.rapport = rapport_elem.text.strip()
            
            # Participant engagement
            engagement_elem = dynamics.find("participant_engagement")
            if engagement_elem is not None and engagement_elem.text:
                data.participant_engagement = engagement_elem.text.strip()
            
            # Coherence
            coherence_elem = dynamics.find("coherence")
            if coherence_elem is not None and coherence_elem.text:
                data.coherence = coherence_elem.text.strip()
    
    def _extract_analytical_insights(self, root: ET.Element, data: ExtractedData) -> None:
        """Extract analytical notes and insights."""
        analytical_notes = root.find(".//analytical_notes")
        if analytical_notes is not None:
            # Tensions and contradictions
            tensions_elem = analytical_notes.find("tensions_contradictions")
            if tensions_elem is not None and tensions_elem.text:
                data.tensions_contradictions = tensions_elem.text.strip()
            
            # Silences and omissions
            silences_elem = analytical_notes.find("silences_omissions")
            if silences_elem is not None and silences_elem.text:
                data.silences_omissions = silences_elem.text.strip()
            
            # Interviewer reflections
            reflections_elem = analytical_notes.find("interviewer_reflections")
            if reflections_elem is not None and reflections_elem.text:
                data.interviewer_reflections = reflections_elem.text.strip()
            
            # Broader connections
            connections_elem = analytical_notes.find("connections_to_broader_themes")
            if connections_elem is not None and connections_elem.text:
                data.broader_connections = connections_elem.text.strip()
        
        # Extract uncertainty tracking
        self._extract_uncertainty_tracking(root, data)
    
    def _extract_uncertainty_tracking(self, root: ET.Element, data: ExtractedData) -> None:
        """Extract uncertainty tracking information."""
        uncertainty = root.find(".//uncertainty_tracking")
        if uncertainty is not None:
            # Overall confidence
            confidence_elem = uncertainty.find("overall_confidence")
            if confidence_elem is not None and confidence_elem.text:
                try:
                    data.overall_confidence = float(confidence_elem.text)
                except (ValueError, TypeError):
                    pass
            
            # Uncertainty flags
            flags_elem = uncertainty.find("uncertainty_flags")
            if flags_elem is not None:
                for flag in flags_elem.findall("flag"):
                    if flag.text:
                        data.uncertainty_flags.append(flag.text.strip())
            
            # Uncertainty narrative
            narrative_elem = uncertainty.find("uncertainty_narrative")
            if narrative_elem is not None and narrative_elem.text:
                data.uncertainty_narrative = narrative_elem.text.strip()
            
            # Contextual gaps
            gaps_elem = uncertainty.find("contextual_gaps")
            if gaps_elem is not None:
                for gap in gaps_elem.findall("gap"):
                    gap_data = {}
                    type_elem = gap.find("type")
                    if type_elem is not None and type_elem.text:
                        gap_data["type"] = type_elem.text.strip()
                    
                    desc_elem = gap.find("description")
                    if desc_elem is not None and desc_elem.text:
                        gap_data["description"] = desc_elem.text.strip()
                    
                    impact_elem = gap.find("impact")
                    if impact_elem is not None and impact_elem.text:
                        gap_data["impact"] = impact_elem.text.strip()
                    
                    if gap_data:
                        data.contextual_gaps.append(gap_data)
    
    def _extract_themes(self, root: ET.Element, data: ExtractedData) -> None:
        """Extract themes, concerns, and suggestions (handles AI-generated structure)."""
        # Extract themes from priority themes
        priority_summary = root.find(".//priority_summary")
        if priority_summary is not None:
            # Extract themes from national priorities
            for priority in priority_summary.findall(".//priority"):
                theme_elem = priority.find("theme")
                if theme_elem is not None and theme_elem.text:
                    data.themes.append(theme_elem.text.strip())
        
        # Extract from key narratives
        key_narratives = root.find(".//key_narratives")
        if key_narratives is not None:
            for child in key_narratives:
                if child.tag and "narrative" in child.tag:
                    data.themes.append(child.tag.replace("_narrative", "").replace("_", " ").title())
        
        # Fallback: try old structure
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
        """Extract emotional expressions (handles AI-generated structure)."""
        # Extract from narrative features
        narrative_features = root.find(".//narrative_features")
        if narrative_features is not None:
            # Extract dominant frame as emotion
            frame_elem = narrative_features.find("dominant_frame")
            if frame_elem is not None and frame_elem.text:
                emotion = Emotion(
                    type=frame_elem.text.strip(),
                    intensity="medium",
                    target="general",
                    context="Dominant narrative frame"
                )
                data.emotions.append(emotion)
        
        # Fallback: try old structure
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
        """Extract demographic information from participant_profile (AI-generated structure)."""
        # AI-generated structure: <participant_profile>
        participant_profile = root.find(".//participant_profile")
        if participant_profile is not None:
            # Age range
            age_elem = participant_profile.find("age_range")
            if age_elem is not None and age_elem.text:
                data.inferred_age_group = age_elem.text.strip()
            
            # Gender
            gender_elem = participant_profile.find("gender")
            if gender_elem is not None and gender_elem.text:
                data.inferred_gender = gender_elem.text.strip()
            
            # Organizational affiliation
            org_elem = participant_profile.find("organizational_affiliation")
            if org_elem is not None and org_elem.text:
                data.organizational_affiliation = org_elem.text.strip()
            
            # Occupation sector
            occupation_elem = participant_profile.find("occupation_sector")
            if occupation_elem is not None and occupation_elem.text:
                data.occupation_sector = occupation_elem.text.strip()
            
            # Political stance
            political_elem = participant_profile.find("self_described_political_stance")
            if political_elem is not None and political_elem.text:
                data.political_stance = political_elem.text.strip()
        
        # Fallback: try old structure for backward compatibility
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