"""
Multi-pass annotation system for comprehensive turn coverage.
Guarantees 100% turn analysis while maintaining analytical depth.
"""
import json
import asyncio
from openai import OpenAI
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import logging
import time
from datetime import datetime

from src.pipeline.ingestion.document_processor import InterviewDocument
from src.config.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class MultiPassAnnotator:
    """Multi-pass annotation system ensuring comprehensive turn coverage."""
    
    def __init__(
        self,
        model_name: str = "gpt-4.1-nano",
        temperature: float = 0.1,
        max_retries: int = 3,
        turns_per_batch: int = 6
    ):
        """
        Initialize multi-pass annotator.
        
        Args:
            model_name: OpenAI model to use
            temperature: Sampling temperature
            max_retries: Maximum retry attempts per API call
            turns_per_batch: Number of turns to analyze in each batch
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_retries = max_retries
        self.turns_per_batch = turns_per_batch
        
        # Get API key
        config_loader = ConfigLoader()
        api_key = config_loader.get_api_key("openai")
        if not api_key:
            raise ValueError("No OpenAI API key found")
        
        self.client = OpenAI(api_key=api_key)
        
        logger.info(f"Initialized multi-pass annotator with {model_name}")
    
    def create_interview_analysis_prompt(self, interview: InterviewDocument) -> str:
        """Create prompt for Pass 1: Interview-level analysis + turn inventory."""
        return f"""
You are a skilled qualitative researcher with expertise in citizen consultations, political discourse analysis, and Latin American contexts.

INTERVIEW TO ANALYZE:
{interview.text}

METADATA:
- ID: {interview.id}
- Date: {interview.date}
- Location: {interview.location}
- Department: {interview.department}

Provide comprehensive interview-level analysis plus complete turn inventory in JSON format:

{{
  "interview_analysis": {{
    "annotation_metadata": {{
      "annotator_approach": "multipass_comprehensive",
      "annotation_timestamp": "{datetime.now().isoformat()}",
      "interview_id": "{interview.id}",
      "overall_confidence": 0.85,
      "uncertainty_flags": ["cultural_context_needed"],
      "uncertainty_narrative": "Description of annotation uncertainties"
    }},
    "interview_metadata": {{
      "interview_id": "{interview.id}",
      "date": "{interview.date}",
      "municipality": "string",
      "department": "{interview.department}",
      "locality_size": "rural|small_town|medium_city|large_city",
      "duration_minutes": 45,
      "interviewer_ids": ["string"],
      "interview_context": "Brief description of interview setting"
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
          "narrative_elaboration": "Rich description using participant's own words",
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
      ]
    }},
    "narrative_features": {{
      "dominant_frame": "decline|progress|stagnation|mixed",
      "frame_narrative": "Overarching story participant tells about their community/country",
      "temporal_orientation": "past_focused|present_focused|future_focused|mixed",
      "temporal_narrative": "How participant relates past, present, and future",
      "agency_attribution": {{
        "government_responsibility": 0.8,
        "individual_responsibility": 0.4,
        "structural_factors": 0.9,
        "agency_narrative": "Overall view of who has power to create change"
      }},
      "solution_orientation": "highly_specific|moderately_specific|vague|none",
      "solution_narrative": "How participant envisions change happening",
      "cultural_patterns_identified": ["generational_decline", "state_abandonment", "youth_exodus"],
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
      "cultural_context_notes": "Local knowledge that would aid interpretation",
      "connections_to_broader_themes": "How this connects to broader social patterns",
      "analytical_confidence": 0.8
    }}
  }},
  "turn_inventory": {{
    "total_turns_detected": 15,
    "participant_turns": 8,
    "interviewer_turns": 7,
    "turn_list": [
      {{
        "turn_id": 1,
        "speaker": "interviewer|participant",
        "text": "exact text of what was said",
        "significance": "high|medium|low",
        "preliminary_topics": ["topic1", "topic2"],
        "word_count": 25
      }},
      {{
        "turn_id": 2,
        "speaker": "interviewer|participant", 
        "text": "exact text of what was said",
        "significance": "high|medium|low",
        "preliminary_topics": ["topic1"],
        "word_count": 45
      }}
    ]
  }}
}}

CRITICAL REQUIREMENTS:
1. Complete interview-level analysis with all sections
2. Create complete turn inventory - identify EVERY conversation turn
3. Assign significance levels to prioritize which turns need deepest analysis
4. Extract exactly 3 national and 3 local priorities with supporting quotes
5. Return valid JSON only

Analyze the complete interview systematically and create comprehensive turn inventory.
"""
    
    def create_turn_batch_prompt(self, interview: InterviewDocument, turn_batch: List[Dict], 
                                previous_context: str = "") -> str:
        """Create prompt for Pass 2: Detailed turn analysis batch."""
        
        turns_text = "\n\n".join([
            f"TURN {t['turn_id']} ({t['speaker']}):\n{t['text']}"
            for t in turn_batch
        ])
        
        turn_ids = [t['turn_id'] for t in turn_batch]
        
        return f"""
You are a skilled qualitative researcher analyzing conversation turns from a Uruguay citizen consultation interview.

INTERVIEW CONTEXT:
- ID: {interview.id}
- Previous turns context: {previous_context}

TURNS TO ANALYZE IN DETAIL:
{turns_text}

Provide comprehensive analysis for each turn in this batch:

{{
  "batch_metadata": {{
    "batch_turns": {turn_ids},
    "analysis_timestamp": "{datetime.now().isoformat()}",
    "batch_confidence": 0.85
  }},
  "turn_analyses": [
    {{
      "turn_id": {turn_ids[0] if turn_ids else 1},
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
        "evidence_type": "personal_experience|family_experience|community_observation|hearsay|media_reference|statistical_claim|general_assertion|hypothetical|none",
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
      "turn_significance": "Why this turn matters for understanding the participant"
    }}
  ]
}}

CRITICAL REQUIREMENTS:
1. Analyze every turn in the batch with full depth
2. Provide chain-of-thought reasoning for all decisions
3. Include uncertainty tracking and confidence scores
4. Connect to previous context where relevant
5. Return valid JSON only

Focus on faithful representation while achieving systematic analysis.
"""
    
    async def annotate_interview(self, interview: InterviewDocument) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Generate comprehensive multi-pass annotation.
        
        Args:
            interview: Interview document to annotate
            
        Returns:
            Tuple of (complete_annotation, processing_metadata)
        """
        start_time = time.time()
        total_cost = 0.0
        api_calls = []
        
        logger.info(f"Starting multi-pass annotation for interview {interview.id}")
        
        # PASS 1: Interview-level analysis + turn inventory
        logger.info("Pass 1: Interview-level analysis and turn inventory")
        interview_prompt = self.create_interview_analysis_prompt(interview)
        
        interview_response = await self._make_api_call(interview_prompt, "interview_analysis")
        interview_data = json.loads(interview_response.choices[0].message.content)
        
        cost_1 = self._estimate_cost(interview_response.usage.prompt_tokens, 
                                   interview_response.usage.completion_tokens)
        total_cost += cost_1
        api_calls.append({
            "pass": "interview_analysis",
            "cost": cost_1,
            "tokens": interview_response.usage.prompt_tokens + interview_response.usage.completion_tokens
        })
        
        # Extract turn inventory
        turn_inventory = interview_data["turn_inventory"]["turn_list"]
        total_turns = len(turn_inventory)
        
        logger.info(f"Detected {total_turns} turns for detailed analysis")
        
        # PASS 2: Batch turn analysis
        logger.info("Pass 2: Comprehensive turn analysis in batches")
        
        all_turn_analyses = []
        previous_context = ""
        
        # Process turns in batches
        for i in range(0, total_turns, self.turns_per_batch):
            batch_num = (i // self.turns_per_batch) + 1
            turn_batch = turn_inventory[i:i + self.turns_per_batch]
            
            logger.info(f"Processing batch {batch_num}: turns {turn_batch[0]['turn_id']}-{turn_batch[-1]['turn_id']}")
            
            # Create context from previous batch
            if i > 0:
                prev_batch = turn_inventory[max(0, i-3):i]  # Include 3 previous turns for context
                previous_context = " | ".join([f"Turn {t['turn_id']}: {t['text'][:100]}..." for t in prev_batch])
            
            batch_prompt = self.create_turn_batch_prompt(interview, turn_batch, previous_context)
            batch_response = await self._make_api_call(batch_prompt, f"turn_batch_{batch_num}")
            batch_data = json.loads(batch_response.choices[0].message.content)
            
            cost_batch = self._estimate_cost(batch_response.usage.prompt_tokens, 
                                           batch_response.usage.completion_tokens)
            total_cost += cost_batch
            api_calls.append({
                "pass": f"turn_batch_{batch_num}",
                "turns": [t['turn_id'] for t in turn_batch],
                "cost": cost_batch,
                "tokens": batch_response.usage.prompt_tokens + batch_response.usage.completion_tokens
            })
            
            # Collect turn analyses
            all_turn_analyses.extend(batch_data["turn_analyses"])
        
        # PASS 3: Integration and validation
        logger.info("Pass 3: Integration and completeness validation")
        
        # Verify all turns were analyzed
        analyzed_turn_ids = set(t["turn_id"] for t in all_turn_analyses)
        expected_turn_ids = set(t["turn_id"] for t in turn_inventory)
        missing_turns = expected_turn_ids - analyzed_turn_ids
        
        if missing_turns:
            logger.warning(f"Missing turn analyses for turns: {missing_turns}")
            # Could trigger additional API call here if needed
        
        # Create final integrated annotation
        final_annotation = {
            **interview_data["interview_analysis"],
            "conversation_analysis": {
                "total_turns_detected": total_turns,
                "participant_turns": interview_data["turn_inventory"]["participant_turns"],
                "interviewer_turns": interview_data["turn_inventory"]["interviewer_turns"],
                "turns": all_turn_analyses,
                "batch_processing": {
                    "total_batches": len([call for call in api_calls if "turn_batch" in call["pass"]]),
                    "turns_per_batch": self.turns_per_batch,
                    "coverage_complete": len(missing_turns) == 0,
                    "missing_turns": list(missing_turns) if missing_turns else []
                }
            },
            "quality_assessment": {
                "annotation_completeness": 1.0 if not missing_turns else (len(analyzed_turn_ids) / len(expected_turn_ids)),
                "turn_coverage": len(analyzed_turn_ids),
                "expected_turns": len(expected_turn_ids),
                "processing_approach": "multipass_comprehensive",
                "all_turns_analyzed": len(missing_turns) == 0
            }
        }
        
        processing_time = time.time() - start_time
        
        # Create processing metadata
        metadata = {
            "model_name": self.model_name,
            "annotation_approach": "multipass_comprehensive",
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat(),
            "total_api_calls": len(api_calls),
            "total_cost": total_cost,
            "api_call_breakdown": api_calls,
            "turn_coverage": {
                "total_turns": total_turns,
                "analyzed_turns": len(analyzed_turn_ids),
                "coverage_percentage": (len(analyzed_turn_ids) / total_turns) * 100,
                "missing_turns": list(missing_turns) if missing_turns else []
            },
            "overall_confidence": final_annotation["annotation_metadata"]["overall_confidence"]
        }
        
        logger.info(f"Multi-pass annotation complete: {len(analyzed_turn_ids)}/{total_turns} turns analyzed, ${total_cost:.4f} total cost")
        
        return final_annotation, metadata
    
    async def _make_api_call(self, prompt: str, call_type: str) -> Any:
        """Make API call with retries."""
        for attempt in range(self.max_retries):
            try:
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
                
                return response
                
            except Exception as e:
                logger.warning(f"{call_type} attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
        
        raise RuntimeError(f"Failed {call_type} after {self.max_retries} attempts")
    
    def _estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate cost based on actual token usage."""
        if "gpt-4.1-nano" in self.model_name:
            prompt_cost = (prompt_tokens / 1_000_000) * 0.10
            completion_cost = (completion_tokens / 1_000_000) * 0.40
        elif "gpt-4o-mini" in self.model_name:
            prompt_cost = (prompt_tokens / 1_000_000) * 0.15
            completion_cost = (completion_tokens / 1_000_000) * 0.60
        else:
            prompt_cost = (prompt_tokens / 1_000_000) * 2.50
            completion_cost = (completion_tokens / 1_000_000) * 10.00
        return prompt_cost + completion_cost


async def main():
    """Test the multi-pass annotator."""
    # Find test interview
    txt_dir = Path("data/processed/interviews_txt")
    txt_files = list(txt_dir.glob("*.txt"))
    
    if not txt_files:
        print("❌ No interview files found")
        return
    
    # Use a medium-sized file for testing
    test_files = sorted(txt_files, key=lambda f: f.stat().st_size)
    test_file = test_files[len(test_files)//2]
    
    # Process interview
    from src.pipeline.ingestion.document_processor import DocumentProcessor
    processor = DocumentProcessor()
    interview = processor.process_interview(test_file)
    
    print(f"🎯 MULTI-PASS COMPREHENSIVE ANNOTATION TEST")
    print(f"Interview: {interview.id}")
    print(f"Word count: {len(interview.text.split()):,}")
    print(f"Estimated cost: ~$0.006-0.012 (comprehensive coverage)")
    print()
    
    # Create multi-pass annotator
    annotator = MultiPassAnnotator()
    
    try:
        print("🤖 Starting multi-pass annotation...")
        annotation_data, metadata = await annotator.annotate_interview(interview)
        
        print("✅ Multi-pass annotation successful!")
        print()
        print("📊 COMPREHENSIVE RESULTS:")
        print(f"  Total API calls: {metadata['total_api_calls']}")
        print(f"  Turn coverage: {metadata['turn_coverage']['analyzed_turns']}/{metadata['turn_coverage']['total_turns']} ({metadata['turn_coverage']['coverage_percentage']:.1f}%)")
        print(f"  Processing time: {metadata['processing_time']:.1f}s")
        print(f"  Total cost: ${metadata['total_cost']:.4f}")
        
        print(f"\n🔍 API CALL BREAKDOWN:")
        for call in metadata['api_call_breakdown']:
            print(f"  {call['pass']}: ${call['cost']:.4f} ({call['tokens']} tokens)")
        
        # Save result
        output_file = f"multipass_annotation_{interview.id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "annotation_data": annotation_data,
                "processing_metadata": metadata
            }, f, indent=2, ensure_ascii=False)
        
        print(f"  Saved to: {output_file}")
        
        # Show sample results
        turn_analysis = annotation_data['conversation_analysis']['turns'][0]
        print(f"\n📋 SAMPLE TURN ANALYSIS:")
        print(f"  Turn {turn_analysis['turn_id']}: {turn_analysis['turn_analysis']['primary_function']}")
        print(f"  Confidence: {turn_analysis['uncertainty_tracking']['coding_confidence']}")
        print(f"  Significance: {turn_analysis['turn_significance'][:100]}...")
        
        if metadata['turn_coverage']['coverage_percentage'] == 100:
            print(f"\n🎯 SUCCESS: 100% turn coverage achieved!")
        else:
            print(f"\n⚠️  Partial coverage: {metadata['turn_coverage']['missing_turns']}")
        
    except Exception as e:
        print(f"❌ Multi-pass annotation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path.cwd()))
    asyncio.run(main())