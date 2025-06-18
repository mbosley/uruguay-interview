# Annotation Experiments

This directory contains experimental scripts developed during the exploration of different annotation approaches for the Uruguay interview dataset.

## Experiment Overview

These experiments systematically explored different approaches to automated qualitative annotation, ultimately leading to the optimal JSON mode solution.

## Experiment Categories

### 1. Progressive Annotation Experiments
- `demo_progressive_with_caching.py` - Demonstrates progressive annotation with prompt caching
- `test_conversation_view.py` - Tests conversation turn detection and analysis

### 2. Instructor Library Experiments  
- `test_instructor.py` - Basic Instructor library setup and cost analysis
- `test_instructor_annotation.py` - Real API calls with Instructor
- `inspect_instructor_output.py` - Visual inspection of Instructor outputs
- `run_instructor_batch.py` - Batch processing with Instructor

### 3. Streaming Annotation Experiments
- `demo_streaming_annotation.py` - Function calling approach with streaming
- `test_real_annotation.py` - Real streaming annotation attempts

### 4. JSON Mode Experiments (Final Solution)
- `test_simple_json.py` - Initial JSON mode proof of concept
- `test_json_mode.py` - Enhanced JSON mode testing
- `test_json_limits.py` - Testing JSON mode complexity limits
- `test_dynamic_schemas.py` - Dynamic schema generation per interview
- `test_variable_lengths.py` - Length-adaptive schema testing
- `test_full_interview.py` - Complete interview annotation testing

### 5. Quality Analysis
- `compare_annotation_quality.py` - Qualitative comparison across approaches
- `demo_annotation_output.py` - Sample output demonstrations

## Key Findings

### Approach Comparison
1. **Progressive Annotation**: High quality but expensive (~$9.60/interview)
2. **Instructor Library**: Complex schema validation but prone to timeouts
3. **Streaming Function Calls**: Theoretical improvement but implementation complexity
4. **JSON Mode**: Optimal balance of quality, cost, and reliability

### Final Solution: Dynamic JSON Schemas
- **Cost**: $0.001-0.004 per interview (99.96% cost reduction)
- **Quality**: 55-85% depending on schema complexity
- **Reliability**: Consistent completion across all interview lengths
- **Adaptability**: Automatic schema adjustment based on interview characteristics

## Running Experiments

Each script is standalone and can be run independently:

```bash
python tests/annotation_experiments/test_simple_json.py
python tests/annotation_experiments/test_dynamic_schemas.py
python tests/annotation_experiments/compare_annotation_quality.py
```

## Results Data

Experimental results are saved as JSON files:
- `adaptive_schema_result_*.json` - Dynamic schema results
- `full_interview_annotation_*.json` - Comprehensive annotation results
- `simple_json_result.json` - Basic JSON mode results

## Integration Path

The successful JSON mode approach has been integrated into the main pipeline:
- `src/pipeline/annotation/json_mode_annotator.py` - Production implementation
- `src/pipeline/annotation/instructor_batch_annotator.py` - Alternative approach

## Next Steps

1. Convert successful experiments into formal test suite
2. Create performance benchmarks
3. Establish quality metrics and validation
4. Document production deployment procedures