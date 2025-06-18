"""
Progressive XML annotation system.
Fills annotation schema section by section using a single master prompt.
"""
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path
import copy
import re

from src.pipeline.annotation.annotation_engine import AnnotationEngine
from src.pipeline.annotation.schema_validator import SchemaValidator
from src.pipeline.ingestion.document_processor import InterviewDocument

logger = logging.getLogger(__name__)


class ProgressiveAnnotator:
    """Progressive XML annotation system that fills schema section by section."""
    
    def __init__(self, annotation_engine: AnnotationEngine):
        """Initialize with an annotation engine for AI calls."""
        self.engine = annotation_engine
        self.validator = SchemaValidator()
        self.master_prompt = None
        self.current_xml = None
        self.interview = None
        
    def create_skeleton(self, interview: InterviewDocument) -> ET.Element:
        """Create complete XML skeleton with placeholder sections."""
        
        # Detect conversation turns from interview text
        turns = self._detect_turns(interview.text)
        
        # Create skeleton structure
        root = ET.Element("annotation_result")
        
        # Interview level skeleton
        interview_level = ET.SubElement(root, "interview_level")
        
        # Metadata skeleton
        metadata = ET.SubElement(interview_level, "metadata")
        ET.SubElement(metadata, "interview_id").text = f"<!-- FILL: {interview.id} -->"
        ET.SubElement(metadata, "date").text = f"<!-- FILL: {interview.date} -->"
        location = ET.SubElement(metadata, "location")
        ET.SubElement(location, "municipality").text = "<!-- FILL -->"
        ET.SubElement(location, "department").text = "<!-- FILL -->"
        ET.SubElement(location, "locality_size").text = "<!-- FILL -->"
        ET.SubElement(metadata, "duration_minutes").text = "<!-- FILL -->"
        ET.SubElement(metadata, "interviewer_ids").text = "<!-- FILL -->"
        
        # Participant profile skeleton
        profile = ET.SubElement(interview_level, "participant_profile")
        ET.SubElement(profile, "age_range").text = "<!-- FILL -->"
        ET.SubElement(profile, "gender").text = "<!-- FILL -->"
        ET.SubElement(profile, "organizational_affiliation").text = "<!-- FILL -->"
        ET.SubElement(profile, "self_described_political_stance").text = "<!-- FILL -->"
        ET.SubElement(profile, "occupation_sector").text = "<!-- FILL -->"
        
        # Uncertainty tracking skeleton
        uncertainty = ET.SubElement(interview_level, "uncertainty_tracking")
        ET.SubElement(uncertainty, "overall_confidence").text = "<!-- FILL -->"
        flags = ET.SubElement(uncertainty, "uncertainty_flags")
        ET.SubElement(flags, "flag").text = "<!-- FILL -->"
        ET.SubElement(uncertainty, "uncertainty_narrative").text = "<!-- FILL -->"
        
        # Priority summary skeleton
        priority_summary = ET.SubElement(interview_level, "priority_summary")
        
        # National priorities skeleton
        national = ET.SubElement(priority_summary, "national_priorities")
        for rank in [1, 2, 3]:
            priority = ET.SubElement(national, "priority", rank=str(rank))
            ET.SubElement(priority, "theme").text = "<!-- FILL -->"
            issues = ET.SubElement(priority, "specific_issues")
            ET.SubElement(issues, "issue").text = "<!-- FILL -->"
            ET.SubElement(priority, "narrative_elaboration").text = "<!-- FILL -->"
        
        # Local priorities skeleton
        local = ET.SubElement(priority_summary, "local_priorities")
        for rank in [1, 2, 3]:
            priority = ET.SubElement(local, "priority", rank=str(rank))
            ET.SubElement(priority, "theme").text = "<!-- FILL -->"
            issues = ET.SubElement(priority, "specific_issues")
            ET.SubElement(issues, "issue").text = "<!-- FILL -->"
            ET.SubElement(priority, "narrative_elaboration").text = "<!-- FILL -->"
        
        # Narrative features skeleton
        narrative = ET.SubElement(interview_level, "narrative_features")
        ET.SubElement(narrative, "dominant_frame").text = "<!-- FILL -->"
        ET.SubElement(narrative, "frame_narrative").text = "<!-- FILL -->"
        ET.SubElement(narrative, "temporal_orientation").text = "<!-- FILL -->"
        ET.SubElement(narrative, "temporal_narrative").text = "<!-- FILL -->"
        agency = ET.SubElement(narrative, "agency_attribution")
        ET.SubElement(agency, "government_responsibility").text = "<!-- FILL -->"
        ET.SubElement(agency, "individual_responsibility").text = "<!-- FILL -->"
        ET.SubElement(agency, "structural_factors").text = "<!-- FILL -->"
        ET.SubElement(agency, "agency_narrative").text = "<!-- FILL -->"
        ET.SubElement(narrative, "solution_orientation").text = "<!-- FILL -->"
        ET.SubElement(narrative, "solution_narrative").text = "<!-- FILL -->"
        
        # Key narratives skeleton
        key_narratives = ET.SubElement(interview_level, "key_narratives")
        ET.SubElement(key_narratives, "identity_narrative").text = "<!-- FILL -->"
        ET.SubElement(key_narratives, "problem_narrative").text = "<!-- FILL -->"
        ET.SubElement(key_narratives, "hope_narrative").text = "<!-- FILL -->"
        quotes = ET.SubElement(key_narratives, "memorable_quotes")
        ET.SubElement(quotes, "quote").text = "<!-- FILL -->"
        
        # Analytical notes skeleton
        analytical = ET.SubElement(interview_level, "analytical_notes")
        ET.SubElement(analytical, "tensions_contradictions").text = "<!-- FILL -->"
        ET.SubElement(analytical, "silences_omissions").text = "<!-- FILL -->"
        ET.SubElement(analytical, "interviewer_reflections").text = "<!-- FILL -->"
        ET.SubElement(analytical, "connections_to_broader_themes").text = "<!-- FILL -->"
        
        # Interview dynamics skeleton
        dynamics = ET.SubElement(interview_level, "interview_dynamics")
        ET.SubElement(dynamics, "rapport").text = "<!-- FILL -->"
        ET.SubElement(dynamics, "rapport_narrative").text = "<!-- FILL -->"
        ET.SubElement(dynamics, "participant_engagement").text = "<!-- FILL -->"
        ET.SubElement(dynamics, "engagement_narrative").text = "<!-- FILL -->"
        ET.SubElement(dynamics, "coherence").text = "<!-- FILL -->"
        ET.SubElement(dynamics, "coherence_narrative").text = "<!-- FILL -->"
        
        # Turn level skeleton
        turn_level = ET.SubElement(root, "turn_level")
        
        for turn_data in turns:
            turn_elem = ET.SubElement(turn_level, "turn")
            ET.SubElement(turn_elem, "turn_id").text = str(turn_data['id'])
            ET.SubElement(turn_elem, "speaker").text = turn_data['speaker']
            ET.SubElement(turn_elem, "text").text = turn_data['text']
            
            # Turn uncertainty skeleton
            turn_uncertainty = ET.SubElement(turn_elem, "uncertainty_tracking")
            ET.SubElement(turn_uncertainty, "coding_confidence").text = "<!-- FILL -->"
            markers = ET.SubElement(turn_uncertainty, "uncertainty_markers")
            ET.SubElement(markers, "ambiguous_function").text = "<!-- FILL -->"
            
            # Functional annotation skeleton
            functional = ET.SubElement(turn_elem, "functional_annotation")
            reasoning = ET.SubElement(functional, "reasoning")
            reasoning.text = "<!-- FILL: Chain of thought for functional annotation -->"
            ET.SubElement(functional, "primary_function").text = "<!-- FILL -->"
            
            # Content annotation skeleton
            content = ET.SubElement(turn_elem, "content_annotation")
            reasoning = ET.SubElement(content, "reasoning")
            reasoning.text = "<!-- FILL: Chain of thought for content annotation -->"
            topics = ET.SubElement(content, "topics")
            ET.SubElement(topics, "topic").text = "<!-- FILL -->"
            ET.SubElement(content, "topic_narrative").text = "<!-- FILL -->"
            geo_scope = ET.SubElement(content, "geographic_scope")
            ET.SubElement(geo_scope, "scope").text = "<!-- FILL -->"
            
            # Evidence annotation skeleton
            evidence = ET.SubElement(turn_elem, "evidence_annotation")
            reasoning = ET.SubElement(evidence, "reasoning")
            reasoning.text = "<!-- FILL: Chain of thought for evidence annotation -->"
            ET.SubElement(evidence, "evidence_type").text = "<!-- FILL -->"
            ET.SubElement(evidence, "evidence_narrative").text = "<!-- FILL -->"
            ET.SubElement(evidence, "specificity").text = "<!-- FILL -->"
            
            # Stance annotation skeleton
            stance = ET.SubElement(turn_elem, "stance_annotation")
            reasoning = ET.SubElement(stance, "reasoning")
            reasoning.text = "<!-- FILL: Chain of thought for stance annotation -->"
            ET.SubElement(stance, "emotional_valence").text = "<!-- FILL -->"
            ET.SubElement(stance, "emotional_intensity").text = "<!-- FILL -->"
            ET.SubElement(stance, "emotional_narrative").text = "<!-- FILL -->"
            ET.SubElement(stance, "certainty").text = "<!-- FILL -->"
            
            # Turn summary
            ET.SubElement(turn_elem, "turn_narrative_summary").text = "<!-- FILL -->"
        
        # Processing metadata skeleton
        processing = ET.SubElement(root, "processing_metadata")
        ET.SubElement(processing, "model_provider").text = "<!-- FILL -->"
        ET.SubElement(processing, "model_name").text = "<!-- FILL -->"
        ET.SubElement(processing, "timestamp").text = "<!-- FILL -->"
        ET.SubElement(processing, "processing_time").text = "<!-- FILL -->"
        ET.SubElement(processing, "attempts").text = "<!-- FILL -->"
        ET.SubElement(processing, "temperature").text = "<!-- FILL -->"
        ET.SubElement(processing, "interview_word_count").text = "<!-- FILL -->"
        ET.SubElement(processing, "confidence").text = "<!-- FILL -->"
        
        return root
    
    def _detect_turns(self, interview_text: str) -> List[Dict]:
        """Detect conversation turns from interview text."""
        lines = interview_text.split('\n')
        turns = []
        current_speaker = None
        current_text = []
        turn_id = 1
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect speaker changes
            new_speaker = None
            speaker_content = line
            
            # Common speaker patterns
            if line.startswith(('Entrevistador:', 'Entrevistadora:', 'Gabriela Medina', 'Germán Busch')):
                new_speaker = 'interviewer'
                if ':' in line:
                    speaker_content = line.split(':', 1)[1].strip()
            elif line.startswith(('[GM]', '[GB]', 'GM:', 'GB:')):
                new_speaker = 'interviewer'
                speaker_content = line.split(']', 1)[-1].split(':', 1)[-1].strip()
            elif line.startswith(('María Rosales', 'Marcelo Rosales', '[MR]', '[MR2]', 'MR:', 'MR2:')):
                new_speaker = 'participant'
                if ':' in line:
                    speaker_content = line.split(':', 1)[1].strip()
                elif ']' in line:
                    speaker_content = line.split(']', 1)[-1].strip()
            elif line.startswith(('Participante:', 'P:')):
                new_speaker = 'participant'
                speaker_content = line.split(':', 1)[1].strip()
            
            # Handle speaker changes
            if new_speaker and new_speaker != current_speaker:
                # Save previous turn if it exists
                if current_speaker and current_text:
                    turns.append({
                        'id': turn_id,
                        'speaker': current_speaker,
                        'text': ' '.join(current_text).strip()
                    })
                    turn_id += 1
                
                # Start new turn
                current_speaker = new_speaker
                current_text = [speaker_content] if speaker_content else []
            else:
                # Continue current turn
                if current_speaker and line:
                    current_text.append(line)
        
        # Add final turn
        if current_speaker and current_text:
            turns.append({
                'id': turn_id,
                'speaker': current_speaker,
                'text': ' '.join(current_text).strip()
            })
        
        return turns
    
    def create_master_prompt(self, interview: InterviewDocument) -> str:
        """Create comprehensive master prompt with all guidance."""
        
        # Load the annotation prompt template
        prompt_path = Path(__file__).parent.parent.parent.parent / "config" / "prompts" / "annotation_prompt_v1.xml"
        
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt_template = f.read()
        except FileNotFoundError:
            # Fallback simple prompt
            prompt_template = "You are an expert qualitative researcher analyzing citizen consultation interviews."
        
        # Create master prompt
        master_prompt = f"""
{prompt_template}

INTERVIEW TO ANNOTATE:
{interview.text}

PROGRESSIVE ANNOTATION INSTRUCTIONS:
You will be given XML with sections marked "<!-- FILL -->" or "<!-- FILL: description -->".
Your task is to fill ONLY the marked sections, following all the guidance above.

- Read the interview text carefully
- Consider the context from already-completed sections
- For reasoning sections: Provide clear chain-of-thought analysis
- For data sections: Provide precise, schema-compliant values
- For narrative sections: Use participant's own words when possible

CRITICAL: 
- Fill only the marked section, don't change completed parts
- Follow the XSD schema requirements exactly
- Provide thoughtful reasoning for interpretive decisions
- Be systematic and complete in your analysis
"""
        
        return master_prompt
    
    def fill_section(self, xpath: str, description: str = "") -> bool:
        """Fill a specific section of the XML using prompt caching."""
        
        if self.current_xml is None:
            raise ValueError("No XML skeleton loaded")
        
        # Create current XML state for caching
        xml_str = ET.tostring(self.current_xml, encoding='unicode')
        
        # Create focused prompt (this will change for each section)
        task_prompt = f"""
CURRENT XML STATE:
{xml_str}

TASK: Fill the section at XPath: {xpath}
{description}

Return only the content that should replace the "<!-- FILL -->" placeholder.
Do not include XML tags unless they are part of the content structure.
"""
        
        try:
            # Call AI with cached master prompt
            response = self.engine._call_openai(task_prompt, 0.1, cached_content=self.master_prompt)
            
            # Update XML
            success = self._update_xml_section(xpath, response.strip())
            
            if success:
                logger.info(f"Successfully filled section: {xpath}")
            else:
                logger.error(f"Failed to fill section: {xpath}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error filling section {xpath}: {e}")
            return False
    
    def _update_xml_section(self, xpath: str, content: str) -> bool:
        """Update a specific section in the XML."""
        try:
            # Find the element
            elem = self.current_xml.find(xpath)
            if elem is None:
                logger.error(f"XPath not found: {xpath}")
                return False
            
            # Update the content
            if elem.text and "<!-- FILL" in elem.text:
                elem.text = content
            else:
                # Handle child elements
                for child in elem:
                    if child.text and "<!-- FILL" in child.text:
                        child.text = content
                        break
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating XML section: {e}")
            return False
    
    def annotate_progressively(self, interview: InterviewDocument) -> ET.Element:
        """Run complete progressive annotation."""
        
        self.interview = interview
        
        # Step 1: Create skeleton
        logger.info("Creating annotation skeleton...")
        self.current_xml = self.create_skeleton(interview)
        
        # Step 2: Create master prompt
        logger.info("Creating master prompt...")
        self.master_prompt = self.create_master_prompt(interview)
        
        # Step 3: Fill sections progressively
        sections_to_fill = [
            (".//metadata/interview_id", "Interview ID"),
            (".//metadata/date", "Interview date"),
            (".//metadata/location/municipality", "Municipality"),
            (".//metadata/location/department", "Department"),
            (".//metadata/location/locality_size", "Locality size"),
            # Add more sections as needed for testing
        ]
        
        logger.info("Starting progressive annotation...")
        for xpath, description in sections_to_fill:
            logger.info(f"Filling: {description}")
            success = self.fill_section(xpath, description)
            if not success:
                logger.error(f"Failed to fill {description}, continuing...")
        
        return self.current_xml


if __name__ == "__main__":
    # Test the progressive annotator
    from src.pipeline.ingestion.document_processor import DocumentProcessor
    
    # Find test interview
    txt_dir = Path(__file__).parent.parent.parent.parent / "data" / "processed" / "interviews_txt"
    txt_files = list(txt_dir.glob("*.txt"))
    
    if txt_files:
        test_file = min(txt_files, key=lambda f: f.stat().st_size)
        
        # Process interview
        processor = DocumentProcessor()
        interview = processor.process_interview(test_file)
        
        # Create progressive annotator
        engine = AnnotationEngine(model_provider="openai", model_name="gpt-4o-mini")
        annotator = ProgressiveAnnotator(engine)
        
        # Test skeleton creation
        skeleton = annotator.create_skeleton(interview)
        turns = skeleton.findall(".//turn")
        
        print(f"Created skeleton for interview {interview.id}")
        print(f"Detected {len(turns)} conversation turns")
        print(f"Skeleton has {len(skeleton.findall('.//*'))} total elements")
        
        # Show first few turns
        for i, turn in enumerate(turns[:3], 1):
            turn_id = turn.find("turn_id").text
            speaker = turn.find("speaker").text
            text = turn.find("text").text[:100]
            print(f"Turn {turn_id} ({speaker}): {text}...")
    else:
        print("No interview files found for testing")