# Recursive Agent Demonstration

This document demonstrates how the recursive agent functionality works in the Uruguay interview research system.

## Overview

The research agent can now spawn sub-agents to delegate specific research tasks. This creates a hierarchical research structure where:
- A root agent handles the broad research question
- Sub-agents investigate specific themes or perspectives
- Sub-sub-agents can drill down even further (up to max depth)

## Key Features

### 1. Automatic Depth Tracking
- Each agent knows its depth level (0 = root, 1 = first sub-agent, etc.)
- Maximum depth is configurable (default: 3)
- Agents at max depth cannot spawn further sub-agents

### 2. Delegation Tool
```python
spawn_sub_agent(
    question="Specific research question",
    context="What parent found and why delegation is needed",
    max_iterations=10  # Optional, default 10
)
```

### 3. Result Aggregation
Sub-agents return structured JSON results that include:
- Final research summary
- Key findings from scratchpad
- Statistics about their exploration
- Session tracking for audit trail

## Example Usage

### Root Agent Question
```
"What are the main challenges facing rural communities in Uruguay?"
```

### Expected Delegation Pattern
```
ROOT: "What are the main challenges facing rural communities?"
├── SUB 1: "Analyze healthcare access challenges in rural areas"
│   ├── SUB 1.1: "Focus on specialist availability and wait times"
│   └── SUB 1.2: "Examine emergency services coverage"
├── SUB 2: "Investigate educational infrastructure in rural schools"
│   └── SUB 2.1: "Study teacher retention and support systems"
└── SUB 3: "Explore economic opportunities and youth migration"
```

## Running the Test

### Basic Test
```bash
python test_recursive_agent.py
```

### Manual Test with Specific Question
```bash
python interview_research_agent_improved.py --research \
  "Compare healthcare experiences between urban Montevideo and rural interior regions"
```

### Direct Sub-Agent Call (for testing)
```bash
python interview_research_agent_improved.py \
  --sub-agent --depth 1 --parent test123 --max-depth 2 \
  "Analyze rural healthcare infrastructure challenges"
```

## System Prompt Guidance

The agent receives guidance about delegation in several places:

1. **Hierarchy Context**: Sub-agents are told their depth level
2. **Delegation Strategy**: Clear criteria for when to delegate
3. **Tool Description**: spawn_sub_agent tool explains its purpose
4. **Examples**: Concrete delegation patterns in the prompt

## Benefits

1. **Comprehensive Coverage**: Complex topics get thorough exploration
2. **Parallel Investigation**: Multiple themes explored simultaneously
3. **Specialized Analysis**: Each sub-agent focuses on specific aspect
4. **Scalable Research**: Can handle very broad research questions
5. **Audit Trail**: Complete tracking of delegation hierarchy

## Configuration

In `interview_research_tools.py`:
- Tool definition includes max_iterations parameter
- Command template passes depth and parent info

In `interview_research_agent_improved.py`:
- Agent class tracks depth, max_depth, parent_session_id
- Sub-agents run with reduced verbosity
- Results simplified for parent consumption

## Monitoring

Look for these indicators in the logs:
- 🚀 Delegation messages when spawning sub-agents
- Depth level shown in agent initialization
- Sub-agent results returned as JSON
- Statistics tracking number of sub-agents spawned