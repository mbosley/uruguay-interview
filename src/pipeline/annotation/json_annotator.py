"""
Enhanced JSON mode annotation system incorporating XML schema richness.
Balances comprehensive analysis with cost efficiency.
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


class EnhancedJSONAnnotator:
    """Enhanced JSON annotation system incorporating XML schema richness."""
    
    def __init__(
        self,
        model_name: str = "gpt-4.1-nano",
        temperature: float = 0.1,
        max_retries: int = 3
    ):
        """
        Initialize enhanced JSON annotator.
        
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
        
        logger.info(f"Initialized enhanced JSON annotator with {model_name}")
    
    def create_enhanced_prompt(self, interview: InterviewDocument) -> str:
        """Create comprehensive prompt incorporating XML schema guidance."""
        return f"""
You are a skilled qualitative researcher with expertise in citizen consultations, political discourse analysis, and Latin American contexts. You combine systematic coding with interpretive sensitivity, balancing consistency with nuance.

ROLE AND MINDSET:
- Approach each interview with curiosity and respect for the participant's perspective
- Look for both what is said and how it is said
- Notice patterns while remaining alert to uniqueness
- Connect individual experiences to broader social narratives
- Maintain reflexivity about your own interpretive position

ANNOTATION PHILOSOPHY:
1. **Faithful Representation**: Accurately represent the participant's views and experiences. When in doubt, stay closer to their language and framing.
2. **Systematic Flexibility**: Use categorical codes for comparability, but use narratives to capture what categories miss.
3. **Contextual Sensitivity**: Participants speak from specific social positions and local contexts. What seems "local" in the capital may be national for rural areas.
4. **Analytical Humility**: You are interpreting, not judging. Avoid evaluating correctness of participants' views.

COMMON URUGUAYAN INTERVIEW PATTERNS TO RECOGNIZE:
- **Generational Decline Narrative**: Compare past/present through children's experiences ("antes", "ya no es como", "se está perdiendo")
- **Abandonment by State**: Government has forgotten rural/peripheral areas, with specific service failures
- **Youth Exodus**: Young people leaving for education/work and not returning, connected to economic decline
- **Public-Private Tensions**: Defending public services in principle while acknowledging failures

INTERVIEW TO ANALYZE:
{interview.text}

METADATA:
- ID: {interview.id}
- Date: {interview.date}
- Location: {interview.location}
- Department: {interview.department}

Provide systematic analysis in JSON format following this enhanced schema:

{{
  "annotation_metadata": {{
    "annotator_approach": "enhanced_json_with_xml_guidance",
    "annotation_timestamp": "{datetime.now().isoformat()}",
    "interview_id": "{interview.id}",
    "overall_confidence": 0.85,
    "uncertainty_flags": ["cultural_context_needed", "emotional_overwhelm"],
    "uncertainty_narrative": "Description of annotation uncertainties and impact"
  }},
  "interview_metadata": {{
    "interview_id": "{interview.id}",
    "date": "{interview.date}",
    "municipality": "string",
    "department": "{interview.department}",
    "locality_size": "rural|small_town|medium_city|large_city",
    "duration_minutes": 45,
    "interviewer_ids": ["string"],
    "interview_context": "Brief description of interview setting/circumstances"
  }},
  "participant_profile": {{
    "age_range": "18-29|30-49|50-64|65+",
    "gender": "male|female|non_binary|prefer_not_to_say",
    "occupation_sector": "agriculture|manufacturing|services|public_sector|education|healthcare|commerce|construction|transport|unemployed|retired|other",
    "organizational_affiliation": "string or null",
    "self_described_political_stance": "string or null",
    "profile_confidence": 0.8,
    "profile_notes": "What information is explicit vs inferred"
  }},
  "priority_analysis": {{
    "national_priorities": [
      {{
        "rank": 1,
        "theme": "string",
        "specific_issues": ["string"],
        "narrative_elaboration": "Rich description of how participant frames this priority, using their own words",
        "emotional_intensity": 0.7,
        "supporting_quotes": ["participant quote 1", "participant quote 2"],
        "confidence": 0.9,
        "reasoning": "Why this was coded as priority 1"
      }},
      {{
        "rank": 2,
        "theme": "string", 
        "specific_issues": ["string"],
        "narrative_elaboration": "Rich description using participant's framing",
        "emotional_intensity": 0.5,
        "supporting_quotes": ["participant quote"],
        "confidence": 0.8,
        "reasoning": "Why this was coded as priority 2"
      }},
      {{
        "rank": 3,
        "theme": "string",
        "specific_issues": ["string"],
        "narrative_elaboration": "Rich description using participant's framing",
        "emotional_intensity": 0.4,
        "supporting_quotes": ["participant quote"],
        "confidence": 0.7,
        "reasoning": "Why this was coded as priority 3"
      }}
    ],
    "local_priorities": [
      {{
        "rank": 1,
        "theme": "string",
        "specific_issues": ["string"],
        "narrative_elaboration": "Rich description using participant's framing",
        "emotional_intensity": 0.8,
        "supporting_quotes": ["participant quote"],
        "confidence": 0.9,
        "reasoning": "Why this was coded as local priority 1"
      }},
      {{
        "rank": 2,
        "theme": "string",
        "specific_issues": ["string"],
        "narrative_elaboration": "Rich description using participant's framing",
        "emotional_intensity": 0.6,
        "supporting_quotes": ["participant quote"],
        "confidence": 0.8,
        "reasoning": "Why this was coded as local priority 2"
      }},
      {{
        "rank": 3,
        "theme": "string",
        "specific_issues": ["string"],
        "narrative_elaboration": "Rich description using participant's framing",
        "emotional_intensity": 0.4,
        "supporting_quotes": ["participant quote"],
        "confidence": 0.7,
        "reasoning": "Why this was coded as local priority 3"
      }}
    ],
    "priority_methodology_notes": "How priorities were identified and any edge cases"
  }},
  "narrative_features": {{
    "dominant_frame": "decline|progress|stagnation|mixed",
    "frame_narrative": "Overarching story participant tells about their community/country",
    "frame_confidence": 0.85,
    "temporal_orientation": "past_focused|present_focused|future_focused|mixed",
    "temporal_narrative": "How participant relates past, present, and future",
    "agency_attribution": {{
      "government_responsibility": "What participant sees as government role (0.0-1.0)",
      "individual_responsibility": "What participant sees as individual role (0.0-1.0)",
      "structural_factors": "Systemic factors identified (0.0-1.0)",
      "agency_narrative": "Overall view of who has power to create change"
    }},
    "solution_orientation": "highly_specific|moderately_specific|vague|none",
    "solution_narrative": "How participant envisions change happening",
    "cultural_patterns_identified": ["generational_decline", "state_abandonment", "youth_exodus", "public_private_tensions"],
    "narrative_confidence": 0.8
  }},
  "key_narratives": {{
    "identity_narrative": "How participant positions themselves and their community",
    "problem_narrative": "Core story about what's wrong and why",
    "hope_narrative": "What gives them hope or optimism, if anything",
    "memorable_quotes": ["striking quote 1", "representative quote 2", "key quote 3"],
    "rhetorical_strategies": ["metaphors used", "comparison patterns", "emotional appeals"],
    "narrative_confidence": 0.85
  }},
  "conversation_analysis": {{
    "total_turns_detected": 15,
    "participant_turns": 8,
    "interviewer_turns": 7,
    "turns": [
      {{
        "turn_id": 1,
        "speaker": "interviewer|participant",
        "text": "actual text of what was said",
        "turn_analysis": {{
          "reasoning": "Detailed chain-of-thought analysis of what's happening",
          "primary_function": "greeting|problem_identification|solution_proposal|agreement|disagreement|question|clarification|personal_narrative|evaluation|closing|elaboration|meta_commentary",
          "secondary_functions": ["justification", "exemplification", "comparison"],
          "function_confidence": 0.9
        }},
        "content_analysis": {{
          "reasoning": "Chain-of-thought analysis of topics and content",
          "topics": ["employment", "security", "education"],
          "geographic_scope": ["local", "national"],
          "temporal_reference": "past|present|future|comparison",
          "topic_narrative": "How participant discusses these topics",
          "content_confidence": 0.85
        }},
        "evidence_analysis": {{
          "reasoning": "Analysis of evidence provided",
          "evidence_type": "personal_experience|family_experience|community_observation|hearsay|media_reference|statistical_claim|general_assertion|hypothetical",
          "evidence_narrative": "Description of how evidence is used",
          "specificity": "very_specific|somewhat_specific|general|vague",
          "evidence_confidence": 0.8
        }},
        "emotional_analysis": {{
          "reasoning": "Analysis of emotions and certainty",
          "emotional_valence": "positive|mostly_positive|neutral|mostly_negative|negative|mixed",
          "emotional_intensity": 0.7,
          "specific_emotions": ["frustration", "hope", "concern"],
          "emotional_narrative": "Description of emotional texture and journey",
          "certainty": "very_certain|somewhat_certain|uncertain|ambivalent",
          "rhetorical_features": "Metaphors, linguistic choices, cultural references"
        }},
        "uncertainty_tracking": {{
          "coding_confidence": 0.85,
          "ambiguous_aspects": ["function", "emotional_tone"],
          "edge_case_flag": false,
          "alternative_interpretations": ["Other valid reading of this turn"],
          "resolution_strategy": "participant_framing_privileged|context_from_other_turns|conservative_coding",
          "annotator_notes": "Additional concerns or observations"
        }},
        "moral_foundations_analysis": {{
          "reasoning": "Analysis of moral foundations invoked",
          "care_harm": 0.0,
          "fairness_cheating": 0.0,
          "loyalty_betrayal": 0.0,
          "authority_subversion": 0.0,
          "sanctity_degradation": 0.0,
          "liberty_oppression": 0.0,
          "dominant_foundation": "none|care_harm|fairness_cheating|loyalty_betrayal|authority_subversion|sanctity_degradation|liberty_oppression",
          "foundations_narrative": "How moral concerns are expressed",
          "mft_confidence": 0.0
        }},
        "turn_significance": "Why this turn matters for understanding the participant"
      }}
    ]
  }},
  "interview_dynamics": {{
    "rapport": "excellent|good|adequate|poor",
    "rapport_narrative": "Quality of interaction and key moments",
    "participant_engagement": "highly_engaged|engaged|moderately_engaged|disengaged",
    "engagement_narrative": "How engagement evolved through interview",
    "coherence": "highly_coherent|coherent|somewhat_coherent|incoherent",
    "coherence_narrative": "Nature of storytelling and argumentation",
    "interviewer_effects": "Notable influence of interviewer on responses",
    "dynamics_confidence": 0.8
  }},
  "analytical_synthesis": {{
    "tensions_contradictions": "Internal tensions in participant discourse",
    "silences_omissions": "Notable silences or avoided topics",
    "patterns_across_turns": "How themes develop through the conversation",
    "cultural_context_notes": "Local knowledge that would aid interpretation",
    "connections_to_broader_themes": "How this connects to broader social patterns",
    "analytical_confidence": 0.8
  }},
  "quality_assessment": {{
    "annotation_completeness": 0.9,
    "interpretive_depth": 0.85,
    "evidence_grounding": 0.9,
    "cultural_sensitivity": 0.8,
    "systematic_consistency": 0.85,
    "areas_needing_review": ["specific aspects that need team discussion"],
    "recommended_follow_up": ["validation steps or additional analysis needed"]
  }}
}}

CRITICAL REQUIREMENTS:
1. Analyze EVERY conversation turn systematically
2. Provide detailed chain-of-thought reasoning for all interpretive decisions
3. Extract exactly 3 national and 3 local priorities with confidence scores
4. Use participant's own words extensively in narratives
5. Include uncertainty tracking and alternative interpretations where relevant
6. Apply cultural context knowledge about Uruguayan interview patterns
7. Maintain analytical humility - interpret, don't judge
8. Ground all interpretations in specific textual evidence
9. Return valid JSON only - no other text

MORAL FOUNDATIONS ANALYSIS (6th Dimension):
Identify moral foundations in each turn:
- Care/Harm: Protection, suffering ("cuidar", "sufrir", "proteger")
- Fairness/Cheating: Justice, corruption ("justo", "corrupción", "derechos")
- Loyalty/Betrayal: Community, abandonment ("abandonar", "comunidad", "unidos")
- Authority/Subversion: Respect, tradition ("respeto", "autoridad", "orden")
- Sanctity/Degradation: Purity, values ("valores", "moral", "contaminar")
- Liberty/Oppression: Freedom, control ("libertad", "control", "oprimir")

Score 0.0-1.0 based on intensity. Note Uruguayan patterns like state abandonment (Loyalty+Care).

Focus on faithful representation while achieving systematic analysis. When uncertain, document the uncertainty rather than forcing false precision.
"""
    
    def annotate_interview(self, interview: InterviewDocument) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Generate enhanced annotation using OpenAI JSON mode.
        
        Args:
            interview: Interview document to annotate
            
        Returns:
            Tuple of (annotation_data, processing_metadata)
        """
        start_time = time.time()
        
        # Create enhanced prompt
        prompt = self.create_enhanced_prompt(interview)
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Enhanced JSON annotation attempt {attempt + 1} for interview {interview.id}")
                
                # OpenAI API call with JSON mode
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert qualitative researcher specializing in Latin American political discourse. You must respond with valid JSON only."
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    response_format={"type": "json_object"},
                    temperature=self.temperature
                )
                
                # Parse JSON response
                annotation_json = json.loads(response.choices[0].message.content)
                
                # Validate enhanced structure
                required_sections = [
                    "annotation_metadata", "interview_metadata", "participant_profile", 
                    "priority_analysis", "narrative_features", "key_narratives",
                    "conversation_analysis", "interview_dynamics", "analytical_synthesis",
                    "quality_assessment"
                ]
                
                for section in required_sections:
                    if section not in annotation_json:
                        raise ValueError(f"Missing required section: {section}")
                
                # Validate priorities
                priority_analysis = annotation_json["priority_analysis"]
                if len(priority_analysis["national_priorities"]) != 3:
                    raise ValueError(f"Expected 3 national priorities, got {len(priority_analysis['national_priorities'])}")
                
                if len(priority_analysis["local_priorities"]) != 3:
                    raise ValueError(f"Expected 3 local priorities, got {len(priority_analysis['local_priorities'])}")
                
                # Validate conversation analysis
                conv_analysis = annotation_json["conversation_analysis"]
                if "turns" not in conv_analysis or len(conv_analysis["turns"]) == 0:
                    raise ValueError("No conversation turns found in analysis")
                
                processing_time = time.time() - start_time
                
                # Create processing metadata
                metadata = {
                    "model_name": self.model_name,
                    "annotation_approach": "enhanced_json_with_xml_guidance",
                    "processing_time": processing_time,
                    "timestamp": datetime.now().isoformat(),
                    "attempt": attempt + 1,
                    "total_turns": len(conv_analysis["turns"]),
                    "overall_confidence": annotation_json["annotation_metadata"]["overall_confidence"],
                    "estimated_cost": self._estimate_cost(response.usage.prompt_tokens, response.usage.completion_tokens),
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens
                }
                
                logger.info(f"Successfully created enhanced annotation for interview {interview.id} with {len(conv_analysis['turns'])} turns")
                
                return annotation_json, metadata
                
            except json.JSONDecodeError as e:
                logger.warning(f"JSON decode error on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries - 1:
                    raise ValueError(f"Failed to get valid JSON after {self.max_retries} attempts")
                
            except Exception as e:
                logger.error(f"Enhanced annotation attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
        
        raise RuntimeError(f"Failed to annotate after {self.max_retries} attempts")
    
    def _estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate cost based on actual token usage."""
        if "gpt-4.1-nano" in self.model_name:
            # GPT-4.1 nano pricing - much cheaper!
            prompt_cost = (prompt_tokens / 1_000_000) * 0.10
            completion_cost = (completion_tokens / 1_000_000) * 0.40
        elif "gpt-4o-mini" in self.model_name:
            # GPT-4o-mini pricing
            prompt_cost = (prompt_tokens / 1_000_000) * 0.15
            completion_cost = (completion_tokens / 1_000_000) * 0.60
        else:
            # Default to GPT-4o pricing
            prompt_cost = (prompt_tokens / 1_000_000) * 2.50
            completion_cost = (completion_tokens / 1_000_000) * 10.00
        return prompt_cost + completion_cost
    
    def validate_annotation_quality(self, annotation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate annotation against quality criteria."""
        quality_report = {
            "overall_score": 0.0,
            "dimension_scores": {},
            "issues_found": [],
            "recommendations": []
        }
        
        # Check completeness
        required_quotes = 0
        actual_quotes = 0
        
        # Priority quotes
        for priority_list in [annotation_data["priority_analysis"]["national_priorities"], 
                             annotation_data["priority_analysis"]["local_priorities"]]:
            for priority in priority_list:
                required_quotes += 1
                if priority.get("supporting_quotes") and len(priority["supporting_quotes"]) > 0:
                    actual_quotes += 1
        
        quote_completeness = actual_quotes / required_quotes if required_quotes > 0 else 0.0
        quality_report["dimension_scores"]["quote_completeness"] = quote_completeness
        
        # Check confidence tracking
        has_confidence_scores = True
        confidence_fields = [
            "annotation_metadata.overall_confidence",
            "participant_profile.profile_confidence", 
            "narrative_features.narrative_confidence"
        ]
        
        for field_path in confidence_fields:
            parts = field_path.split('.')
            value = annotation_data
            try:
                for part in parts:
                    value = value[part]
                if not isinstance(value, (int, float)) or value < 0 or value > 1:
                    has_confidence_scores = False
                    break
            except (KeyError, TypeError):
                has_confidence_scores = False
                break
        
        quality_report["dimension_scores"]["confidence_tracking"] = 1.0 if has_confidence_scores else 0.0
        
        # Check turn analysis depth
        turns = annotation_data["conversation_analysis"]["turns"]
        turn_depth_score = 0.0
        
        if turns:
            required_turn_fields = ["turn_analysis", "content_analysis", "evidence_analysis", 
                                   "emotional_analysis", "uncertainty_tracking"]
            
            complete_turns = 0
            for turn in turns:
                if all(field in turn for field in required_turn_fields):
                    complete_turns += 1
            
            turn_depth_score = complete_turns / len(turns)
        
        quality_report["dimension_scores"]["turn_analysis_depth"] = turn_depth_score
        
        # Calculate overall score
        scores = list(quality_report["dimension_scores"].values())
        quality_report["overall_score"] = sum(scores) / len(scores) if scores else 0.0
        
        # Generate recommendations
        if quote_completeness < 0.8:
            quality_report["recommendations"].append("Increase authentic quote extraction")
        
        if not has_confidence_scores:
            quality_report["recommendations"].append("Improve confidence score tracking")
        
        if turn_depth_score < 0.9:
            quality_report["recommendations"].append("Enhance turn-level analysis completeness")
        
        return quality_report


def main():
    """Test the enhanced JSON annotator."""
    # Find test interview
    txt_dir = Path("data/processed/interviews_txt")
    txt_files = list(txt_dir.glob("*.txt"))
    
    if not txt_files:
        print("❌ No interview files found")
        return
    
    # Use a medium-sized file for testing
    test_files = sorted(txt_files, key=lambda f: f.stat().st_size)
    test_file = test_files[len(test_files)//2]  # Use middle-sized file
    
    # Process interview
    from src.pipeline.ingestion.document_processor import DocumentProcessor
    processor = DocumentProcessor()
    interview = processor.process_interview(test_file)
    
    print(f"🎯 ENHANCED JSON MODE ANNOTATION TEST")
    print(f"Interview: {interview.id}")
    print(f"Word count: {len(interview.text.split()):,}")
    print(f"Estimated cost: ~$0.002-0.005 (GPT-4.1 nano)")
    print()
    
    # Create enhanced annotator
    annotator = EnhancedJSONAnnotator()
    
    try:
        print("🤖 Making enhanced JSON mode API call...")
        annotation_data, metadata = annotator.annotate_interview(interview)
        
        print("✅ Enhanced JSON annotation successful!")
        print()
        print("📊 RESULTS:")
        print(f"  Turns analyzed: {len(annotation_data['conversation_analysis']['turns'])}")
        print(f"  National priorities: {len(annotation_data['priority_analysis']['national_priorities'])}")
        print(f"  Local priorities: {len(annotation_data['priority_analysis']['local_priorities'])}")
        print(f"  Overall confidence: {annotation_data['annotation_metadata']['overall_confidence']}")
        print(f"  Processing time: {metadata['processing_time']:.1f}s")
        print(f"  Actual cost: ${metadata['estimated_cost']:.4f}")
        print(f"  Prompt tokens: {metadata['prompt_tokens']:,}")
        print(f"  Completion tokens: {metadata['completion_tokens']:,}")
        
        # Validate quality
        print(f"\n🔍 QUALITY VALIDATION:")
        quality_report = annotator.validate_annotation_quality(annotation_data)
        print(f"  Overall quality score: {quality_report['overall_score']:.2f}")
        
        for dimension, score in quality_report['dimension_scores'].items():
            print(f"  {dimension}: {score:.2f}")
        
        if quality_report['recommendations']:
            print(f"  Recommendations: {', '.join(quality_report['recommendations'])}")
        
        # Save result
        output_file = f"enhanced_annotation_{interview.id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "annotation_data": annotation_data,
                "processing_metadata": metadata,
                "quality_report": quality_report
            }, f, indent=2, ensure_ascii=False)
        
        print(f"  Saved to: {output_file}")
        
        # Show sample priority
        national_p1 = annotation_data['priority_analysis']['national_priorities'][0]
        print(f"\n📋 SAMPLE PRIORITY ANALYSIS:")
        print(f"  Theme: {national_p1['theme']}")
        print(f"  Confidence: {national_p1['confidence']}")
        if national_p1.get('supporting_quotes'):
            print(f"  Quote: \"{national_p1['supporting_quotes'][0][:100]}...\"")
        
    except Exception as e:
        print(f"❌ Enhanced annotation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path.cwd()))
    main()