# Agent Tool Update: Interview Summary Feature

## Overview
The `get_interview_turn` tool has been enhanced to encourage more targeted exploration by the research agent.

## Changes

### Previous Behavior
- `get 072:` → Returns ALL turns from interview 072 (potentially overwhelming)
- `get 072:24` → Returns specific turn 24
- `get 072:20-25` → Returns turns 20-25

### New Behavior
- `get 072:` → Returns **interview summary** with:
  - Interview metadata
  - AI-generated summary
  - Key themes with descriptions
  - Priority rankings
  - First 3 notable quotes
  - Statistics (turn count, speakers, theme count)
  - Tips for deeper exploration
- `get 072:24` → Returns specific turn 24 (unchanged)
- `get 072:20-25` → Returns turns 20-25 (unchanged)
- `get 072: --full` → Returns all turns (old behavior, CLI only)

## Benefits

1. **Encourages Strategic Exploration**: Agent gets overview first, then dives into specific areas
2. **Reduces Token Usage**: Summary is ~1-2K tokens vs 10-50K for full interview
3. **Better Research Flow**: Natural progression from overview → themes → specific quotes
4. **Preserves Flexibility**: Can still get full interview if needed

## Example Agent Workflow

```python
# 1. Get overview of an interview
get_interview_turn("072:")
# Returns: summary, themes, notable quotes, stats

# 2. Based on themes, explore specific turns
get_interview_turn("072:89")  # A notable quote about education

# 3. Get context around interesting finding
get_interview_turn("072:85-93")  # Range around the quote
```

## Implementation Notes

- The `--full` flag is only available via CLI, not through the agent tools
- This encourages agents to be more selective and research-driven
- Summary includes "tips" section guiding agent to next steps
- Notable quotes are truncated to 200 chars with "..." to maintain readability