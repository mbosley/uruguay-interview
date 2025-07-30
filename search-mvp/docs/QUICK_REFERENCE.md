# Quick Reference Guide

## Command Line Usage

### Basic Usage
```bash
# Simple research question
python interview_research_agent.py "What do citizens say about healthcare?"

# With make command
make agent QUESTION="What are the main security concerns?"
```

### Advanced Options
```bash
# All options
python interview_research_agent.py \
  --provider moonshot \
  --max-iterations 20 \
  --research \
  --debug \
  --width 100 \
  "Your research question"

# Using make with options
make agent PROVIDER=groq MAX_ITER=15 DEBUG=1 WIDTH=60 QUESTION="test"
```

## Citation Format Reference

### Standard Citations
- `[[064:23]]` - Interview 064, turn 23
- `[[071:45]]` - Interview 071, turn 45
- `[[089:12]]` - Interview 089, turn 12

### Range Citations
- `[[064:23-30]]` - Interview 064, turns 23 through 30
- `[[071:45-50]]` - Interview 071, turns 45 through 50

### Summary Citations
- `[[068:summary]]` - Summary of interview 068
- `[[092:summary]]` - Summary of interview 092

## Tool Reference

### Information Gathering
- `get_corpus_stats()` - Overview of all interviews
- `list_interview_themes()` - List all 121 themes or themes for specific interview

### Search Tools
- `search_interviews(query)` - Text/semantic search across corpus
- `search_themes(keyword)` - Find themes by keyword

### Content Retrieval
- `get_interview_turn(turn_id)` - Get specific turn or range
  - Single turn: `"064:23"`
  - Range: `"064:23-30"`
  - Summary: `"064:"`

### Note Taking
- `scratchpad_append(note)` - Add to research notes
- `scratchpad_read()` - Review all notes

## Debug Mode Features

When running with `--debug`:
- Detailed API call logging
- Full error tracebacks
- Tool execution timing
- Token usage per call
- Event store interactions

## Output Formatting

### Width Control
- Default: 80 characters
- Affects all output including:
  - Section headers
  - Tool results
  - Thinking sections
  - Scratchpad notes
  - Final reports

### Visual Indicators
- `🚀` Agent initialization
- `🔄` Iteration start
- `💭` Agent thinking
- `🔧` Tool execution
- `✅` Tool success
- `📝` Scratchpad note
- `📋` Report generation
- `✨` Completion
- `❌` Error

## Common Issues

### Report Not Generating
- Ensure at least 3 tool calls completed
- Check for API errors in debug mode
- Verify provider credentials

### Text Wrapping Issues
- Use `--width` to adjust output width
- Default is 80 characters
- Minimum recommended: 60

### Debug Information
- Use `--debug` flag for detailed logs
- Check event store for full trace
- Review tool execution timing