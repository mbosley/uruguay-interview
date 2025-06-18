#!/usr/bin/env python3
"""Test complete interview annotation with full dynamic schema."""
import sys
from pathlib import Path
import json
from openai import OpenAI
import time

# Add project root to path
sys.path.insert(0, str(Path.cwd()))

from src.pipeline.ingestion.document_processor import DocumentProcessor
from src.config.config_loader import ConfigLoader

def analyze_interview_for_schema(interview):
    """Analyze interview to create optimal schema."""
    
    lines = interview.text.split('\n')
    
    # Count actual conversation turns
    turn_patterns = [
        'Entrevistador:', 'Entrevistadora:', 'Gabriela Medina', 'Germán Busch',
        '[GM]', '[GB]', 'GM:', 'GB:', 'María Rosales', 'Marcelo Rosales', 
        '[MR]', '[MR2]', 'MR:', 'MR2:', 'Participante:', 'P:'
    ]
    
    turns = []
    current_speaker = None
    current_text = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check for speaker change
        new_speaker = None
        content = line
        
        for pattern in turn_patterns:
            if line.startswith(pattern):
                if 'GM' in pattern or 'GB' in pattern or 'Entrevistador' in pattern:
                    new_speaker = 'interviewer'
                else:
                    new_speaker = 'participant'
                
                if ':' in line:
                    content = line.split(':', 1)[1].strip()
                elif ']' in line and line.startswith('['):
                    content = line.split(']', 1)[1].strip()
                break
        
        if new_speaker and new_speaker != current_speaker:
            # Save previous turn
            if current_speaker and current_text:
                turns.append({
                    'speaker': current_speaker,
                    'text': ' '.join(current_text).strip()
                })
            
            # Start new turn
            current_speaker = new_speaker
            current_text = [content] if content else []
        elif current_speaker and line:
            current_text.append(line)
    
    # Add final turn
    if current_speaker and current_text:
        turns.append({
            'speaker': current_speaker,
            'text': ' '.join(current_text).strip()
        })
    
    word_count = len(interview.text.split())
    
    # Detect themes
    text_lower = interview.text.lower()
    themes = {
        'salud': any(word in text_lower for word in ['salud', 'medicina', 'médico', 'hospital', 'medicamento']),
        'educacion': any(word in text_lower for word in ['educación', 'escuela', 'liceo', 'estudio', 'enseñanza']),
        'seguridad': any(word in text_lower for word in ['seguridad', 'robo', 'delincuencia', 'policía', 'crimen']),
        'economia': any(word in text_lower for word in ['trabajo', 'empleo', 'economía', 'plata', 'sueldo']),
        'infraestructura': any(word in text_lower for word in ['calle', 'ruta', 'transporte', 'ómnibus', 'luz']),
        'vivienda': any(word in text_lower for word in ['vivienda', 'casa', 'hogar', 'alquiler']),
        'juventud': any(word in text_lower for word in ['joven', 'juventud', 'adolescente', 'chiquilín'])
    }
    
    detected_themes = [theme for theme, present in themes.items() if present]
    
    return {
        'turn_count': len(turns),
        'turns': turns,
        'word_count': word_count,
        'detected_themes': detected_themes,
        'complexity_score': len(detected_themes) + (len(turns) / 10) + (word_count / 1000)
    }

def create_comprehensive_schema(interview, analysis):
    """Create a comprehensive schema for complete annotation."""
    
    schema = {
        "interview_metadata": {
            "interview_id": interview.id,
            "date": interview.date,
            "location": interview.location,
            "department": interview.department,
            "participant_count": "single|multiple",
            "participant_age": "18-29|30-49|50-64|65+",
            "participant_gender": "male|female|multiple|unclear",
            "municipality": "string",
            "locality_type": "rural|small_town|medium_city|large_city",
            "interview_duration": "short|medium|long",
            "word_count": analysis['word_count'],
            "conversation_turns": analysis['turn_count']
        },
        
        "participant_profile": {
            "age_assessment": "string with reasoning",
            "gender_assessment": "string with reasoning", 
            "occupation_mentioned": "string or null",
            "education_level_inferred": "string or null",
            "family_situation_mentioned": "string or null",
            "community_involvement": "string or null",
            "political_engagement": "high|medium|low|unclear"
        },
        
        "national_priorities": [
            {
                "rank": 1,
                "theme": "string",
                "specific_issues": ["string", "string"],
                "participant_reasoning": "how participant explained this priority",
                "supporting_quotes": ["direct quote 1", "direct quote 2"],
                "emotional_intensity": "high|medium|low",
                "certainty_level": "very_certain|certain|somewhat_uncertain|uncertain",
                "solution_orientation": "problem_focused|solution_focused|balanced"
            },
            {
                "rank": 2,
                "theme": "string",
                "specific_issues": ["string", "string"],
                "participant_reasoning": "how participant explained this priority",
                "supporting_quotes": ["direct quote 1", "direct quote 2"],
                "emotional_intensity": "high|medium|low",
                "certainty_level": "very_certain|certain|somewhat_uncertain|uncertain",
                "solution_orientation": "problem_focused|solution_focused|balanced"
            },
            {
                "rank": 3,
                "theme": "string",
                "specific_issues": ["string", "string"],
                "participant_reasoning": "how participant explained this priority",
                "supporting_quotes": ["direct quote 1", "direct quote 2"],
                "emotional_intensity": "high|medium|low",
                "certainty_level": "very_certain|certain|somewhat_uncertain|uncertain",
                "solution_orientation": "problem_focused|solution_focused|balanced"
            }
        ],
        
        "local_priorities": [
            {
                "rank": 1,
                "theme": "string",
                "specific_issues": ["string", "string"],
                "participant_reasoning": "how participant explained this priority",
                "supporting_quotes": ["direct quote 1", "direct quote 2"],
                "geographic_scope": "neighborhood|city|department|region",
                "personal_experience": "yes|no|unclear",
                "proposed_solutions": ["string"] 
            },
            {
                "rank": 2,
                "theme": "string",
                "specific_issues": ["string", "string"],
                "participant_reasoning": "how participant explained this priority",
                "supporting_quotes": ["direct quote 1", "direct quote 2"],
                "geographic_scope": "neighborhood|city|department|region",
                "personal_experience": "yes|no|unclear",
                "proposed_solutions": ["string"]
            },
            {
                "rank": 3,
                "theme": "string",
                "specific_issues": ["string", "string"],
                "participant_reasoning": "how participant explained this priority",
                "supporting_quotes": ["direct quote 1", "direct quote 2"],
                "geographic_scope": "neighborhood|city|department|region",
                "personal_experience": "yes|no|unclear",
                "proposed_solutions": ["string"]
            }
        ]
    }
    
    # Add theme-specific analysis
    if analysis['detected_themes']:
        schema["thematic_analysis"] = {}
        
        for theme in analysis['detected_themes']:
            schema["thematic_analysis"][f"{theme}_analysis"] = {
                "prominence_level": "central|important|mentioned|peripheral",
                "participant_perspective": "string describing viewpoint",
                "personal_connection": "direct_experience|indirect_experience|general_concern|no_connection",
                "specific_examples": ["string"],
                "proposed_solutions": ["string"],
                "emotional_tone": "very_positive|positive|neutral|negative|very_negative",
                "key_quotes": ["quote1", "quote2"]
            }
    
    # Add conversation analysis based on turn count
    if analysis['turn_count'] <= 30:
        schema["detailed_conversation_analysis"] = {
            "turn_by_turn": [
                {
                    "turn_number": "integer",
                    "speaker": "interviewer|participant",
                    "text_preview": "first 100 characters",
                    "primary_function": "question|answer|elaboration|clarification|problem_identification|solution_proposal|personal_story|evaluation",
                    "topics_discussed": ["string"],
                    "emotional_markers": ["string"],
                    "evidence_type": "personal_experience|hearsay|media|official_data|general_knowledge|none",
                    "reasoning": "analytical reasoning for classifications"
                }
            ]
        }
    else:
        schema["conversation_summary"] = {
            "total_turns": analysis['turn_count'],
            "conversation_phases": [
                {
                    "phase_name": "string",
                    "turn_range": "string like '1-15'",
                    "main_topics": ["string"],
                    "key_insights": ["string"],
                    "participant_engagement": "high|medium|low"
                }
            ],
            "most_revealing_exchanges": [
                {
                    "turn_numbers": "string",
                    "topic": "string",
                    "significance": "string",
                    "key_quotes": ["string"]
                }
            ]
        }
    
    # Add narrative and interpretive analysis
    schema["narrative_analysis"] = {
        "dominant_interpretive_frame": "string describing how participant makes sense of issues",
        "temporal_orientation": "past_focused|present_focused|future_focused|mixed",
        "agency_attribution": {
            "government_responsibility": "string",
            "individual_responsibility": "string", 
            "community_responsibility": "string",
            "structural_factors": "string"
        },
        "solution_approach": "government_action|individual_action|community_action|systemic_change|mixed",
        "emotional_journey": "string describing emotional arc of interview",
        "identity_presentation": "string describing how participant presents themselves",
        "cultural_references": ["uruguayan cultural elements mentioned"],
        "implicit_assumptions": ["unstated assumptions participant makes"]
    }
    
    schema["memorable_content"] = {
        "most_powerful_quotes": ["quote1", "quote2", "quote3"],
        "most_revealing_moments": ["description of significant moments"],
        "surprising_insights": ["unexpected perspectives or information"],
        "contradictions_or_tensions": ["internal contradictions in discourse"],
        "silence_or_avoidance": ["topics avoided or not discussed"]
    }
    
    schema["interview_quality_assessment"] = {
        "rapport_quality": "excellent|good|adequate|poor",
        "participant_openness": "very_open|open|somewhat_guarded|guarded",
        "response_depth": "very_detailed|detailed|moderate|superficial",
        "coherence": "highly_coherent|coherent|somewhat_scattered|incoherent",
        "interviewer_effectiveness": "excellent|good|adequate|poor",
        "overall_data_quality": "excellent|good|adequate|poor"
    }
    
    schema["annotation_confidence"] = {
        "overall_confidence": 0.85,
        "priority_identification_confidence": 0.9,
        "thematic_analysis_confidence": 0.8,
        "narrative_interpretation_confidence": 0.75,
        "areas_of_uncertainty": ["specific uncertainties"],
        "recommendations_for_follow_up": ["suggestions for additional analysis"]
    }
    
    return schema

def test_full_interview():
    """Test complete interview annotation."""
    
    # Find a representative interview
    txt_dir = Path("data/processed/interviews_txt")
    txt_files = list(txt_dir.glob("*.txt"))
    
    if not txt_files:
        print("❌ No interview files found")
        return
    
    # Use a medium-sized interview for comprehensive testing
    processor = DocumentProcessor()
    interviews_with_size = []
    
    for txt_file in txt_files[:10]:  # Test first 10 to find good candidate
        interview = processor.process_interview(txt_file)
        word_count = len(interview.text.split())
        interviews_with_size.append((interview, word_count, txt_file))
    
    # Sort by size and pick middle one
    interviews_with_size.sort(key=lambda x: x[1])
    interview, word_count, txt_file = interviews_with_size[len(interviews_with_size)//2]
    
    print("🎯 FULL INTERVIEW ANNOTATION TEST")
    print("=" * 50)
    print(f"Interview: {interview.id}")
    print(f"File: {txt_file.name}")
    print(f"Word count: {word_count:,}")
    print(f"Character count: {len(interview.text):,}")
    print()
    
    # Analyze interview characteristics
    print("📊 Analyzing interview characteristics...")
    analysis = analyze_interview_for_schema(interview)
    
    print(f"Detected conversation turns: {analysis['turn_count']}")
    print(f"Detected themes: {', '.join(analysis['detected_themes'])}")
    print(f"Complexity score: {analysis['complexity_score']:.1f}")
    print()
    
    # Generate comprehensive schema
    print("🏗️ Generating comprehensive schema...")
    schema = create_comprehensive_schema(interview, analysis)
    schema_size = len(json.dumps(schema, indent=2))
    
    print(f"Schema size: {schema_size:,} characters")
    print(f"Estimated schema fields: {len(json.dumps(schema).split(','))}")
    print()
    
    # Create the annotation prompt
    schema_json = json.dumps(schema, indent=2)
    
    prompt = f"""
You are an expert qualitative researcher analyzing a citizen consultation interview from Uruguay.

COMPLETE INTERVIEW TEXT:
{interview.text}

INTERVIEW CONTEXT:
- ID: {interview.id}
- Date: {interview.date}
- Location: {interview.location}, {interview.department}
- Detected themes: {', '.join(analysis['detected_themes'])}
- Conversation turns: {analysis['turn_count']}

Provide a comprehensive systematic analysis following this EXACT JSON structure:

{schema_json}

CRITICAL INSTRUCTIONS:
1. Analyze the COMPLETE interview text thoroughly
2. Extract priorities with precise supporting quotes in participant's own words
3. Provide detailed reasoning for all analytical decisions
4. Fill every field in the schema with meaningful content
5. Use "string" placeholders to indicate the type of content expected
6. Ensure all quotes are accurate and properly attributed
7. Be thorough but precise in your analysis
8. Return ONLY valid JSON - no other text

This is a comprehensive annotation - take time to analyze deeply and systematically.
"""
    
    # Get API client
    config_loader = ConfigLoader()
    api_key = config_loader.get_api_key("openai")
    client = OpenAI(api_key=api_key)
    
    print("🤖 Making comprehensive annotation API call...")
    print("⏳ This may take 30-60 seconds due to comprehensive analysis...")
    
    start_time = time.time()
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert qualitative researcher. Provide comprehensive, systematic analysis. Return valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        processing_time = time.time() - start_time
        
        # Parse result
        result = json.loads(response.choices[0].message.content)
        
        print("✅ COMPREHENSIVE ANNOTATION SUCCESS!")
        print(f"Processing time: {processing_time:.1f} seconds")
        print()
        
        # Display key results
        print("📊 ANNOTATION RESULTS SUMMARY:")
        print("=" * 40)
        
        meta = result["interview_metadata"]
        print("📋 INTERVIEW METADATA:")
        for key, value in meta.items():
            print(f"  {key}: {value}")
        print()
        
        print("🎯 NATIONAL PRIORITIES (with full analysis):")
        for i, priority in enumerate(result["national_priorities"], 1):
            print(f"  {priority['rank']}. {priority['theme']}")
            print(f"     Issues: {', '.join(priority['specific_issues'])}")
            print(f"     Reasoning: {priority['participant_reasoning'][:100]}...")
            print(f"     Quotes: {len(priority['supporting_quotes'])} supporting quotes")
            print(f"     Emotion: {priority['emotional_intensity']}, Certainty: {priority['certainty_level']}")
            print()
        
        print("🏠 LOCAL PRIORITIES (with full analysis):")
        for i, priority in enumerate(result["local_priorities"], 1):
            print(f"  {priority['rank']}. {priority['theme']}")
            print(f"     Issues: {', '.join(priority['specific_issues'])}")
            print(f"     Scope: {priority['geographic_scope']}")
            print(f"     Personal experience: {priority['personal_experience']}")
            print(f"     Solutions proposed: {len(priority['proposed_solutions'])}")
            print()
        
        # Show thematic analysis if present
        if "thematic_analysis" in result:
            print("🎨 THEMATIC ANALYSIS:")
            for theme, analysis in result["thematic_analysis"].items():
                print(f"  {theme}: {analysis['prominence_level']} prominence")
                print(f"    Perspective: {analysis['participant_perspective'][:80]}...")
                print(f"    Connection: {analysis['personal_connection']}")
                print()
        
        # Show narrative analysis
        narrative = result["narrative_analysis"]
        print("📖 NARRATIVE ANALYSIS:")
        print(f"  Interpretive frame: {narrative['dominant_interpretive_frame'][:100]}...")
        print(f"  Temporal focus: {narrative['temporal_orientation']}")
        print(f"  Solution approach: {narrative['solution_approach']}")
        print()
        
        # Show quality assessment
        quality = result["interview_quality_assessment"]
        print("⭐ INTERVIEW QUALITY:")
        for key, value in quality.items():
            print(f"  {key}: {value}")
        print()
        
        # Show confidence
        confidence = result["annotation_confidence"]
        print("🤔 CONFIDENCE ASSESSMENT:")
        print(f"  Overall confidence: {confidence['overall_confidence']}")
        print(f"  Priority identification: {confidence['priority_identification_confidence']}")
        print(f"  Uncertainties: {len(confidence['areas_of_uncertainty'])} areas")
        print()
        
        # Cost analysis
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        total_tokens = prompt_tokens + completion_tokens
        cost = (prompt_tokens / 1_000_000) * 0.15 + (completion_tokens / 1_000_000) * 0.60
        
        print("💰 COST ANALYSIS:")
        print(f"  Prompt tokens: {prompt_tokens:,}")
        print(f"  Completion tokens: {completion_tokens:,}")
        print(f"  Total tokens: {total_tokens:,}")
        print(f"  Cost: ${cost:.4f}")
        print(f"  37 interviews: ${cost * 37:.2f}")
        print()
        
        # Save comprehensive result
        output_file = f"full_interview_annotation_{interview.id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'interview_metadata': {
                    'id': interview.id,
                    'word_count': word_count,
                    'processing_time': processing_time,
                    'cost': cost,
                    'token_usage': {
                        'prompt': prompt_tokens,
                        'completion': completion_tokens,
                        'total': total_tokens
                    }
                },
                'analysis_characteristics': analysis,
                'schema_used': schema,
                'annotation_result': result
            }, f, indent=2, ensure_ascii=False)
        
        print(f"💾 COMPREHENSIVE RESULT SAVED:")
        print(f"  File: {output_file}")
        print(f"  Size: {Path(output_file).stat().st_size:,} bytes")
        print()
        
        print("🎉 FULL INTERVIEW ANNOTATION SUCCESS!")
        print("  ✅ Complete interview processed")
        print("  ✅ Comprehensive multi-dimensional analysis")
        print("  ✅ Dynamic schema with theme-specific sections")
        print("  ✅ Detailed priority extraction with reasoning")
        print("  ✅ Narrative and quality assessment")
        print("  ✅ Confidence scoring and uncertainty tracking")
        print(f"  ✅ Cost-effective: ${cost:.4f} for comprehensive analysis")
        print(f"  ✅ Ready for production scaling")
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing failed: {e}")
        print("Response was not valid JSON")
        
    except Exception as e:
        print(f"❌ Comprehensive annotation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_full_interview()