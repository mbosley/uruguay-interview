"""
Instructor-based annotation system for Uruguay interviews.
Extracts complete structured annotations in a single API call with automatic validation.
"""
import instructor
import xml.etree.ElementTree as ET
from openai import OpenAI
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import logging
import time
from datetime import datetime

from src.pipeline.annotation.instructor_models import CompleteInterviewAnnotation
from src.pipeline.ingestion.document_processor import InterviewDocument
from src.config.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class InstructorAnnotator:
    """Single-call annotation system using Instructor for structured outputs."""
    
    def __init__(
        self, 
        model_provider: str = "openai",
        model_name: str = "gpt-4.1-nano",
        temperature: float = 0.1,
        max_retries: int = 3
    ):
        """
        Initialize the Instructor-based annotator.
        
        Args:
            model_provider: AI provider (currently supports 'openai')
            model_name: Specific model to use
            temperature: Sampling temperature for AI calls
            max_retries: Maximum retries for validation failures
        """
        self.model_provider = model_provider
        self.model_name = model_name
        self.temperature = temperature
        self.max_retries = max_retries
        
        # Get API key
        config_loader = ConfigLoader()
        api_key = config_loader.get_api_key(model_provider)
        
        if not api_key:
            raise ValueError(f"No API key found for provider: {model_provider}")
        
        # Initialize client with Instructor
        if model_provider == "openai":
            openai_client = OpenAI(api_key=api_key)
            self.client = instructor.from_openai(openai_client)
        else:
            raise ValueError(f"Unsupported provider: {model_provider}")
        
        # Load annotation schema prompt
        self.annotation_prompt = self._load_annotation_prompt()
        
        logger.info(f"Initialized Instructor annotator with {model_provider}:{model_name}")
    
    def _load_annotation_prompt(self) -> str:
        """Load the annotation prompt template."""
        prompt_path = Path(__file__).parent.parent.parent.parent / "config" / "prompts" / "annotation_prompt_v1.xml"
        
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            # Fallback prompt if file not found
            return """
You are an expert qualitative researcher specializing in citizen consultation interviews.
Analyze the interview systematically and provide detailed annotations following the structured schema.
Provide chain-of-thought reasoning for all interpretive decisions.
"""
    
    def annotate_interview(
        self, 
        interview: InterviewDocument
    ) -> Tuple[CompleteInterviewAnnotation, Dict[str, Any]]:
        """
        Generate complete structured annotation for an interview.
        
        Args:
            interview: Processed interview document
            
        Returns:
            Tuple of (complete annotation, processing metadata)
        """
        start_time = time.time()
        
        # Create comprehensive prompt
        system_prompt = """You are an expert qualitative researcher specializing in citizen consultations from Uruguay. 

Your task is to provide a complete, systematic analysis of this interview following rigorous qualitative research standards.

CRITICAL REQUIREMENTS:
1. Analyze EVERY conversation turn individually with detailed reasoning
2. Provide chain-of-thought analysis for all interpretive decisions  
3. Extract national and local priorities with supporting evidence
4. Assess narrative patterns, emotional content, and evidence types
5. Maintain high standards for qualitative research validity
6. Be thorough but precise in your analysis

Follow the structured schema exactly. Each reasoning field should contain your analytical thinking process."""
        
        user_prompt = f"""
{self.annotation_prompt}

INTERVIEW TO ANALYZE:
{interview.text}

INTERVIEW METADATA:
- ID: {interview.id}
- Date: {interview.date}
- Location: {interview.location}
- Department: {interview.department}

Provide a complete systematic analysis following the structured annotation schema.
Analyze every conversation turn with detailed reasoning for each annotation decision.
"""
        
        try:
            logger.info(f"Starting Instructor annotation for interview {interview.id}")
            
            # Single API call with automatic validation and retries
            annotation = self.client.chat.completions.create(
                model=self.model_name,
                response_model=CompleteInterviewAnnotation,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_retries=self.max_retries
            )
            
            processing_time = time.time() - start_time
            
            # Create processing metadata
            metadata = {
                "model_provider": self.model_provider,
                "model_name": self.model_name,
                "timestamp": datetime.now().isoformat(),
                "processing_time": processing_time,
                "temperature": self.temperature,
                "interview_word_count": len(interview.text.split()),
                "total_turns_annotated": len(annotation.turns),
                "overall_confidence": annotation.overall_confidence,
                "validation_retries": 0  # Instructor handles retries internally
            }
            
            logger.info(f"Successfully annotated interview {interview.id} with {len(annotation.turns)} turns in {processing_time:.2f}s")
            
            return annotation, metadata
            
        except Exception as e:
            logger.error(f"Failed to annotate interview {interview.id}: {e}")
            raise
    
    def convert_to_xml(self, annotation: CompleteInterviewAnnotation) -> ET.Element:
        """
        Convert Pydantic annotation to XML format for compatibility.
        
        Args:
            annotation: Complete interview annotation
            
        Returns:
            XML element tree representation
        """
        # Create root element
        root = ET.Element("annotation_result")
        
        # ===== INTERVIEW LEVEL =====
        interview_level = ET.SubElement(root, "interview_level")
        
        # Metadata
        metadata = ET.SubElement(interview_level, "metadata")
        ET.SubElement(metadata, "interview_id").text = annotation.interview_id
        ET.SubElement(metadata, "date").text = annotation.date
        
        location = ET.SubElement(metadata, "location")
        ET.SubElement(location, "municipality").text = annotation.location.municipality
        ET.SubElement(location, "department").text = annotation.location.department
        ET.SubElement(location, "locality_size").text = annotation.location.locality_size
        
        if annotation.duration_minutes:
            ET.SubElement(metadata, "duration_minutes").text = str(annotation.duration_minutes)
        ET.SubElement(metadata, "interviewer_ids").text = ", ".join(annotation.interviewer_ids)
        
        # Participant profile
        profile = ET.SubElement(interview_level, "participant_profile")
        ET.SubElement(profile, "age_range").text = annotation.participant_profile.age_range
        ET.SubElement(profile, "gender").text = annotation.participant_profile.gender
        ET.SubElement(profile, "occupation_sector").text = annotation.participant_profile.occupation_sector
        if annotation.participant_profile.organizational_affiliation:
            ET.SubElement(profile, "organizational_affiliation").text = annotation.participant_profile.organizational_affiliation
        if annotation.participant_profile.self_described_political_stance:
            ET.SubElement(profile, "self_described_political_stance").text = annotation.participant_profile.self_described_political_stance
        
        # Priority summary
        priority_summary = ET.SubElement(interview_level, "priority_summary")
        
        # National priorities
        national = ET.SubElement(priority_summary, "national_priorities")
        for priority in annotation.national_priorities:
            priority_elem = ET.SubElement(national, "priority", rank=str(priority.rank))
            ET.SubElement(priority_elem, "theme").text = priority.theme
            issues = ET.SubElement(priority_elem, "specific_issues")
            for issue in priority.specific_issues:
                ET.SubElement(issues, "issue").text = issue
            ET.SubElement(priority_elem, "narrative_elaboration").text = priority.narrative_elaboration
        
        # Local priorities  
        local = ET.SubElement(priority_summary, "local_priorities")
        for priority in annotation.local_priorities:
            priority_elem = ET.SubElement(local, "priority", rank=str(priority.rank))
            ET.SubElement(priority_elem, "theme").text = priority.theme
            issues = ET.SubElement(priority_elem, "specific_issues")
            for issue in priority.specific_issues:
                ET.SubElement(issues, "issue").text = issue
            ET.SubElement(priority_elem, "narrative_elaboration").text = priority.narrative_elaboration
        
        # Narrative features
        narrative = ET.SubElement(interview_level, "narrative_features")
        ET.SubElement(narrative, "dominant_frame").text = annotation.dominant_frame
        ET.SubElement(narrative, "frame_narrative").text = annotation.frame_narrative
        ET.SubElement(narrative, "temporal_orientation").text = annotation.temporal_orientation
        ET.SubElement(narrative, "temporal_narrative").text = annotation.temporal_narrative
        
        agency = ET.SubElement(narrative, "agency_attribution")
        ET.SubElement(agency, "government_responsibility").text = annotation.agency_attribution.government_responsibility
        ET.SubElement(agency, "individual_responsibility").text = annotation.agency_attribution.individual_responsibility
        ET.SubElement(agency, "structural_factors").text = annotation.agency_attribution.structural_factors
        ET.SubElement(agency, "agency_narrative").text = annotation.agency_attribution.agency_narrative
        
        ET.SubElement(narrative, "solution_orientation").text = annotation.solution_orientation
        ET.SubElement(narrative, "solution_narrative").text = annotation.solution_narrative
        
        # Key narratives
        key_narratives = ET.SubElement(interview_level, "key_narratives")
        ET.SubElement(key_narratives, "identity_narrative").text = annotation.key_narratives.identity_narrative
        ET.SubElement(key_narratives, "problem_narrative").text = annotation.key_narratives.problem_narrative
        ET.SubElement(key_narratives, "hope_narrative").text = annotation.key_narratives.hope_narrative
        quotes = ET.SubElement(key_narratives, "memorable_quotes")
        for quote in annotation.key_narratives.memorable_quotes:
            ET.SubElement(quotes, "quote").text = quote
        
        # Analytical notes
        analytical = ET.SubElement(interview_level, "analytical_notes")
        ET.SubElement(analytical, "tensions_contradictions").text = annotation.tensions_contradictions
        ET.SubElement(analytical, "silences_omissions").text = annotation.silences_omissions
        ET.SubElement(analytical, "interviewer_reflections").text = annotation.interviewer_reflections
        ET.SubElement(analytical, "connections_to_broader_themes").text = annotation.connections_to_broader_themes
        
        # Interview dynamics
        dynamics = ET.SubElement(interview_level, "interview_dynamics")
        ET.SubElement(dynamics, "rapport").text = annotation.interview_dynamics.rapport
        ET.SubElement(dynamics, "rapport_narrative").text = annotation.interview_dynamics.rapport_narrative
        ET.SubElement(dynamics, "participant_engagement").text = annotation.interview_dynamics.participant_engagement
        ET.SubElement(dynamics, "engagement_narrative").text = annotation.interview_dynamics.engagement_narrative
        ET.SubElement(dynamics, "coherence").text = annotation.interview_dynamics.coherence
        ET.SubElement(dynamics, "coherence_narrative").text = annotation.interview_dynamics.coherence_narrative
        
        # Uncertainty tracking
        uncertainty = ET.SubElement(interview_level, "uncertainty_tracking")
        ET.SubElement(uncertainty, "overall_confidence").text = str(annotation.overall_confidence)
        flags = ET.SubElement(uncertainty, "uncertainty_flags")
        for flag in annotation.uncertainty_flags:
            ET.SubElement(flags, "flag").text = flag
        ET.SubElement(uncertainty, "uncertainty_narrative").text = annotation.uncertainty_narrative
        
        # ===== TURN LEVEL =====
        turn_level = ET.SubElement(root, "turn_level")
        
        for turn in annotation.turns:
            turn_elem = ET.SubElement(turn_level, "turn")
            ET.SubElement(turn_elem, "turn_id").text = str(turn.turn_id)
            ET.SubElement(turn_elem, "speaker").text = turn.speaker
            ET.SubElement(turn_elem, "text").text = turn.text
            
            # Turn uncertainty
            turn_uncertainty = ET.SubElement(turn_elem, "uncertainty_tracking")
            ET.SubElement(turn_uncertainty, "coding_confidence").text = str(turn.uncertainty_tracking.coding_confidence)
            markers = ET.SubElement(turn_uncertainty, "uncertainty_markers")
            ET.SubElement(markers, "ambiguous_function").text = str(turn.uncertainty_tracking.ambiguous_function).lower()
            
            # Functional annotation
            functional = ET.SubElement(turn_elem, "functional_annotation")
            ET.SubElement(functional, "reasoning").text = turn.functional_annotation.reasoning
            ET.SubElement(functional, "primary_function").text = turn.functional_annotation.primary_function
            
            # Content annotation
            content = ET.SubElement(turn_elem, "content_annotation")
            ET.SubElement(content, "reasoning").text = turn.content_annotation.reasoning
            topics = ET.SubElement(content, "topics")
            for topic in turn.content_annotation.topics:
                ET.SubElement(topics, "topic").text = topic
            ET.SubElement(content, "topic_narrative").text = turn.content_annotation.topic_narrative
            geo_scope = ET.SubElement(content, "geographic_scope")
            for scope in turn.content_annotation.geographic_scope:
                ET.SubElement(geo_scope, "scope").text = scope
            
            # Evidence annotation
            evidence = ET.SubElement(turn_elem, "evidence_annotation")
            ET.SubElement(evidence, "reasoning").text = turn.evidence_annotation.reasoning
            ET.SubElement(evidence, "evidence_type").text = turn.evidence_annotation.evidence_type
            ET.SubElement(evidence, "evidence_narrative").text = turn.evidence_annotation.evidence_narrative
            ET.SubElement(evidence, "specificity").text = turn.evidence_annotation.specificity
            
            # Stance annotation
            stance = ET.SubElement(turn_elem, "stance_annotation")
            ET.SubElement(stance, "reasoning").text = turn.stance_annotation.reasoning
            ET.SubElement(stance, "emotional_valence").text = turn.stance_annotation.emotional_valence
            ET.SubElement(stance, "emotional_intensity").text = turn.stance_annotation.emotional_intensity
            ET.SubElement(stance, "emotional_narrative").text = turn.stance_annotation.emotional_narrative
            ET.SubElement(stance, "certainty").text = turn.stance_annotation.certainty
            
            # Turn summary
            ET.SubElement(turn_elem, "turn_narrative_summary").text = turn.turn_narrative_summary
        
        # ===== PROCESSING METADATA =====
        processing = ET.SubElement(root, "processing_metadata")
        ET.SubElement(processing, "model_provider").text = self.model_provider
        ET.SubElement(processing, "model_name").text = self.model_name
        ET.SubElement(processing, "timestamp").text = datetime.now().isoformat()
        ET.SubElement(processing, "confidence").text = str(annotation.overall_confidence)
        
        return root
    
    def calculate_cost_estimate(self, interview: InterviewDocument) -> Dict[str, float]:
        """
        Calculate cost estimate for annotating an interview.
        
        Args:
            interview: Interview to estimate cost for
            
        Returns:
            Cost breakdown dictionary
        """
        # Token estimates
        input_tokens = len(interview.text.split()) * 1.3 + len(self.annotation_prompt.split()) * 1.3
        output_tokens = 3000  # Estimated for complete annotation
        
        # GPT-4.1-nano pricing
        cost_per_1m_input = 0.10
        cost_per_1m_output = 0.40
        
        input_cost = (input_tokens / 1_000_000) * cost_per_1m_input
        output_cost = (output_tokens / 1_000_000) * cost_per_1m_output
        total_cost = input_cost + output_cost
        
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost
        }


if __name__ == "__main__":
    # Test the Instructor annotator
    from src.pipeline.ingestion.document_processor import DocumentProcessor
    
    # Find test interview
    txt_dir = Path(__file__).parent.parent.parent.parent / "data" / "processed" / "interviews_txt"
    txt_files = list(txt_dir.glob("*.txt"))
    
    if txt_files:
        # Use smallest file for testing
        test_file = min(txt_files, key=lambda f: f.stat().st_size)
        
        # Process interview
        processor = DocumentProcessor()
        interview = processor.process_interview(test_file)
        
        # Create annotator
        annotator = InstructorAnnotator(model_name="gpt-4o-mini")  # Use cheaper model for testing
        
        # Calculate cost
        cost_estimate = annotator.calculate_cost_estimate(interview)
        print(f"Cost estimate for interview {interview.id}: ${cost_estimate['total_cost']:.4f}")
        
        # Test annotation (uncomment to run actual API call)
        # annotation, metadata = annotator.annotate_interview(interview)
        # print(f"Annotated {len(annotation.turns)} turns with confidence {annotation.overall_confidence}")
    else:
        print("No interview files found for testing")