"""
XML Schema Definition (XSD) validator for AI annotation outputs.
Enforces strict schema compliance to ensure predictable parsing.
"""
import logging
from pathlib import Path
from typing import List, Tuple, Optional
import xml.etree.ElementTree as ET

# Try to import lxml for XSD validation, fall back to basic validation
try:
    from lxml import etree
    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False

logger = logging.getLogger(__name__)


class SchemaValidator:
    """Validates XML annotations against formal XSD schema."""
    
    def __init__(self, xsd_path: Optional[Path] = None):
        """
        Initialize schema validator.
        
        Args:
            xsd_path: Path to XSD schema file. If None, uses default schema.
        """
        if xsd_path is None:
            xsd_path = Path(__file__).parent.parent.parent.parent / "config" / "schemas" / "annotation_schema.xsd"
        
        self.xsd_path = xsd_path
        self.schema = None
        
        if LXML_AVAILABLE:
            self._load_xsd_schema()
        else:
            logger.warning("lxml not available, falling back to basic validation")
    
    def _load_xsd_schema(self) -> None:
        """Load XSD schema for validation."""
        try:
            with open(self.xsd_path, 'r', encoding='utf-8') as f:
                schema_doc = etree.parse(f)
            self.schema = etree.XMLSchema(schema_doc)
            logger.info(f"Loaded XSD schema from {self.xsd_path}")
        except Exception as e:
            logger.error(f"Failed to load XSD schema from {self.xsd_path}: {e}")
            self.schema = None
    
    def validate_xml_string(self, xml_string: str) -> Tuple[bool, List[str]]:
        """
        Validate XML string against XSD schema.
        
        Args:
            xml_string: XML content to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        if not LXML_AVAILABLE or self.schema is None:
            return self._basic_validation(xml_string)
        
        try:
            # Parse XML with lxml
            xml_doc = etree.fromstring(xml_string.encode('utf-8'))
            
            # Validate against schema
            is_valid = self.schema.validate(xml_doc)
            
            if is_valid:
                return True, []
            else:
                # Extract validation errors
                errors = []
                for error in self.schema.error_log:
                    errors.append(f"Line {error.line}: {error.message}")
                return False, errors
                
        except etree.XMLSyntaxError as e:
            return False, [f"XML syntax error: {e}"]
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False, [f"Validation failed: {e}"]
    
    def validate_xml_element(self, xml_element: ET.Element) -> Tuple[bool, List[str]]:
        """
        Validate XML element against XSD schema.
        
        Args:
            xml_element: XML element to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        # Convert ElementTree element to string
        xml_string = ET.tostring(xml_element, encoding='unicode')
        return self.validate_xml_string(xml_string)
    
    def _basic_validation(self, xml_string: str) -> Tuple[bool, List[str]]:
        """
        Basic validation when lxml is not available.
        Checks for required elements and structure.
        """
        errors = []
        
        try:
            # Parse with ElementTree
            root = ET.fromstring(xml_string)
            
            # Check root element
            if root.tag != "annotation_result":
                errors.append("Root element must be 'annotation_result'")
                return False, errors
            
            # Check for required top-level sections
            required_sections = ["interview_level", "turn_level", "processing_metadata"]
            for section in required_sections:
                if root.find(section) is None:
                    errors.append(f"Missing required section: {section}")
            
            # Validate interview_level structure
            interview_level = root.find("interview_level")
            if interview_level is not None:
                interview_required = [
                    "metadata", 
                    "participant_profile", 
                    "uncertainty_tracking",
                    "priority_summary",
                    "narrative_features",
                    "key_narratives",
                    "analytical_notes",
                    "interview_dynamics"
                ]
                
                for section in interview_required:
                    if interview_level.find(section) is None:
                        errors.append(f"Missing interview_level section: {section}")
            
            # Validate metadata structure
            metadata = root.find(".//metadata")
            if metadata is not None:
                metadata_required = ["interview_id", "date", "location", "duration_minutes", "interviewer_ids"]
                for field in metadata_required:
                    if metadata.find(field) is None:
                        errors.append(f"Missing metadata field: {field}")
                
                # Check location structure
                location = metadata.find("location")
                if location is not None:
                    location_required = ["municipality", "department", "locality_size"]
                    for field in location_required:
                        if location.find(field) is None:
                            errors.append(f"Missing location field: {field}")
            
            # Validate priority structure
            priority_summary = root.find(".//priority_summary")
            if priority_summary is not None:
                for priority_type in ["national_priorities", "local_priorities"]:
                    priorities = priority_summary.find(priority_type)
                    if priorities is not None:
                        priority_elements = priorities.findall("priority")
                        for priority in priority_elements:
                            # Check rank attribute
                            rank = priority.get("rank")
                            if rank is None:
                                errors.append(f"Priority missing rank attribute in {priority_type}")
                            else:
                                try:
                                    rank_val = int(rank)
                                    if not 1 <= rank_val <= 3:
                                        errors.append(f"Invalid priority rank {rank} in {priority_type}")
                                except ValueError:
                                    errors.append(f"Non-numeric priority rank {rank} in {priority_type}")
                            
                            # Check required priority fields
                            priority_fields = ["theme", "specific_issues", "narrative_elaboration"]
                            for field in priority_fields:
                                if priority.find(field) is None:
                                    errors.append(f"Missing priority field {field} in {priority_type}")
            
            # Validate participant profile
            participant_profile = root.find(".//participant_profile")
            if participant_profile is not None:
                profile_required = [
                    "age_range", 
                    "gender", 
                    "organizational_affiliation",
                    "self_described_political_stance", 
                    "occupation_sector"
                ]
                for field in profile_required:
                    if participant_profile.find(field) is None:
                        errors.append(f"Missing participant_profile field: {field}")
            
            # Validate confidence scores
            confidence_fields = [
                ".//overall_confidence",
                ".//government_responsibility", 
                ".//individual_responsibility",
                ".//structural_factors"
            ]
            
            for field_path in confidence_fields:
                field = root.find(field_path)
                if field is not None and field.text:
                    try:
                        value = float(field.text)
                        if not 0.0 <= value <= 1.0:
                            errors.append(f"Confidence value {value} out of range [0.0, 1.0] for {field_path}")
                    except ValueError:
                        errors.append(f"Non-numeric confidence value '{field.text}' for {field_path}")
            
            return len(errors) == 0, errors
            
        except ET.ParseError as e:
            return False, [f"XML parsing error: {e}"]
        except Exception as e:
            return False, [f"Validation error: {e}"]
    
    def create_validation_report(self, xml_string: str) -> str:
        """
        Create a detailed validation report for debugging.
        
        Args:
            xml_string: XML content to validate
            
        Returns:
            Formatted validation report
        """
        is_valid, errors = self.validate_xml_string(xml_string)
        
        report = []
        report.append("=== XML Schema Validation Report ===")
        report.append(f"Schema: {self.xsd_path}")
        report.append(f"Validator: {'lxml XSD' if LXML_AVAILABLE and self.schema else 'Basic ElementTree'}")
        report.append(f"Status: {'VALID' if is_valid else 'INVALID'}")
        report.append("")
        
        if errors:
            report.append("Validation Errors:")
            for i, error in enumerate(errors, 1):
                report.append(f"  {i}. {error}")
        else:
            report.append("No validation errors found.")
        
        report.append("")
        report.append(f"XML Length: {len(xml_string)} characters")
        
        # Count elements
        try:
            root = ET.fromstring(xml_string)
            element_count = len(root.findall(".//*"))
            report.append(f"Element Count: {element_count}")
        except:
            report.append("Could not parse XML for element count")
        
        return "\n".join(report)
    
    def suggest_fixes(self, errors: List[str]) -> List[str]:
        """
        Suggest fixes for common validation errors.
        
        Args:
            errors: List of validation error messages
            
        Returns:
            List of suggested fixes
        """
        suggestions = []
        
        for error in errors:
            error_lower = error.lower()
            
            if "missing" in error_lower and "section" in error_lower:
                suggestions.append(f"Add the missing section: {error}")
            elif "missing" in error_lower and "field" in error_lower:
                suggestions.append(f"Add the required field: {error}")
            elif "rank" in error_lower and "attribute" in error_lower:
                suggestions.append("Add rank attribute to priority elements (rank=\"1\", rank=\"2\", or rank=\"3\")")
            elif "confidence" in error_lower and "range" in error_lower:
                suggestions.append("Ensure confidence values are between 0.0 and 1.0")
            elif "xml syntax" in error_lower:
                suggestions.append("Fix XML syntax errors - check for unclosed tags, invalid characters")
            elif "specific_issues" in error_lower:
                suggestions.append("Use standardized format: <specific_issues><issue>text</issue></specific_issues>")
            else:
                suggestions.append(f"Address validation error: {error}")
        
        return suggestions


def install_lxml_instructions():
    """Return instructions for installing lxml for full XSD validation."""
    return """
To enable full XSD schema validation, install lxml:

pip install lxml

This will enable:
- Complete XSD schema validation
- Detailed error reporting with line numbers
- Better validation performance
- Support for all XML Schema features

Without lxml, basic validation is used which checks:
- Required elements and structure
- Data type constraints
- Value range validation
"""


if __name__ == "__main__":
    # Test schema validator
    validator = SchemaValidator()
    
    if not LXML_AVAILABLE:
        print("lxml not available - install with: pip install lxml")
        print(install_lxml_instructions())
    
    # Test with sample XML
    sample_xml = '''<?xml version="1.0" encoding="UTF-8"?>
    <annotation_result>
        <interview_level>
            <metadata>
                <interview_id>test</interview_id>
                <date>2025-05-28</date>
                <location>
                    <municipality>Test</municipality>
                    <department>Test</department>
                    <locality_size>small_town</locality_size>
                </location>
                <duration_minutes>60</duration_minutes>
                <interviewer_ids>TEST</interviewer_ids>
            </metadata>
            <participant_profile>
                <age_range>30-44</age_range>
                <gender>male</gender>
                <organizational_affiliation>Test Org</organizational_affiliation>
                <self_described_political_stance>center</self_described_political_stance>
                <occupation_sector>public_sector</occupation_sector>
            </participant_profile>
            <uncertainty_tracking>
                <overall_confidence>0.8</overall_confidence>
                <uncertainty_flags></uncertainty_flags>
                <uncertainty_narrative>Test</uncertainty_narrative>
            </uncertainty_tracking>
            <priority_summary>
                <national_priorities>
                    <priority rank="1">
                        <theme>Test Theme</theme>
                        <specific_issues><issue>test issue</issue></specific_issues>
                        <narrative_elaboration>Test narrative</narrative_elaboration>
                    </priority>
                </national_priorities>
                <local_priorities>
                    <priority rank="1">
                        <theme>Test Theme</theme>
                        <specific_issues><issue>test issue</issue></specific_issues>
                        <narrative_elaboration>Test narrative</narrative_elaboration>
                    </priority>
                </local_priorities>
            </priority_summary>
            <narrative_features>
                <dominant_frame>progress</dominant_frame>
                <frame_narrative>Test</frame_narrative>
                <temporal_orientation>present_focused</temporal_orientation>
                <temporal_narrative>Test</temporal_narrative>
                <agency_attribution>
                    <government_responsibility>0.7</government_responsibility>
                    <individual_responsibility>0.3</individual_responsibility>
                    <structural_factors>0.5</structural_factors>
                    <agency_narrative>Test</agency_narrative>
                </agency_attribution>
                <solution_orientation>moderately_specific</solution_orientation>
                <solution_narrative>Test</solution_narrative>
            </narrative_features>
            <key_narratives>
                <identity_narrative>Test</identity_narrative>
                <problem_narrative>Test</problem_narrative>
                <hope_narrative>Test</hope_narrative>
                <memorable_quotes><quote>test quote</quote></memorable_quotes>
            </key_narratives>
            <analytical_notes>
                <tensions_contradictions>Test</tensions_contradictions>
                <silences_omissions>Test</silences_omissions>
                <interviewer_reflections>Test</interviewer_reflections>
                <connections_to_broader_themes>Test</connections_to_broader_themes>
            </analytical_notes>
            <interview_dynamics>
                <rapport>good</rapport>
                <rapport_narrative>Test</rapport_narrative>
                <participant_engagement>engaged</participant_engagement>
                <engagement_narrative>Test</engagement_narrative>
                <coherence>coherent</coherence>
                <coherence_narrative>Test</coherence_narrative>
            </interview_dynamics>
        </interview_level>
        <turn_level>
            <turn>
                <turn_id>1</turn_id>
                <speaker>participant</speaker>
                <text>Test turn text</text>
                <uncertainty_tracking>
                    <coding_confidence>0.9</coding_confidence>
                    <uncertainty_markers>
                        <ambiguous_function>false</ambiguous_function>
                    </uncertainty_markers>
                </uncertainty_tracking>
                <functional_annotation>
                    <primary_function>narrative</primary_function>
                </functional_annotation>
                <content_annotation>
                    <topics><topic>test topic</topic></topics>
                    <topic_narrative>Test</topic_narrative>
                    <geographic_scope><scope>local</scope></geographic_scope>
                </content_annotation>
                <evidence_annotation>
                    <evidence_type>personal_experience</evidence_type>
                    <evidence_narrative>Test</evidence_narrative>
                    <specificity>somewhat_specific</specificity>
                </evidence_annotation>
                <stance_annotation>
                    <emotional_valence>positive</emotional_valence>
                    <emotional_intensity>0.6</emotional_intensity>
                    <emotional_narrative>Test</emotional_narrative>
                    <certainty>certain</certainty>
                </stance_annotation>
                <turn_narrative_summary>Test summary</turn_narrative_summary>
            </turn>
        </turn_level>
        <processing_metadata>
            <model_provider>openai</model_provider>
            <model_name>gpt-4o-mini</model_name>
            <timestamp>2025-06-17T10:00:00</timestamp>
            <processing_time>30.5</processing_time>
            <attempts>1</attempts>
            <temperature>0.3</temperature>
            <interview_word_count>500</interview_word_count>
            <confidence>0.8</confidence>
        </processing_metadata>
    </annotation_result>'''
    
    print("Testing schema validation...")
    is_valid, errors = validator.validate_xml_string(sample_xml)
    
    print(f"Valid: {is_valid}")
    if errors:
        print("Errors:")
        for error in errors:
            print(f"  - {error}")
    
    print("\nValidation report:")
    print(validator.create_validation_report(sample_xml))