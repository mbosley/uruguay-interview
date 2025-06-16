"""
Prompt management for AI annotation engine using XML schema.
"""
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import logging
import re
from datetime import datetime

from config.settings import config

logger = logging.getLogger(__name__)


class PromptManager:
    """Manages prompts and schemas for AI annotation using XML."""
    
    def __init__(self, schema_path: Optional[Path] = None):
        """Initialize prompt manager with annotation schema."""
        if schema_path is None:
            schema_path = config.get_prompt_path(config.DEFAULT_ANNOTATION_PROMPT)
        
        self.schema_path = schema_path
        self.schema_tree = self._load_schema()
        self.schema_root = self.schema_tree.getroot()
        
    def _load_schema(self) -> ET.ElementTree:
        """Load XML annotation schema."""
        try:
            tree = ET.parse(self.schema_path)
            return tree
        except Exception as e:
            logger.error(f"Failed to load schema from {self.schema_path}: {e}")
            raise
    
    def create_annotation_prompt(self, interview_text: str, interview_metadata: Dict[str, Any]) -> str:
        """Create annotation prompt by injecting interview into XML schema."""
        # Create a copy of the schema to modify
        schema_copy = ET.ElementTree(ET.fromstring(ET.tostring(self.schema_root)))
        root = schema_copy.getroot()
        
        # Create interview section to inject
        interview_section = ET.Element("interview_to_annotate")
        
        # Add metadata
        metadata_elem = ET.SubElement(interview_section, "provided_metadata")
        ET.SubElement(metadata_elem, "interview_id").text = str(interview_metadata.get('id', 'unknown'))
        ET.SubElement(metadata_elem, "date").text = interview_metadata.get('date', '')
        ET.SubElement(metadata_elem, "location").text = interview_metadata.get('location', '')
        ET.SubElement(metadata_elem, "department").text = interview_metadata.get('department', '')
        ET.SubElement(metadata_elem, "participant_count").text = str(interview_metadata.get('participant_count', 0))
        
        # Add interview text
        ET.SubElement(interview_section, "interview_text").text = interview_text
        
        # Add instructions for completion
        instructions = ET.Element("completion_instructions")
        instructions.text = """
Please complete the annotation by filling in all required fields in the schema below.
Follow the step-by-step process outlined in the annotator instructions.
Preserve the XML structure and provide values for all required attributes and elements.
Use CDATA sections for long text fields to preserve formatting.
        """
        
        # Insert at beginning of root
        root.insert(0, instructions)
        root.insert(1, interview_section)
        
        # Convert to string with pretty formatting
        xml_string = self._pretty_print_xml(root)
        
        prompt = f"""You are provided with a detailed annotation schema and an interview to analyze.
Complete the XML annotation following all instructions and examples in the schema.

{xml_string}

IMPORTANT: 
- Return ONLY the completed XML annotation (everything from <annotation_result> to </annotation_result>)
- Preserve the exact XML structure from the schema
- Fill in all required fields with appropriate values
- Use the participant's own words in narrative fields
- Include confidence scores where requested
- Flag any uncertainties appropriately

Begin your response with <annotation_result> and end with </annotation_result>."""
        
        return prompt
    
    def create_empty_annotation_template(self, interview_id: str) -> ET.Element:
        """Create an empty annotation template following the schema."""
        annotation = ET.Element("annotation_result")
        annotation.set("schema_version", "1.0")
        annotation.set("annotation_timestamp", datetime.now().isoformat())
        
        # Interview-level annotation
        interview_level = ET.SubElement(annotation, "interview_level")
        
        # Metadata
        metadata = ET.SubElement(interview_level, "metadata")
        ET.SubElement(metadata, "interview_id").text = interview_id
        ET.SubElement(metadata, "date")
        location = ET.SubElement(metadata, "location")
        ET.SubElement(location, "municipality")
        ET.SubElement(location, "department")
        ET.SubElement(location, "locality_size")
        ET.SubElement(metadata, "duration_minutes")
        ET.SubElement(metadata, "interviewer_ids")
        
        # Participant profile
        profile = ET.SubElement(interview_level, "participant_profile")
        ET.SubElement(profile, "age_range")
        ET.SubElement(profile, "gender")
        ET.SubElement(profile, "organizational_affiliation")
        ET.SubElement(profile, "self_described_political_stance")
        ET.SubElement(profile, "occupation_sector")
        
        # Uncertainty tracking
        uncertainty = ET.SubElement(interview_level, "uncertainty_tracking")
        ET.SubElement(uncertainty, "overall_confidence").text = "0.0"
        uncertainty_flags = ET.SubElement(uncertainty, "uncertainty_flags")
        ET.SubElement(uncertainty_flags, "flag")
        ET.SubElement(uncertainty_flags, "uncertainty_narrative")
        ET.SubElement(uncertainty, "edge_cases")
        ET.SubElement(uncertainty, "contextual_gaps")
        
        # Priority summary
        priority_summary = ET.SubElement(interview_level, "priority_summary")
        
        # National priorities
        national = ET.SubElement(priority_summary, "national_priorities")
        for rank in range(1, 4):
            priority = ET.SubElement(national, "priority")
            priority.set("rank", str(rank))
            ET.SubElement(priority, "theme")
            ET.SubElement(priority, "specific_issues")
            ET.SubElement(priority, "narrative_elaboration")
        
        # Local priorities
        local = ET.SubElement(priority_summary, "local_priorities")
        for rank in range(1, 4):
            priority = ET.SubElement(local, "priority")
            priority.set("rank", str(rank))
            ET.SubElement(priority, "theme")
            ET.SubElement(priority, "specific_issues")
            ET.SubElement(priority, "narrative_elaboration")
        
        # Add other required sections
        self._add_narrative_features(interview_level)
        self._add_key_narratives(interview_level)
        self._add_analytical_notes(interview_level)
        self._add_interview_dynamics(interview_level)
        
        return annotation
    
    def _add_narrative_features(self, parent: ET.Element) -> None:
        """Add narrative features section to annotation."""
        features = ET.SubElement(parent, "narrative_features")
        ET.SubElement(features, "dominant_frame")
        ET.SubElement(features, "frame_narrative")
        ET.SubElement(features, "temporal_orientation")
        ET.SubElement(features, "temporal_narrative")
        ET.SubElement(features, "agency_attribution")
        ET.SubElement(features, "agency_narrative")
        
        metaphors = ET.SubElement(features, "metaphors_and_imagery")
        ET.SubElement(metaphors, "key_metaphors")
        ET.SubElement(metaphors, "imagery_analysis")
        
        emotional = ET.SubElement(features, "emotional_register")
        ET.SubElement(emotional, "dominant_emotions")
        ET.SubElement(emotional, "emotional_trajectory")
        ET.SubElement(emotional, "emotional_intensity").text = "0.0"
    
    def _add_key_narratives(self, parent: ET.Element) -> None:
        """Add key narratives section to annotation."""
        narratives = ET.SubElement(parent, "key_narratives")
        ET.SubElement(narratives, "identity_narrative")
        ET.SubElement(narratives, "problem_narrative")
        ET.SubElement(narratives, "solution_narrative")
        ET.SubElement(narratives, "hope_narrative")
    
    def _add_analytical_notes(self, parent: ET.Element) -> None:
        """Add analytical notes section to annotation."""
        notes = ET.SubElement(parent, "analytical_notes")
        ET.SubElement(notes, "tensions_and_contradictions")
        ET.SubElement(notes, "silences_and_absences")
        ET.SubElement(notes, "connections_to_broader_themes")
        ET.SubElement(notes, "interviewer_reflections")
    
    def _add_interview_dynamics(self, parent: ET.Element) -> None:
        """Add interview dynamics section to annotation."""
        dynamics = ET.SubElement(parent, "interview_dynamics")
        ET.SubElement(dynamics, "rapport_quality")
        ET.SubElement(dynamics, "participant_engagement")
        ET.SubElement(dynamics, "communication_challenges")
        ET.SubElement(dynamics, "notable_moments")
    
    def parse_annotation_response(self, xml_response: str) -> ET.Element:
        """Parse XML annotation response from AI."""
        try:
            # Extract annotation result from response
            start_tag = "<annotation_result"
            end_tag = "</annotation_result>"
            
            start_idx = xml_response.find(start_tag)
            end_idx = xml_response.find(end_tag) + len(end_tag)
            
            if start_idx == -1 or end_idx < len(end_tag):
                raise ValueError("No valid annotation_result found in response")
            
            xml_content = xml_response[start_idx:end_idx]
            
            # Parse XML
            annotation = ET.fromstring(xml_content)
            
            # Validate basic structure
            if annotation.tag != "annotation_result":
                raise ValueError("Root element must be annotation_result")
            
            return annotation
            
        except ET.ParseError as e:
            logger.error(f"Failed to parse XML response: {e}")
            logger.debug(f"Response excerpt: {xml_response[:500]}...")
            raise ValueError(f"Invalid XML in response: {e}")
    
    def validate_annotation(self, annotation: ET.Element) -> Tuple[bool, List[str]]:
        """Validate that annotation follows schema requirements."""
        errors = []
        
        # Check for required sections
        interview_level = annotation.find("interview_level")
        if interview_level is None:
            errors.append("Missing interview_level element")
            return False, errors
        
        # Validate metadata
        metadata = interview_level.find("metadata")
        if metadata is None:
            errors.append("Missing metadata section")
        else:
            required_metadata = ["interview_id", "date", "location"]
            for field in required_metadata:
                if metadata.find(field) is None:
                    errors.append(f"Missing metadata field: {field}")
        
        # Validate priorities
        priority_summary = interview_level.find("priority_summary")
        if priority_summary is None:
            errors.append("Missing priority_summary section")
        else:
            for priority_type in ["national_priorities", "local_priorities"]:
                priorities = priority_summary.find(priority_type)
                if priorities is None:
                    errors.append(f"Missing {priority_type}")
                else:
                    priority_elements = priorities.findall("priority")
                    if len(priority_elements) == 0:
                        errors.append(f"No priorities found in {priority_type}")
                    
                    for p in priority_elements:
                        if p.get("rank") is None:
                            errors.append(f"Priority missing rank attribute in {priority_type}")
                        if p.find("theme") is None or not p.find("theme").text:
                            errors.append(f"Priority missing theme in {priority_type}")
        
        # Validate confidence score
        confidence = interview_level.find(".//overall_confidence")
        if confidence is not None and confidence.text:
            try:
                conf_value = float(confidence.text)
                if not 0 <= conf_value <= 1:
                    errors.append(f"Invalid confidence score: {conf_value}")
            except ValueError:
                errors.append(f"Non-numeric confidence score: {confidence.text}")
        
        return len(errors) == 0, errors
    
    def extract_key_data(self, annotation: ET.Element) -> Dict[str, Any]:
        """Extract key data points from XML annotation for easier access."""
        data = {}
        interview_level = annotation.find("interview_level")
        
        if interview_level is None:
            return data
        
        # Extract metadata
        metadata = interview_level.find("metadata")
        if metadata is not None:
            data["interview_id"] = self._get_text(metadata, "interview_id")
            data["date"] = self._get_text(metadata, "date")
            
            location = metadata.find("location")
            if location is not None:
                data["municipality"] = self._get_text(location, "municipality")
                data["department"] = self._get_text(location, "department")
        
        # Extract priorities
        data["national_priorities"] = []
        data["local_priorities"] = []
        
        priority_summary = interview_level.find("priority_summary")
        if priority_summary is not None:
            for priority_type in ["national_priorities", "local_priorities"]:
                priorities = priority_summary.find(priority_type)
                if priorities is not None:
                    for p in priorities.findall("priority"):
                        priority_data = {
                            "rank": int(p.get("rank", 0)),
                            "theme": self._get_text(p, "theme"),
                            "narrative": self._get_text(p, "narrative_elaboration")
                        }
                        data[priority_type].append(priority_data)
        
        # Extract confidence
        confidence = interview_level.find(".//overall_confidence")
        if confidence is not None and confidence.text:
            try:
                data["confidence"] = float(confidence.text)
            except ValueError:
                data["confidence"] = 0.0
        
        return data
    
    def _get_text(self, parent: ET.Element, tag: str, default: str = "") -> str:
        """Safely get text from XML element."""
        elem = parent.find(tag)
        return elem.text.strip() if elem is not None and elem.text else default
    
    def _pretty_print_xml(self, elem: ET.Element) -> str:
        """Pretty print XML with proper indentation."""
        rough_string = ET.tostring(elem, encoding='unicode')
        
        # Simple pretty printing
        import xml.dom.minidom
        dom = xml.dom.minidom.parseString(rough_string)
        return dom.toprettyxml(indent="  ")


if __name__ == "__main__":
    # Test prompt manager
    pm = PromptManager()
    print(f"Schema loaded from: {pm.schema_path}")
    
    # Test creating empty template
    template = pm.create_empty_annotation_template("test_001")
    print("\nEmpty template created with", len(template.findall(".//*")), "elements")
    
    # Test metadata creation
    test_metadata = {
        "id": "001",
        "date": "2025-05-28",
        "location": "Montevideo",
        "department": "Montevideo",
        "participant_count": 2
    }
    
    test_text = "Sample interview text..."
    prompt = pm.create_annotation_prompt(test_text, test_metadata)
    print("\nPrompt created, length:", len(prompt))