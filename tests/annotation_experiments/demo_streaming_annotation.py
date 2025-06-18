#!/usr/bin/env python3
"""
Demo of streaming annotation with function calling for fine-grained control.
Shows how to maintain progressive control in a single API call.
"""
import json
from typing import Dict, List, Any

def demo_streaming_annotation_pattern():
    """Show what the streaming function calling pattern would look like."""
    
    print("🎯 STREAMING ANNOTATION WITH FUNCTION CALLING")
    print("=" * 60)
    
    # Define the functions the model can call
    functions = [
        {
            "name": "fill_interview_metadata",
            "description": "Fill interview-level metadata fields",
            "parameters": {
                "type": "object",
                "properties": {
                    "interview_id": {"type": "string"},
                    "date": {"type": "string"},
                    "municipality": {"type": "string"},
                    "department": {"type": "string"},
                    "participant_age": {"type": "string"},
                    "participant_gender": {"type": "string"}
                },
                "required": ["interview_id", "date", "municipality"]
            }
        },
        {
            "name": "analyze_turn_reasoning",
            "description": "Provide chain-of-thought reasoning for a conversation turn",
            "parameters": {
                "type": "object",
                "properties": {
                    "turn_id": {"type": "integer"},
                    "reasoning": {"type": "string", "description": "Detailed reasoning for annotation decisions"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                },
                "required": ["turn_id", "reasoning", "confidence"]
            }
        },
        {
            "name": "annotate_turn_function",
            "description": "Determine the primary function of a conversation turn",
            "parameters": {
                "type": "object",
                "properties": {
                    "turn_id": {"type": "integer"},
                    "primary_function": {
                        "type": "string",
                        "enum": ["greeting", "problem_identification", "solution_proposal", 
                                "agreement", "disagreement", "question", "clarification", 
                                "narrative", "evaluation", "closing"]
                    },
                    "secondary_functions": {"type": "array", "items": {"type": "string"}},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                },
                "required": ["turn_id", "primary_function", "confidence"]
            }
        },
        {
            "name": "annotate_turn_content",
            "description": "Analyze the content and topics of a conversation turn",
            "parameters": {
                "type": "object",
                "properties": {
                    "turn_id": {"type": "integer"},
                    "topics": {"type": "array", "items": {"type": "string"}},
                    "geographic_scope": {"type": "string", "enum": ["local", "national", "regional"]},
                    "evidence_type": {"type": "string", "enum": ["personal_experience", "hearsay", "media", "official"]},
                    "emotional_valence": {"type": "string", "enum": ["positive", "negative", "neutral", "mixed"]}
                },
                "required": ["turn_id", "topics"]
            }
        },
        {
            "name": "request_guidance",
            "description": "Ask for clarification or guidance when uncertain",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "context": {"type": "string"},
                    "options": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["question", "context"]
            }
        }
    ]
    
    print("\n📋 FUNCTION DEFINITIONS:")
    for func in functions:
        print(f"  • {func['name']}: {func['description']}")
    
    print("\n🔄 STREAMING CONVERSATION FLOW:")
    print("-" * 40)
    
    # Simulate the streaming conversation
    conversation_flow = [
        {
            "role": "system",
            "content": "You are analyzing an interview. Fill the annotation systematically using function calls. Start with metadata, then analyze each turn with reasoning before making annotations."
        },
        {
            "role": "user", 
            "content": """
INTERVIEW TEXT:
Entrevistador: Buenos días, ¿podría contarme cuáles considera que son los principales problemas de Uruguay?
Participante: Buenos días. Mire, para mí el tema más grave es la seguridad. En mi barrio han robado varias veces...

[Full interview text would be here]

TASK: Analyze this interview systematically. Start with metadata, then analyze each conversation turn with detailed reasoning.
"""
        }
    ]
    
    # Simulated streaming responses with function calls
    streaming_responses = [
        {
            "type": "function_call",
            "function": "fill_interview_metadata",
            "arguments": {
                "interview_id": "20250528_0900_058",
                "date": "2025-05-28",
                "municipality": "Montevideo", 
                "department": "Montevideo",
                "participant_age": "middle_aged",
                "participant_gender": "male"
            },
            "reasoning": "Extracted from filename and interview content analysis"
        },
        {
            "type": "function_call", 
            "function": "analyze_turn_reasoning",
            "arguments": {
                "turn_id": 1,
                "reasoning": "The interviewer's opening turn serves as a broad, open-ended question designed to elicit the participant's top-of-mind priorities. The phrasing 'principales problemas' frames the conversation around challenges rather than opportunities. This is a classic opening move in qualitative research to establish rapport and get the participant talking about their concerns without leading them toward specific topics.",
                "confidence": 0.95
            }
        },
        {
            "type": "function_call",
            "function": "annotate_turn_function", 
            "arguments": {
                "turn_id": 1,
                "primary_function": "question",
                "secondary_functions": ["greeting"],
                "confidence": 0.9
            }
        },
        {
            "type": "function_call",
            "function": "analyze_turn_reasoning",
            "arguments": {
                "turn_id": 2,
                "reasoning": "The participant immediately identifies security as the primary concern and provides concrete, localized evidence through personal neighborhood experience. The response pattern shows: 1) Direct answer to the question, 2) Personal prioritization ('para mí'), 3) Immediate grounding in lived experience ('en mi barrio'). This indicates high salience and emotional investment in the security topic.",
                "confidence": 0.88
            }
        },
        {
            "type": "function_call",
            "function": "annotate_turn_function",
            "arguments": {
                "turn_id": 2, 
                "primary_function": "problem_identification",
                "secondary_functions": ["narrative"],
                "confidence": 0.92
            }
        },
        {
            "type": "function_call",
            "function": "annotate_turn_content",
            "arguments": {
                "turn_id": 2,
                "topics": ["security", "crime", "neighborhood_safety"],
                "geographic_scope": "local",
                "evidence_type": "personal_experience", 
                "emotional_valence": "negative"
            }
        },
        {
            "type": "function_call",
            "function": "request_guidance",
            "arguments": {
                "question": "Should I continue with systematic turn-by-turn analysis or focus on priority themes first?",
                "context": "I've analyzed the first two turns and see a clear security priority emerging. The participant is providing rich narrative detail.",
                "options": ["Continue turn-by-turn", "Identify all priority themes first", "Focus on security narrative"]
            }
        }
    ]
    
    print("\n🤖 MODEL FUNCTION CALLS (Streamed):")
    for i, response in enumerate(streaming_responses, 1):
        print(f"\n  Call {i}: {response['function']}")
        print(f"    Arguments: {json.dumps(response['arguments'], indent=6)}")
        
        # Show our response/guidance
        if response['function'] == 'fill_interview_metadata':
            our_response = "✅ Metadata looks good. Now analyze each turn with reasoning first."
        elif response['function'] == 'analyze_turn_reasoning':
            our_response = f"✅ Good reasoning for turn {response['arguments']['turn_id']}. Now determine the function."
        elif response['function'] == 'annotate_turn_function':
            our_response = f"✅ Function annotation complete for turn {response['arguments']['turn_id']}. Continue with content analysis."
        elif response['function'] == 'annotate_turn_content':
            our_response = f"✅ Turn {response['arguments']['turn_id']} complete. Move to next turn."
        elif response['function'] == 'request_guidance':
            our_response = "Continue turn-by-turn for complete coverage. Prioritize reasoning quality."
        
        print(f"    Our Response: {our_response}")
    
    print(f"\n💰 COST COMPARISON:")
    print(f"  Traditional Progressive: ~740 API calls = ~$9.60")
    print(f"  Streaming Functions: 1 API call = ~$0.013")
    print(f"  Cost Reduction: 99.86% savings!")
    
    print(f"\n✨ ADVANTAGES:")
    print(f"  🎯 Maintains fine-grained control")
    print(f"  🧠 Preserves chain-of-thought reasoning")
    print(f"  🔄 Allows mid-stream guidance/correction")
    print(f"  💰 Single API call cost")
    print(f"  📋 Systematic progression through schema")
    print(f"  ✅ Real-time validation and feedback")
    
    print(f"\n🔧 IMPLEMENTATION REQUIREMENTS:")
    print(f"  • OpenAI function calling API")
    print(f"  • Streaming response handling")
    print(f"  • Function call interception and response")
    print(f"  • XML state management during stream")
    print(f"  • Real-time validation and guidance injection")


def show_actual_api_call():
    """Show what the actual OpenAI API call would look like."""
    
    print(f"\n🔧 ACTUAL OPENAI API CALL:")
    print("=" * 40)
    
    api_call_example = {
        "model": "gpt-4.1-nano",
        "messages": [
            {
                "role": "system",
                "content": "You are an expert qualitative researcher. Analyze interviews systematically using function calls. Always provide reasoning before making annotations."
            },
            {
                "role": "user",
                "content": "[FULL INTERVIEW TEXT AND ANNOTATION SCHEMA HERE]"
            }
        ],
        "functions": "... [function definitions from above]",
        "function_call": "auto",
        "stream": True,
        "temperature": 0.1
    }
    
    print(f"API Call Structure:")
    print(f"  Model: gpt-4.1-nano (cheapest)")
    print(f"  Stream: True (real-time function calls)")
    print(f"  Functions: 5 annotation functions defined")
    print(f"  Function Call: auto (model decides when to call)")
    print(f"  Temperature: 0.1 (consistent outputs)")
    
    print(f"\nStreaming Response Handler:")
    print(f"  1. Receive function call")
    print(f"  2. Validate arguments against schema") 
    print(f"  3. Update XML with new data")
    print(f"  4. Send guidance/correction if needed")
    print(f"  5. Continue stream until complete")


if __name__ == "__main__":
    demo_streaming_annotation_pattern()
    show_actual_api_call()