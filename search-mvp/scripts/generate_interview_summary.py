#!/usr/bin/env python3
"""
Generate complete prompts for interview annotation
Outputs JSON that can be passed to any LLM API
"""

import json
import sys
from pathlib import Path

def load_guidelines():
    """Load the annotation guidelines template"""
    prompt_file = Path(__file__).parent.parent / "prompts" / "interview_annotation_prompt.md"
    
    if not prompt_file.exists():
        raise FileNotFoundError(f"Guidelines not found at {prompt_file}")
    
    with open(prompt_file, 'r', encoding='utf-8') as f:
        return f.read()

def load_interview(interview_id):
    """Load the interview data"""
    interview_path = Path(__file__).parent.parent.parent / "data" / "processed" / "structured" / f"{interview_id}.json"
    
    if not interview_path.exists():
        raise FileNotFoundError(f"Interview {interview_id} not found at {interview_path}")
    
    with open(interview_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_prompt_package(interview_id):
    """Generate a complete prompt package for API consumption"""
    
    interview_id = interview_id.zfill(3)  # Ensure 3-digit format
    
    # Load components
    guidelines = load_guidelines()
    interview_data = load_interview(interview_id)
    
    # Create the complete prompt package
    prompt_package = {
        "system": guidelines,
        "user": f"""Please analyze this Uruguay citizen consultation interview and create a comprehensive annotation following the guidelines provided.

Interview ID: {interview_id}

Interview Data:
{json.dumps(interview_data, indent=2, ensure_ascii=False)}

Create a complete annotation with:
1. Comprehensive tags (demographics, themes, emotions, etc.)
2. Rich thematic analysis of 2-4 major themes
3. Notable quotes with context
4. Conversation structure mapping
5. Research value assessment

Output only the JSON annotation structure, no additional text.""",
        "metadata": {
            "interview_id": interview_id,
            "interview_location": interview_data['metadata'].get('location', 'Unknown'),
            "total_turns": interview_data['total_turns'],
            "task": "interview_annotation"
        }
    }
    
    return prompt_package

def main():
    """Main function for command line usage"""
    if len(sys.argv) != 2:
        print("Usage: python generate_interview_summary.py <interview_id>", file=sys.stderr)
        print("Example: python generate_interview_summary.py 071", file=sys.stderr)
        sys.exit(1)
    
    interview_id = sys.argv[1]
    
    try:
        # Generate the complete prompt package
        prompt_package = generate_prompt_package(interview_id)
        
        # Output as JSON for API consumption
        print(json.dumps(prompt_package, indent=2, ensure_ascii=False))
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()