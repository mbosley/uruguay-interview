#!/usr/bin/env python3
"""Test with simplified JSON schema that will actually work."""
import sys
from pathlib import Path
import json
from openai import OpenAI

# Add project root to path
sys.path.insert(0, str(Path.cwd()))

from src.pipeline.ingestion.document_processor import DocumentProcessor
from src.config.config_loader import ConfigLoader

def test_simple_json_annotation():
    """Test with a simpler schema that will actually complete."""
    
    # Find test interview
    txt_dir = Path("data/processed/interviews_txt")
    txt_files = list(txt_dir.glob("*.txt"))
    
    if not txt_files:
        print("❌ No interview files found")
        return
    
    # Use smallest file
    test_file = min(txt_files, key=lambda f: f.stat().st_size)
    
    # Process interview
    processor = DocumentProcessor()
    interview = processor.process_interview(test_file)
    
    print("🎯 SIMPLIFIED JSON MODE TEST")
    print("=" * 40)
    print(f"Interview: {interview.id}")
    print(f"Word count: {len(interview.text.split()):,}")
    print()
    
    # Get API client
    config_loader = ConfigLoader()
    api_key = config_loader.get_api_key("openai")
    client = OpenAI(api_key=api_key)
    
    # Create simplified prompt
    prompt = f"""
Analyze this Uruguay citizen consultation interview and provide a structured JSON response.

INTERVIEW TEXT:
{interview.text[:2000]}...

Return only valid JSON with this structure:
{{
  "interview_id": "{interview.id}",
  "participant_age": "18-29|30-49|50-64|65+",
  "participant_gender": "male|female|other",
  "municipality": "string",
  "national_priorities": [
    {{"rank": 1, "theme": "string", "issues": ["string"], "quote": "participant quote"}},
    {{"rank": 2, "theme": "string", "issues": ["string"], "quote": "participant quote"}},
    {{"rank": 3, "theme": "string", "issues": ["string"], "quote": "participant quote"}}
  ],
  "local_priorities": [
    {{"rank": 1, "theme": "string", "issues": ["string"], "quote": "participant quote"}},
    {{"rank": 2, "theme": "string", "issues": ["string"], "quote": "participant quote"}},
    {{"rank": 3, "theme": "string", "issues": ["string"], "quote": "participant quote"}}
  ],
  "conversation_turns": [
    {{
      "turn_id": 1,
      "speaker": "interviewer|participant", 
      "text": "what was said",
      "function": "question|answer|elaboration|clarification",
      "reasoning": "why this function was chosen"
    }}
  ],
  "confidence": 0.85
}}

Focus on accuracy. Extract the participant's top priorities with supporting quotes.
"""
    
    try:
        print("🤖 Making simplified JSON API call...")
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert qualitative researcher. Respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        # Parse response
        result = json.loads(response.choices[0].message.content)
        
        print("✅ JSON annotation successful!")
        print()
        
        # Display results
        print("📊 ACTUAL RESULTS:")
        print("=" * 30)
        
        print(f"Interview ID: {result['interview_id']}")
        print(f"Participant: {result['participant_age']} {result['participant_gender']}")
        print(f"Municipality: {result['municipality']}")
        print(f"Confidence: {result['confidence']}")
        print()
        
        print("🎯 NATIONAL PRIORITIES:")
        for priority in result['national_priorities']:
            print(f"  {priority['rank']}. {priority['theme']}")
            print(f"     Issues: {', '.join(priority['issues'])}")
            print(f"     Quote: \"{priority['quote']}\"")
            print()
        
        print("🏠 LOCAL PRIORITIES:")
        for priority in result['local_priorities']:
            print(f"  {priority['rank']}. {priority['theme']}")
            print(f"     Issues: {', '.join(priority['issues'])}")
            print(f"     Quote: \"{priority['quote']}\"")
            print()
        
        print(f"🔄 CONVERSATION ANALYSIS ({len(result['conversation_turns'])} turns):")
        for turn in result['conversation_turns'][:5]:
            print(f"  Turn {turn['turn_id']} ({turn['speaker']}): {turn['function']}")
            text_preview = turn['text'][:60] + "..." if len(turn['text']) > 60 else turn['text']
            print(f"    \"{text_preview}\"")
            reasoning_preview = turn['reasoning'][:80] + "..." if len(turn['reasoning']) > 80 else turn['reasoning']
            print(f"    Reasoning: {reasoning_preview}")
            print()
        
        if len(result['conversation_turns']) > 5:
            print(f"  ... and {len(result['conversation_turns']) - 5} more turns")
        
        # Save result
        output_file = "simple_json_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Saved to: {output_file}")
        
        # Cost calculation
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        cost = (prompt_tokens / 1_000_000) * 0.15 + (completion_tokens / 1_000_000) * 0.60
        
        print(f"\n💰 ACTUAL COST: ${cost:.4f}")
        print(f"   Prompt tokens: {prompt_tokens:,}")
        print(f"   Completion tokens: {completion_tokens:,}")
        
        print(f"\n🎉 JSON MODE WORKS!")
        print(f"   ✅ Real API call completed successfully")
        print(f"   ✅ Valid JSON response received")
        print(f"   ✅ Structured priority extraction")
        print(f"   ✅ Turn-by-turn analysis with reasoning")
        print(f"   ✅ Cost-effective: ${cost:.4f} per interview")
        print(f"   ✅ 37 interviews would cost: ${cost * 37:.2f}")
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing failed: {e}")
        print("Response was not valid JSON")
        
    except Exception as e:
        print(f"❌ API call failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_simple_json_annotation()