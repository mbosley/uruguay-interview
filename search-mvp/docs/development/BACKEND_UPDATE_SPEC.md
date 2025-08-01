# Backend Update Specification for Enhanced Demo

## Overview
This specification details the required backend changes to support the enhanced single-page demo with full preview capabilities and streaming report generation.

## Current State

### Event Structure
Currently, the backend emits events through the event store with this structure:
```python
{
    "type": "tool_result",
    "data": {
        "tool": "search_interviews",  # Missing in current implementation
        "metadata": {
            "size": 1234,
            "preview": "Found 5 results..."
        }
    },
    "timestamp": "2025-07-29T..."
}
```

### Issues
1. `tool_result` events don't include the tool name
2. `tool_result` events don't include the actual result data
3. Final report generation happens all at once (no streaming)
4. No separate LLM call for report synthesis

## Required Changes

### 1. Enhanced Tool Result Events

**File**: `search-mvp/interview_research_agent_improved.py`

**Location**: Around line 528 in the `autonomous_research` method

**Current Code**:
```python
# Emit tool_result event
await self.emit_event("tool_result", {
    "tool": tool_name,
    "metadata": {
        "size": len(result),
        "preview": preview or result[:200] + "..." if len(result) > 200 else result
    }
}, iteration + 1)
```

**Updated Code**:
```python
# Emit tool_result event with full data
await self.emit_event("tool_result", {
    "tool": tool_name,
    "result": result,  # Include full result
    "metadata": {
        "size": len(result),
        "preview": self._generate_preview(tool_name, result)
    }
}, iteration + 1)
```

**Add Helper Method**:
```python
def _generate_preview(self, tool_name: str, result: str) -> str:
    """Generate informative preview based on tool type"""
    try:
        if tool_name == "get_corpus_stats":
            data = json.loads(result)
            return f"{data.get('total_interviews', 0)} interviews, {data.get('total_turns', 0)} turns"
        
        elif tool_name == "search_interviews":
            data = json.loads(result)
            results = data.get('results', [])
            return f"Found {len(results)} results"
        
        elif tool_name == "get_interview_turn":
            data = json.loads(result)
            if data.get('type') == 'interview_summary':
                return f"Interview {data.get('interview_id', '')} summary"
            elif data.get('turns'):
                return f"{len(data.get('turns', []))} turns retrieved"
        
        elif tool_name == "list_interview_themes":
            data = json.loads(result)
            theme_count = len(data.get('themes', {}))
            return f"{theme_count} themes found"
        
        else:
            return result[:200] + "..." if len(result) > 200 else result
            
    except:
        return result[:200] + "..." if len(result) > 200 else result
```

### 2. Streaming Report Generation

**Add New Method** to `InterviewResearchAgent`:

```python
async def generate_streaming_report(self, research_context: dict) -> AsyncGenerator[str, None]:
    """Generate final report with streaming"""
    
    # Emit start event
    await self.emit_event("response_start", {})
    
    # Build synthesis prompt
    synthesis_prompt = self._build_synthesis_prompt(research_context)
    
    # Stream response from LLM
    stream = self.client.chat.completions.create(
        model=self.model,
        messages=[
            {
                "role": "system",
                "content": "You are a qualitative research analyst. Synthesize the research findings into a clear, structured report with specific citations."
            },
            {
                "role": "user", 
                "content": synthesis_prompt
            }
        ],
        temperature=0.3,
        stream=True
    )
    
    full_response = ""
    for chunk in stream:
        if chunk.choices[0].delta.content:
            text = chunk.choices[0].delta.content
            full_response += text
            
            # Emit chunk event
            await self.emit_event("response_chunk", {
                "chunk": text
            })
            
            yield text
    
    # Extract sources from response
    sources = self._extract_sources(full_response)
    
    # Emit end event
    await self.emit_event("response_end", {
        "response": full_response,
        "sources": sources
    })
    
    return full_response

def _build_synthesis_prompt(self, research_context: dict) -> str:
    """Build prompt for synthesis with all research context"""
    
    # Extract key information from tool calls
    findings = []
    evidence = []
    
    for call in research_context.get('tool_calls', []):
        if call['tool'] == 'get_interview_turn' and 'result' in call:
            # Extract key quotes and context
            try:
                data = json.loads(call['result'])
                if data.get('turns'):
                    for turn in data['turns']:
                        evidence.append({
                            'interview': data.get('interview_id', ''),
                            'turn': turn.get('turn_id', ''),
                            'text': turn.get('text', ''),
                            'speaker': turn.get('speaker', '')
                        })
            except:
                pass
    
    prompt = f"""Based on the following research into the question: "{research_context['question']}"

Research Summary:
{research_context.get('scratchpad', 'No notes available')}

Key Evidence Collected:
{json.dumps(evidence, indent=2)}

Please synthesize these findings into a structured report following this format:

# STRUCTURED FINDINGS

## Key Findings

Finding_1: [Concise title of the finding]
- Statement: [Clear statement of what was found]
- Evidence: [Specific quotes with citations in format (interview:turn)]
- Significance: [Why this matters for the research question]

Finding_2: [Next finding...]
[Continue for all major findings]

## Summary
[Brief overall summary connecting the findings]

Guidelines:
- Use specific citations for every claim
- Quote directly from interviews when possible
- Focus on patterns and themes across multiple interviews
- Highlight contrasts or tensions in the data
"""
    
    return prompt
```

### 3. Update Main Research Flow

**Modify** `autonomous_research` method around line 671:

**Current Code**:
```python
# Emit final response events
await self.emit_event("response_start", {})
await self.emit_event("response_end", {
    "response": final_response,
    "sources": self._extract_sources(final_response)
})
```

**Updated Code**:
```python
# Generate streaming report with separate LLM call
research_context = {
    'question': research_question,
    'tool_calls': tool_call_log,
    'scratchpad': scratchpad_content,
    'iterations': iteration
}

# Stream the report
final_response = ""
async for chunk in self.generate_streaming_report(research_context):
    final_response += chunk

# Note: events are emitted within generate_streaming_report
```

### 4. Update API Server SSE Endpoint

**File**: `search-mvp/api_server.py`

No changes needed - the SSE endpoint already handles the event types correctly.

### 5. Event Store Updates

**File**: `search-mvp/event_store.py`

No changes needed - the event store is generic and handles any event structure.

## Testing Plan

### 1. Test Enhanced Tool Results
```python
# Verify tool_result events include full data
{
    "type": "tool_result",
    "data": {
        "tool": "search_interviews",
        "result": "{\"results\": [...]}",  # Full JSON result
        "metadata": {
            "size": 15234,
            "preview": "Found 12 results"
        }
    }
}
```

### 2. Test Streaming Report
```python
# Verify event sequence
1. response_start → {}
2. response_chunk → {"chunk": "# STRUCTURED"}
3. response_chunk → {"chunk": " FINDINGS\n\n"}
4. ... more chunks ...
5. response_end → {"response": full_text, "sources": [...]}
```

### 3. Frontend Compatibility
- Existing WebSocket endpoint should work unchanged
- New SSE endpoint properly formats events
- Demo receives and displays enhanced previews

## Implementation Steps

1. **Phase 1**: Enhanced tool results (30 min)
   - Add `_generate_preview` method
   - Update tool_result event emission
   - Test with existing demo

2. **Phase 2**: Report streaming (1 hour)
   - Add `generate_streaming_report` method
   - Add `_build_synthesis_prompt` helper
   - Update main research flow
   - Test streaming with demo

3. **Phase 3**: Testing & refinement (30 min)
   - Verify all event types work
   - Test edge cases
   - Ensure backward compatibility

## Backward Compatibility

All changes maintain backward compatibility:
- WebSocket clients continue to work
- Existing event structure is extended, not changed
- New fields are additions, not replacements

## Configuration Options

Add to `InterviewResearchAgent.__init__`:
```python
self.enable_streaming_report = kwargs.get('enable_streaming_report', True)
self.include_full_results = kwargs.get('include_full_results', True)
```

This allows gradual rollout and testing.