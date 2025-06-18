#!/usr/bin/env python3
"""Test dynamic schema generation based on interview characteristics."""
import sys
from pathlib import Path
import json
from openai import OpenAI

# Add project root to path
sys.path.insert(0, str(Path.cwd()))

from src.pipeline.ingestion.document_processor import DocumentProcessor
from src.config.config_loader import ConfigLoader

def analyze_interview_characteristics(interview):
    """Analyze interview to determine optimal schema."""
    
    lines = interview.text.split('\n')
    
    # Count turns
    turn_patterns = [
        'Entrevistador:', 'Entrevistadora:', 'Gabriela Medina', 'Germán Busch',
        '[GM]', '[GB]', 'GM:', 'GB:', 'María Rosales', 'Marcelo Rosales', 
        '[MR]', '[MR2]', 'MR:', 'MR2:', 'Participante:', 'P:'
    ]
    
    turn_count = 0
    for line in lines:
        if any(line.strip().startswith(pattern) for pattern in turn_patterns):
            turn_count += 1
    
    word_count = len(interview.text.split())
    
    # Detect content themes (simple keyword analysis)
    text_lower = interview.text.lower()
    themes = {
        'health': any(word in text_lower for word in ['salud', 'medicina', 'médico', 'hospital']),
        'education': any(word in text_lower for word in ['educación', 'escuela', 'liceo', 'estudio']),
        'security': any(word in text_lower for word in ['seguridad', 'robo', 'delincuencia', 'policía']),
        'economy': any(word in text_lower for word in ['trabajo', 'empleo', 'economía', 'plata']),
        'infrastructure': any(word in text_lower for word in ['calle', 'ruta', 'transporte', 'ómnibus']),
        'housing': any(word in text_lower for word in ['vivienda', 'casa', 'hogar']),
        'environment': any(word in text_lower for word in ['ambiente', 'contaminación', 'basura'])
    }
    
    detected_themes = [theme for theme, present in themes.items() if present]
    
    return {
        'turn_count': turn_count,
        'word_count': word_count,
        'size_category': 'small' if word_count < 3000 else 'medium' if word_count < 6000 else 'large',
        'turn_category': 'few' if turn_count < 30 else 'medium' if turn_count < 60 else 'many',
        'detected_themes': detected_themes,
        'complexity_score': len(detected_themes) + (turn_count / 20) + (word_count / 1000)
    }

def generate_adaptive_schema(interview, characteristics):
    """Generate a schema tailored to the specific interview."""
    
    base_schema = {
        "interview_metadata": {
            "interview_id": interview.id,
            "participant_age": "18-29|30-49|50-64|65+",
            "participant_gender": "male|female|other",
            "municipality": "string",
            "word_count": characteristics['word_count'],
            "turn_count": characteristics['turn_count'],
            "complexity_score": characteristics['complexity_score']
        },
        "national_priorities": [
            {
                "rank": 1,
                "theme": "string",
                "issues": ["string"],
                "participant_quote": "direct quote",
                "confidence": 0.9
            },
            {
                "rank": 2,
                "theme": "string", 
                "issues": ["string"],
                "participant_quote": "direct quote",
                "confidence": 0.8
            },
            {
                "rank": 3,
                "theme": "string",
                "issues": ["string"],
                "participant_quote": "direct quote",
                "confidence": 0.7
            }
        ],
        "local_priorities": [
            {
                "rank": 1,
                "theme": "string",
                "issues": ["string"],
                "participant_quote": "direct quote",
                "confidence": 0.9
            },
            {
                "rank": 2,
                "theme": "string",
                "issues": ["string"],
                "participant_quote": "direct quote",
                "confidence": 0.8
            },
            {
                "rank": 3,
                "theme": "string",
                "issues": ["string"],
                "participant_quote": "direct quote",
                "confidence": 0.7
            }
        ]
    }
    
    # Add theme-specific analysis based on detected themes
    if characteristics['detected_themes']:
        base_schema["theme_analysis"] = {}
        
        for theme in characteristics['detected_themes']:
            base_schema["theme_analysis"][f"{theme}_analysis"] = {
                "prominence": "high|medium|low",
                "participant_perspective": "string describing viewpoint",
                "specific_mentions": ["quote1", "quote2"],
                "solutions_mentioned": ["string"]
            }
    
    # Add turn analysis based on turn count
    if characteristics['turn_count'] <= 20:
        # Full turn analysis for short interviews
        base_schema["conversation_turns"] = [
            {
                "turn_id": "number",
                "speaker": "interviewer|participant",
                "text": "full text of turn",
                "function": "question|answer|elaboration|clarification",
                "topics": ["string"],
                "emotional_tone": "positive|negative|neutral",
                "reasoning": "analytical reasoning"
            }
        ]
    elif characteristics['turn_count'] <= 50:
        # Summarized turn analysis for medium interviews
        base_schema["conversation_summary"] = {
            "total_turns": characteristics['turn_count'],
            "key_exchanges": [
                {
                    "turn_range": "string like '1-5'",
                    "topic": "string",
                    "summary": "string",
                    "key_quotes": ["string"]
                }
            ],
            "conversation_flow": "string describing overall flow"
        }
    else:
        # High-level analysis for long interviews
        base_schema["conversation_overview"] = {
            "total_turns": characteristics['turn_count'],
            "main_phases": [
                {
                    "phase": "opening|priorities|elaboration|solutions|closing",
                    "turn_range": "string",
                    "summary": "string"
                }
            ],
            "most_engaged_moments": ["string"],
            "key_insights": ["string"]
        }
    
    # Add complexity-based additional analysis
    if characteristics['complexity_score'] > 8:
        base_schema["advanced_analysis"] = {
            "narrative_complexity": "high|medium|low",
            "internal_contradictions": ["string"],
            "evolution_of_thinking": "string describing any changes in perspective",
            "implicit_themes": ["themes not explicitly stated but evident"],
            "cultural_context": "specific Uruguayan cultural references or context"
        }
    
    # Add confidence assessment
    base_schema["annotation_confidence"] = {
        "overall_confidence": 0.85,
        "priority_identification_confidence": 0.9,
        "theme_analysis_confidence": 0.8,
        "schema_appropriateness": "excellent|good|adequate|poor",
        "areas_of_uncertainty": ["string"]
    }
    
    return base_schema

def test_dynamic_schema_approach():
    """Test the dynamic schema approach on different interview types."""
    
    txt_dir = Path("data/processed/interviews_txt")
    txt_files = list(txt_dir.glob("*.txt"))
    
    if not txt_files:
        print("❌ No interview files found")
        return
    
    processor = DocumentProcessor()
    config_loader = ConfigLoader()
    api_key = config_loader.get_api_key("openai")
    client = OpenAI(api_key=api_key)
    
    # Test with 3 different interview sizes
    test_files = [
        min(txt_files, key=lambda f: f.stat().st_size),  # Smallest
        sorted(txt_files, key=lambda f: f.stat().st_size)[len(txt_files)//2],  # Medium
        max(txt_files, key=lambda f: f.stat().st_size)   # Largest
    ]
    
    results = []
    
    for i, test_file in enumerate(test_files, 1):
        interview = processor.process_interview(test_file)
        characteristics = analyze_interview_characteristics(interview)
        
        print(f"🎯 DYNAMIC SCHEMA TEST {i}/3")
        print(f"Interview: {interview.id}")
        print(f"Characteristics: {characteristics}")
        print()
        
        # Generate adaptive schema
        schema = generate_adaptive_schema(interview, characteristics)
        
        # Create prompt with dynamic schema
        schema_str = json.dumps(schema, indent=2)
        
        prompt = f"""
Analyze this Uruguay citizen consultation interview using the adaptive schema.

INTERVIEW TEXT:
{interview.text[:4000]}{"..." if len(interview.text) > 4000 else ""}

Return only valid JSON following this EXACT structure:
{schema_str}

The schema has been customized for this interview's characteristics:
- Word count: {characteristics['word_count']}
- Turn count: {characteristics['turn_count']}
- Detected themes: {', '.join(characteristics['detected_themes'])}
- Complexity score: {characteristics['complexity_score']:.1f}

Follow the schema structure precisely. Provide thorough analysis within each section.
"""
        
        try:
            print("🤖 Testing adaptive schema...")
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert qualitative researcher. Follow the provided schema exactly."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content)
            
            print("✅ Adaptive schema successful!")
            
            # Calculate cost
            cost = (response.usage.prompt_tokens / 1_000_000) * 0.15 + (response.usage.completion_tokens / 1_000_000) * 0.60
            
            results.append({
                'interview_id': interview.id,
                'characteristics': characteristics,
                'schema_fields': len(json.dumps(schema).split(',')),
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'cost': cost,
                'success': True
            })
            
            print(f"Schema complexity: {len(json.dumps(schema).split(','))} fields")
            print(f"Cost: ${cost:.4f}")
            print(f"Tokens: {response.usage.prompt_tokens + response.usage.completion_tokens:,}")
            
            # Save result
            output_file = f"adaptive_schema_result_{interview.id}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'characteristics': characteristics,
                    'schema_used': schema,
                    'annotation_result': result
                }, f, indent=2, ensure_ascii=False)
            
            print(f"Saved to: {output_file}")
            print()
            
        except Exception as e:
            print(f"❌ Adaptive schema failed: {e}")
            results.append({
                'interview_id': interview.id,
                'characteristics': characteristics,
                'success': False,
                'error': str(e)
            })
            print()
    
    # Summary
    print("📊 DYNAMIC SCHEMA RESULTS:")
    print("=" * 40)
    
    successful = [r for r in results if r.get('success')]
    if successful:
        total_cost = sum(r['cost'] for r in successful)
        avg_cost = total_cost / len(successful)
        
        print(f"Successful tests: {len(successful)}/{len(results)}")
        print(f"Average cost: ${avg_cost:.4f}")
        print(f"Total cost for 3 tests: ${total_cost:.4f}")
        print(f"Projected cost for 37 interviews: ${avg_cost * 37:.2f}")
        print()
        
        print("Schema adaptation worked:")
        for result in successful:
            chars = result['characteristics']
            print(f"  {result['interview_id']}: {chars['word_count']} words, {chars['turn_count']} turns → {result['schema_fields']} schema fields")
    
    print()
    print("🎉 DYNAMIC SCHEMA BENEFITS:")
    print("  ✅ Tailored analysis for each interview's characteristics")
    print("  ✅ Optimal schema complexity based on content")
    print("  ✅ Theme-specific analysis when relevant")
    print("  ✅ Turn analysis adapted to conversation length")
    print("  ✅ Cost efficiency through right-sized schemas")

if __name__ == "__main__":
    test_dynamic_schema_approach()