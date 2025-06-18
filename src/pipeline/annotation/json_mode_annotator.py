"""
JSON mode annotation system for Uruguay interviews.
Uses OpenAI's native JSON mode for structured outputs.
"""
import json
import xml.etree.ElementTree as ET
from openai import OpenAI
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import logging
import time
from datetime import datetime

from src.pipeline.ingestion.document_processor import InterviewDocument
from src.config.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class JSONModeAnnotator:
    """Annotation system using OpenAI's native JSON mode."""
    
    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.1,
        max_retries: int = 3
    ):
        """
        Initialize JSON mode annotator.
        
        Args:
            model_name: OpenAI model to use
            temperature: Sampling temperature
            max_retries: Maximum retry attempts
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_retries = max_retries
        
        # Get API key
        config_loader = ConfigLoader()
        api_key = config_loader.get_api_key("openai")
        if not api_key:
            raise ValueError("No OpenAI API key found")
        
        self.client = OpenAI(api_key=api_key)
        
        logger.info(f"Initialized JSON mode annotator with {model_name}")
    
    def create_json_schema_prompt(self, interview: InterviewDocument) -> str:
        """Create prompt that specifies the exact JSON schema we want."""
        return f"""
You are an expert qualitative researcher analyzing a citizen consultation interview from Uruguay.

INTERVIEW TO ANALYZE:
{interview.text}

INTERVIEW METADATA:
- ID: {interview.id}
- Date: {interview.date}
- Location: {interview.location}
- Department: {interview.department}

Provide a complete systematic analysis in JSON format with the following structure:

{{
  "interview_metadata": {{
    "interview_id": "{interview.id}",
    "date": "{interview.date}",
    "municipality": "string",
    "department": "{interview.department}",
    "locality_size": "rural|small_town|medium_city|large_city",
    "duration_minutes": 45,
    "interviewer_ids": ["string"]
  }},
  "participant_profile": {{
    "age_range": "18-29|30-49|50-64|65+",
    "gender": "male|female|non_binary|prefer_not_to_say",
    "occupation_sector": "agriculture|manufacturing|services|public_sector|education|healthcare|commerce|construction|transport|unemployed|retired|other",
    "organizational_affiliation": "string or null",
    "political_stance": "string or null"
  }},
  "national_priorities": [
    {{
      "rank": 1,
      "theme": "string",
      "specific_issues": ["string"],
      "narrative_elaboration": "string with participant's own words"
    }},
    {{
      "rank": 2,
      "theme": "string", 
      "specific_issues": ["string"],
      "narrative_elaboration": "string with participant's own words"
    }},
    {{
      "rank": 3,
      "theme": "string",
      "specific_issues": ["string"], 
      "narrative_elaboration": "string with participant's own words"
    }}
  ],
  "local_priorities": [
    {{
      "rank": 1,
      "theme": "string",
      "specific_issues": ["string"],
      "narrative_elaboration": "string with participant's own words"
    }},
    {{
      "rank": 2,
      "theme": "string",
      "specific_issues": ["string"],
      "narrative_elaboration": "string with participant's own words"
    }},
    {{
      "rank": 3,
      "theme": "string",
      "specific_issues": ["string"],
      "narrative_elaboration": "string with participant's own words"
    }}
  ],
  "narrative_features": {{
    "dominant_frame": "string describing main interpretive frame",
    "frame_narrative": "string explaining how this frame manifests",
    "temporal_orientation": "past_focused|present_focused|future_focused|mixed",
    "temporal_narrative": "string explaining temporal focus",
    "solution_orientation": "problem_focused|solution_focused|balanced",
    "solution_narrative": "string explaining solution approach"
  }},
  "agency_attribution": {{
    "government_responsibility": "string describing what participant sees as government role",
    "individual_responsibility": "string describing what participant sees as individual role", 
    "structural_factors": "string describing systemic factors identified",
    "agency_narrative": "string describing overall view of who has power to create change"
  }},
  "key_narratives": {{
    "identity_narrative": "string describing how participant sees their identity and role",
    "problem_narrative": "string describing how participant frames problems",
    "hope_narrative": "string describing participant's hopes and aspirations",
    "memorable_quotes": ["string", "string", "string"]
  }},
  "conversation_turns": [
    {{
      "turn_id": 1,
      "speaker": "interviewer|participant",
      "text": "actual text of what was said",
      "functional_analysis": {{
        "reasoning": "chain-of-thought analysis of what speaker is doing",
        "primary_function": "greeting|problem_identification|solution_proposal|agreement|disagreement|question|clarification|narrative|evaluation|closing|elaboration|meta_commentary"
      }},
      "content_analysis": {{
        "reasoning": "chain-of-thought analysis of topics and content",
        "topics": ["string"],
        "geographic_scope": ["local|national|regional"],
        "topic_narrative": "how participant discusses these topics"
      }},
      "evidence_analysis": {{
        "reasoning": "chain-of-thought analysis of evidence provided",
        "evidence_type": "personal_experience|hearsay|media_report|official_data|general_knowledge|observation|none",
        "evidence_narrative": "description of evidence",
        "specificity": "highly_specific|moderately_specific|general|vague"
      }},
      "stance_analysis": {{
        "reasoning": "chain-of-thought analysis of emotions and certainty",
        "emotional_valence": "positive|negative|neutral|mixed",
        "emotional_intensity": "low|moderate|high",
        "emotional_narrative": "description of emotions expressed",
        "certainty": "certain|mostly_certain|uncertain|very_uncertain"
      }},
      "confidence": 0.85
    }}
  ],
  "interview_dynamics": {{
    "rapport": "excellent|good|adequate|poor",
    "rapport_narrative": "description of rapport quality",
    "participant_engagement": "highly_engaged|engaged|moderately_engaged|disengaged", 
    "engagement_narrative": "description of engagement level",
    "coherence": "highly_coherent|coherent|somewhat_coherent|incoherent",
    "coherence_narrative": "description of coherence level"
  }},
  "analytical_notes": {{
    "tensions_contradictions": "internal tensions in participant discourse",
    "silences_omissions": "notable silences or avoided topics",
    "interviewer_reflections": "assessment of interview quality",
    "connections_to_broader_themes": "how this connects to broader social themes"
  }},
  "overall_assessment": {{
    "confidence": 0.87,
    "uncertainty_flags": ["string"],
    "uncertainty_narrative": "description of annotation uncertainties"
  }}
}}

CRITICAL REQUIREMENTS:
1. Analyze EVERY conversation turn in the interview
2. Provide chain-of-thought reasoning for all interpretive decisions
3. Extract exactly 3 national and 3 local priorities ranked 1-3
4. Use participant's own words in narratives when possible
5. Return valid JSON only - no other text

The JSON must be complete and valid. Analyze every conversation turn systematically.
"""
    
    def annotate_interview(self, interview: InterviewDocument) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Generate annotation using OpenAI JSON mode.
        
        Args:
            interview: Interview document to annotate
            
        Returns:
            Tuple of (annotation_data, processing_metadata)
        """
        start_time = time.time()
        
        # Create prompt
        prompt = self.create_json_schema_prompt(interview)
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"JSON mode annotation attempt {attempt + 1} for interview {interview.id}")
                
                # OpenAI API call with JSON mode
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert qualitative researcher. You must respond with valid JSON only."
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    response_format={"type": "json_object"},  # This is the key for JSON mode
                    temperature=self.temperature
                )
                
                # Parse JSON response
                annotation_json = json.loads(response.choices[0].message.content)
                
                # Validate basic structure
                required_keys = ["interview_metadata", "participant_profile", "national_priorities", 
                               "local_priorities", "conversation_turns", "overall_assessment"]
                
                for key in required_keys:
                    if key not in annotation_json:
                        raise ValueError(f"Missing required key: {key}")
                
                # Validate priorities
                if len(annotation_json["national_priorities"]) != 3:
                    raise ValueError(f"Expected 3 national priorities, got {len(annotation_json['national_priorities'])}")
                
                if len(annotation_json["local_priorities"]) != 3:
                    raise ValueError(f"Expected 3 local priorities, got {len(annotation_json['local_priorities'])}")
                
                processing_time = time.time() - start_time
                
                # Create processing metadata
                metadata = {
                    "model_name": self.model_name,
                    "processing_time": processing_time,
                    "timestamp": datetime.now().isoformat(),
                    "attempt": attempt + 1,
                    "total_turns": len(annotation_json["conversation_turns"]),
                    "confidence": annotation_json["overall_assessment"]["confidence"],
                    "estimated_cost": self._estimate_cost(response.usage.prompt_tokens, response.usage.completion_tokens)
                }
                
                logger.info(f"Successfully annotated interview {interview.id} with {len(annotation_json['conversation_turns'])} turns")
                
                return annotation_json, metadata
                
            except json.JSONDecodeError as e:
                logger.warning(f"JSON decode error on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries - 1:
                    raise ValueError(f"Failed to get valid JSON after {self.max_retries} attempts")
                
            except Exception as e:
                logger.error(f"Annotation attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
        
        raise RuntimeError(f"Failed to annotate after {self.max_retries} attempts")
    
    def _estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate cost based on actual token usage."""
        # GPT-4o-mini pricing
        prompt_cost = (prompt_tokens / 1_000_000) * 0.15
        completion_cost = (completion_tokens / 1_000_000) * 0.60
        return prompt_cost + completion_cost
    
    def convert_to_xml(self, annotation_data: Dict[str, Any]) -> ET.Element:
        """Convert JSON annotation to XML format for compatibility."""
        root = ET.Element("annotation_result")
        
        # Interview level
        interview_level = ET.SubElement(root, "interview_level")
        
        # Metadata
        metadata = ET.SubElement(interview_level, "metadata")
        meta = annotation_data["interview_metadata"]
        for key, value in meta.items():
            if key == "interviewer_ids":
                ET.SubElement(metadata, key).text = ", ".join(value) if isinstance(value, list) else str(value)
            else:
                ET.SubElement(metadata, key).text = str(value)
        
        # Participant profile
        profile = ET.SubElement(interview_level, "participant_profile")
        for key, value in annotation_data["participant_profile"].items():
            if value is not None:
                ET.SubElement(profile, key).text = str(value)
        
        # Priorities
        priority_summary = ET.SubElement(interview_level, "priority_summary")
        
        # National priorities
        national = ET.SubElement(priority_summary, "national_priorities")
        for priority in annotation_data["national_priorities"]:
            priority_elem = ET.SubElement(national, "priority", rank=str(priority["rank"]))
            ET.SubElement(priority_elem, "theme").text = priority["theme"]
            issues = ET.SubElement(priority_elem, "specific_issues")
            for issue in priority["specific_issues"]:
                ET.SubElement(issues, "issue").text = issue
            ET.SubElement(priority_elem, "narrative_elaboration").text = priority["narrative_elaboration"]
        
        # Local priorities
        local = ET.SubElement(priority_summary, "local_priorities") 
        for priority in annotation_data["local_priorities"]:
            priority_elem = ET.SubElement(local, "priority", rank=str(priority["rank"]))
            ET.SubElement(priority_elem, "theme").text = priority["theme"]
            issues = ET.SubElement(priority_elem, "specific_issues")
            for issue in priority["specific_issues"]:
                ET.SubElement(issues, "issue").text = issue
            ET.SubElement(priority_elem, "narrative_elaboration").text = priority["narrative_elaboration"]
        
        # Turn level
        turn_level = ET.SubElement(root, "turn_level")
        for turn in annotation_data["conversation_turns"]:
            turn_elem = ET.SubElement(turn_level, "turn")
            ET.SubElement(turn_elem, "turn_id").text = str(turn["turn_id"])
            ET.SubElement(turn_elem, "speaker").text = turn["speaker"]
            ET.SubElement(turn_elem, "text").text = turn["text"]
            
            # Functional annotation
            functional = ET.SubElement(turn_elem, "functional_annotation")
            ET.SubElement(functional, "reasoning").text = turn["functional_analysis"]["reasoning"]
            ET.SubElement(functional, "primary_function").text = turn["functional_analysis"]["primary_function"]
            
            # Content annotation
            content = ET.SubElement(turn_elem, "content_annotation")
            ET.SubElement(content, "reasoning").text = turn["content_analysis"]["reasoning"]
            topics = ET.SubElement(content, "topics")
            for topic in turn["content_analysis"]["topics"]:
                ET.SubElement(topics, "topic").text = topic
            ET.SubElement(content, "topic_narrative").text = turn["content_analysis"]["topic_narrative"]
            geo_scope = ET.SubElement(content, "geographic_scope")
            for scope in turn["content_analysis"]["geographic_scope"]:
                ET.SubElement(geo_scope, "scope").text = scope
        
        return root


def main():
    """Test the JSON mode annotator."""
    # Find test interview
    txt_dir = Path("data/processed/interviews_txt")
    txt_files = list(txt_dir.glob("*.txt"))
    
    if not txt_files:
        print("❌ No interview files found")
        return
    
    # Use smallest file
    test_file = min(txt_files, key=lambda f: f.stat().st_size)
    
    # Process interview
    from src.pipeline.ingestion.document_processor import DocumentProcessor
    processor = DocumentProcessor()
    interview = processor.process_interview(test_file)
    
    print(f"🎯 JSON MODE ANNOTATION TEST")
    print(f"Interview: {interview.id}")
    print(f"Word count: {len(interview.text.split()):,}")
    print(f"Estimated cost: ~$0.003")
    print()
    
    # Create annotator
    annotator = JSONModeAnnotator()
    
    try:
        print("🤖 Making JSON mode API call...")
        annotation_data, metadata = annotator.annotate_interview(interview)
        
        print("✅ JSON mode annotation successful!")
        print()
        print("📊 RESULTS:")
        print(f"  Turns annotated: {len(annotation_data['conversation_turns'])}")
        print(f"  National priorities: {len(annotation_data['national_priorities'])}")
        print(f"  Local priorities: {len(annotation_data['local_priorities'])}")
        print(f"  Processing time: {metadata['processing_time']:.1f}s")
        print(f"  Actual cost: ${metadata['estimated_cost']:.4f}")
        
        # Save result
        output_file = "json_mode_annotation_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(annotation_data, f, indent=2, ensure_ascii=False)
        
        print(f"  Saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Annotation failed: {e}")


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path.cwd()))
    main()