# AI Annotation Engine Implementation Summary

## Overview

We've implemented an XML-based AI annotation engine that leverages your carefully designed annotation schema to generate rich, structured annotations of citizen interviews.

## Key Design Decisions

### XML-Centric Approach
Based on your feedback that XML outputs produce richer quality than JSON, we've built the system to:
- **Inject interviews directly into the XML schema** as a complete document
- **Request XML output from the AI** to maintain structural fidelity
- **Parse and validate XML responses** to ensure schema compliance

### Architecture Components

1. **PromptManager** (`src/pipeline/annotation/prompt_manager.py`)
   - Loads and manages the XML annotation schema
   - Creates prompts by injecting interview content into the schema
   - Parses and validates XML responses from AI
   - Extracts key data points for downstream processing

2. **AnnotationEngine** (`src/pipeline/annotation/annotation_engine.py`)
   - Supports both OpenAI and Anthropic models
   - Handles API calls with retry logic
   - Validates annotations against schema
   - Adds processing metadata
   - Supports batch processing

## How It Works

### 1. Prompt Creation
```python
# The system creates a complete XML document with the interview embedded
prompt = prompt_manager.create_annotation_prompt(interview_text, metadata)
```

The prompt includes:
- Full XML schema with all instructions and examples
- Interview metadata (date, location, participants)
- Interview text to be analyzed
- Clear instructions to complete the XML annotation

### 2. AI Processing
```python
# Call AI with XML-focused instructions
annotation_xml = engine._call_openai(prompt, temperature=0.3)
```

The AI is instructed to:
- Follow the XML schema exactly
- Fill in all required fields
- Use participant's own words
- Include confidence scores
- Flag uncertainties

### 3. Response Parsing
```python
# Extract and validate the annotation
annotation = prompt_manager.parse_annotation_response(xml_response)
is_valid, errors = prompt_manager.validate_annotation(annotation)
```

The system:
- Extracts the `<annotation_result>` from the response
- Validates against schema requirements
- Checks for missing fields and invalid values
- Provides detailed error messages

## XML Schema Integration

The implementation fully leverages your XML schema including:

- **Role definitions and mindset** from `<annotator_instructions>`
- **Step-by-step process** for annotation workflow
- **Priority ranking structure** with narratives
- **Uncertainty tracking** with confidence scores
- **Rich narrative features** and emotional coding
- **Quality checklist** and ethical reminders

## Example Usage

```python
# Initialize components
processor = DocumentProcessor()
engine = AnnotationEngine(model_provider="openai")

# Process an interview
interview = processor.process_interview("path/to/interview.txt")
annotation, metadata = engine.annotate_interview(interview)

# Extract key data
data = engine.prompt_manager.extract_key_data(annotation)
print(f"Top national priority: {data['national_priorities'][0]['theme']}")
print(f"Confidence: {data['confidence']}")
```

## Quality Features

1. **Retry Logic**: Automatically retries on API failures or validation errors
2. **Cost Estimation**: Calculates annotation costs before processing
3. **Batch Processing**: Can handle multiple interviews efficiently
4. **Validation**: Comprehensive schema validation with error reporting
5. **Metadata Tracking**: Records model, timing, and confidence for each annotation

## Next Steps

With the annotation engine complete, we can now:
1. Process the sample interviews to test quality
2. Build the structured data extraction layer
3. Set up the PostgreSQL database
4. Create the dashboard visualizations

The XML-based approach ensures we maintain the richness and nuance of your annotation schema while enabling scalable processing of thousands of interviews.