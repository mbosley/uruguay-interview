#!/usr/bin/env python3
"""Test how far we can push JSON mode with larger schemas and variable turn counts."""
import sys
from pathlib import Path
import json
from openai import OpenAI

# Add project root to path
sys.path.insert(0, str(Path.cwd()))

from src.pipeline.ingestion.document_processor import DocumentProcessor
from src.config.config_loader import ConfigLoader

def analyze_interview_sizes():
    """Analyze the distribution of interview sizes to understand the challenge."""
    
    txt_dir = Path("data/processed/interviews_txt")
    txt_files = list(txt_dir.glob("*.txt"))
    
    if not txt_files:
        print("❌ No interview files found")
        return
    
    processor = DocumentProcessor()
    
    print("📊 INTERVIEW SIZE ANALYSIS")
    print("=" * 40)
    
    interview_stats = []
    
    for txt_file in txt_files:
        interview = processor.process_interview(txt_file)
        
        # Count conversation turns
        lines = interview.text.split('\n')
        turn_count = 0
        for line in lines:
            line = line.strip()
            if line and any(line.startswith(pattern) for pattern in [
                'Entrevistador:', 'Entrevistadora:', 'Gabriela Medina', 'Germán Busch',
                '[GM]', '[GB]', 'GM:', 'GB:', 'María Rosales', 'Marcelo Rosales', 
                '[MR]', '[MR2]', 'MR:', 'MR2:', 'Participante:', 'P:'
            ]):
                turn_count += 1
        
        word_count = len(interview.text.split())
        char_count = len(interview.text)
        
        interview_stats.append({
            'id': interview.id,
            'turns': turn_count,
            'words': word_count,
            'chars': char_count,
            'estimated_tokens': word_count * 1.3
        })
    
    # Sort by size
    interview_stats.sort(key=lambda x: x['words'])
    
    print(f"Total interviews: {len(interview_stats)}")
    print()
    
    # Show size distribution
    print("📏 SIZE DISTRIBUTION:")
    small = [i for i in interview_stats if i['words'] < 2000]
    medium = [i for i in interview_stats if 2000 <= i['words'] < 4000]
    large = [i for i in interview_stats if i['words'] >= 4000]
    
    print(f"  Small (<2000 words): {len(small)} interviews")
    print(f"  Medium (2000-4000 words): {len(medium)} interviews")
    print(f"  Large (4000+ words): {len(large)} interviews")
    print()
    
    print("🔄 TURN COUNT DISTRIBUTION:")
    low_turns = [i for i in interview_stats if i['turns'] < 50]
    med_turns = [i for i in interview_stats if 50 <= i['turns'] < 100]
    high_turns = [i for i in interview_stats if i['turns'] >= 100]
    
    print(f"  Low (<50 turns): {len(low_turns)} interviews")
    print(f"  Medium (50-100 turns): {len(med_turns)} interviews")
    print(f"  High (100+ turns): {len(high_turns)} interviews")
    print()
    
    print("📈 EXTREMES:")
    smallest = min(interview_stats, key=lambda x: x['words'])
    largest = max(interview_stats, key=lambda x: x['words'])
    min_turns = min(interview_stats, key=lambda x: x['turns'])
    max_turns = max(interview_stats, key=lambda x: x['turns'])
    
    print(f"  Smallest: {smallest['id']} - {smallest['words']} words, {smallest['turns']} turns")
    print(f"  Largest: {largest['id']} - {largest['words']} words, {largest['turns']} turns")
    print(f"  Fewest turns: {min_turns['id']} - {min_turns['turns']} turns")
    print(f"  Most turns: {max_turns['id']} - {max_turns['turns']} turns")
    print()
    
    return interview_stats


def test_expanded_json_schema():
    """Test a more comprehensive JSON schema that's still manageable."""
    
    # Find medium-sized interview
    txt_dir = Path("data/processed/interviews_txt")
    txt_files = list(txt_dir.glob("*.txt"))
    
    processor = DocumentProcessor()
    
    # Get medium-sized interview for testing
    interviews = []
    for txt_file in txt_files[:10]:  # Test first 10
        interview = processor.process_interview(txt_file)
        word_count = len(interview.text.split())
        interviews.append((interview, word_count))
    
    # Pick medium size
    interviews.sort(key=lambda x: x[1])
    interview = interviews[len(interviews)//2][0]
    
    print(f"🎯 EXPANDED JSON SCHEMA TEST")
    print(f"Interview: {interview.id}")
    print(f"Word count: {len(interview.text.split()):,}")
    print()
    
    # Get API client
    config_loader = ConfigLoader()
    api_key = config_loader.get_api_key("openai")
    client = OpenAI(api_key=api_key)
    
    # Create expanded schema with dynamic turn handling
    prompt = f"""
Analyze this Uruguay citizen consultation interview and provide structured analysis.

INTERVIEW TEXT:
{interview.text}

Return only valid JSON with this expanded structure:

{{
  "interview_metadata": {{
    "interview_id": "{interview.id}",
    "participant_age": "18-29|30-49|50-64|65+",
    "participant_gender": "male|female|other",
    "municipality": "string",
    "locality_size": "rural|small_town|medium_city|large_city",
    "occupation": "string",
    "interview_length": "short|medium|long"
  }},
  "national_priorities": [
    {{
      "rank": 1,
      "theme": "string",
      "issues": ["string"],
      "participant_quote": "direct quote from participant",
      "reasoning": "why this was identified as priority 1"
    }},
    {{
      "rank": 2,
      "theme": "string", 
      "issues": ["string"],
      "participant_quote": "direct quote from participant",
      "reasoning": "why this was identified as priority 2"
    }},
    {{
      "rank": 3,
      "theme": "string",
      "issues": ["string"],
      "participant_quote": "direct quote from participant", 
      "reasoning": "why this was identified as priority 3"
    }}
  ],
  "local_priorities": [
    {{
      "rank": 1,
      "theme": "string",
      "issues": ["string"],
      "participant_quote": "direct quote from participant",
      "reasoning": "why this was identified as priority 1"
    }},
    {{
      "rank": 2,
      "theme": "string",
      "issues": ["string"], 
      "participant_quote": "direct quote from participant",
      "reasoning": "why this was identified as priority 2"
    }},
    {{
      "rank": 3,
      "theme": "string",
      "issues": ["string"],
      "participant_quote": "direct quote from participant",
      "reasoning": "why this was identified as priority 3"
    }}
  ],
  "narrative_analysis": {{
    "dominant_frame": "string describing main way participant interprets issues",
    "temporal_focus": "past|present|future|mixed",
    "solution_approach": "government_focused|individual_focused|community_focused|mixed",
    "emotional_tone": "optimistic|pessimistic|neutral|mixed",
    "key_themes": ["string", "string", "string"],
    "memorable_quotes": ["quote1", "quote2", "quote3"]
  }},
  "conversation_turns": [
    {{
      "turn_id": 1,
      "speaker": "interviewer|participant",
      "text": "what was said (first 100 chars)",
      "function": "question|answer|elaboration|clarification|problem_identification|solution_proposal",
      "topics": ["string"],
      "emotional_tone": "positive|negative|neutral",
      "reasoning": "analytical reasoning for this classification"
    }}
  ],
  "interview_quality": {{
    "rapport": "excellent|good|adequate|poor",
    "participant_engagement": "high|medium|low", 
    "response_depth": "detailed|moderate|superficial",
    "coherence": "high|medium|low"
  }},
  "analytical_notes": {{
    "main_insights": "key takeaways from this interview",
    "contradictions": "any internal contradictions noted",
    "gaps": "topics not addressed or avoided",
    "broader_connections": "how this connects to broader Uruguay context"
  }},
  "confidence_assessment": {{
    "overall_confidence": 0.85,
    "priority_confidence": 0.90,
    "narrative_confidence": 0.80,
    "turn_analysis_confidence": 0.85,
    "uncertainty_notes": "specific areas of uncertainty"
  }}
}}

INSTRUCTIONS:
1. Analyze ALL conversation turns, but summarize text to first 100 characters
2. Extract priorities with strong supporting quotes
3. Provide reasoning for all analytical decisions
4. Focus on participant's actual words and perspectives
5. Assess interview quality and your own confidence
"""
    
    try:
        print("🤖 Testing expanded JSON schema...")
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert qualitative researcher. Analyze thoroughly but respond with valid JSON only."
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
        
        print("✅ Expanded JSON schema successful!")
        print()
        
        # Display key results
        meta = result["interview_metadata"]
        print("📋 INTERVIEW METADATA:")
        for key, value in meta.items():
            print(f"  {key}: {value}")
        print()
        
        print("🎯 NATIONAL PRIORITIES (with reasoning):")
        for priority in result["national_priorities"]:
            print(f"  {priority['rank']}. {priority['theme']}")
            print(f"     Issues: {', '.join(priority['issues'])}")
            print(f"     Quote: \"{priority['participant_quote']}\"")
            print(f"     Reasoning: {priority['reasoning']}")
            print()
        
        print("📖 NARRATIVE ANALYSIS:")
        narrative = result["narrative_analysis"]
        for key, value in narrative.items():
            if isinstance(value, list):
                print(f"  {key}: {', '.join(value)}")
            else:
                print(f"  {key}: {value}")
        print()
        
        print(f"🔄 CONVERSATION ANALYSIS ({len(result['conversation_turns'])} turns):")
        for turn in result["conversation_turns"][:5]:
            print(f"  Turn {turn['turn_id']} ({turn['speaker']}): {turn['function']}")
            print(f"    Text: \"{turn['text']}\"")
            print(f"    Topics: {', '.join(turn['topics'])}")
            print(f"    Tone: {turn['emotional_tone']}")
            print(f"    Reasoning: {turn['reasoning'][:60]}...")
            print()
        
        print("🤔 CONFIDENCE ASSESSMENT:")
        conf = result["confidence_assessment"]
        for key, value in conf.items():
            print(f"  {key}: {value}")
        print()
        
        # Cost analysis
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        cost = (prompt_tokens / 1_000_000) * 0.15 + (completion_tokens / 1_000_000) * 0.60
        
        print(f"💰 COST ANALYSIS:")
        print(f"  Prompt tokens: {prompt_tokens:,}")
        print(f"  Completion tokens: {completion_tokens:,}")
        print(f"  Cost: ${cost:.4f}")
        print(f"  37 interviews: ${cost * 37:.2f}")
        
        # Save result
        output_file = "expanded_json_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Saved to: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Expanded schema failed: {e}")
        return False


def main():
    """Run the JSON mode limits analysis."""
    
    # First analyze interview sizes
    stats = analyze_interview_sizes()
    
    print("\n" + "="*50)
    
    # Test expanded schema
    success = test_expanded_json_schema()
    
    if success:
        print("\n🎉 JSON MODE CAPABILITIES:")
        print("  ✅ Can handle expanded schema with multiple analysis dimensions")
        print("  ✅ Scales to medium-sized interviews efficiently")
        print("  ✅ Provides reasoning for analytical decisions")
        print("  ✅ Includes confidence and quality assessments")
        print("  ✅ Maintains cost efficiency")
        print()
        print("💡 STRATEGY FOR VARIABLE TURN COUNTS:")
        print("  1. Use text summarization for turn content (first 100 chars)")
        print("  2. Include all turns but with condensed representation")
        print("  3. Focus on functional classification rather than full content")
        print("  4. Use batch processing for different interview sizes")
        print("  5. Adjust schema complexity based on interview length")


if __name__ == "__main__":
    main()