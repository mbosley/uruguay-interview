# Comprehensive Context for Gemini: Uruguay Interview Research Agent UI

## Project Overview
I'm working on a qualitative research project analyzing 37 citizen consultation interviews from Uruguay. The project has a Streamlit web interface that allows users to query these interviews using an AI research agent.

## Current Problem
I've been trying to implement a polished, ChatGPT-like streaming interface but have created an overly complex mess. The user wants a clean, simple implementation that:
1. Shows real-time streaming responses (token-by-token)
2. Has a "thinking box" that shows the agent's reasoning process
3. Displays progress bars for multi-step research
4. Works with our existing Moonshot/Kimi API (not OpenAI)

## Backend Architecture

### Core Components

1. **Interview Research Agent** (`interview_research_agent_improved.py`):
   - Uses Moonshot AI's Kimi model via OpenAI-compatible API
   - Performs multi-step research with tool calls
   - Has methods like `autonomous_research()` that run iterative analysis
   - Logs progress to `logs/agent_session.log`
   - Returns results as a dict with `final_response`, `stats`, `tool_calls`

2. **Provider Configuration** (`config/providers.py`):
   ```python
   PROVIDERS = {
       "moonshot": ProviderConfig(
           name="moonshot",
           base_url="https://api.moonshot.ai/v1",
           api_key_env="MOONSHOT_API_KEY",
           model_name="kimi-k2-0711-preview",
           ...
       )
   }
   ```

3. **Research Tools** (`interview_research_tools.py`):
   - Various functions for searching/analyzing the interview corpus
   - Tools are called by the agent during research

### Current UI Implementation

**File**: `search-mvp/web_demo/pages/0_🔬_Research_Agent.py`

Current approach (which is failing):
1. Created a `KimiStreamingClient` wrapper to handle streaming
2. Tried to implement "THINKING:" and "ANSWER:" parsing in the stream
3. Attempted to patch the agent's logger to capture events
4. Mixed async/sync code in confusing ways

## What the User Actually Wants

The user showed me this ideal flow:
```
┌ assistant bubble ───────────────────────────────────────────────┐
│ 🧠 **Thinking**                                                 │  ← updates token-by-token
│ 1. Searching interviews for healthcare mentions...▌             │
│ 2. Building answer outline...                                  │
│ ─────────────────────────────────────────────────────────────── │
│ Citizens mention health, education and infrastructure most...▌  │  ← appears AFTER thinking
└─────────────────────────────────────────────────────────────────┘
```

Key requirements:
- Simple, clean code
- Real-time streaming with typing cursor
- Progress bar during research phases
- 3:1 column layout (chat : metrics)
- Example questions as clickable chips
- Thinking box appears ABOVE the final answer
- Works with existing agent, not a rewrite

## My Failed Attempts

1. **Overcomplicated Streaming Client**: Created `streaming_client.py` with complex event types, async generators, and monkey-patching
2. **Mixed Paradigms**: Tried to force streaming onto a non-streaming agent
3. **Too Many Abstractions**: StreamEvent classes, multiple callback systems, etc.

## Simple Working Example They Provided

They gave this pattern for OpenAI (needs adaptation for Kimi):
```python
# Simple streaming
for chunk in client.chat.completions.create(messages=messages, stream=True):
    token = chunk.choices[0].delta.content or ""
    answer += token
    placeholder.markdown(f'{answer}▌', unsafe_allow_html=True)
```

## The Ask for Gemini

**Can you provide a SIMPLE implementation that:**

1. **For Simple Questions**: 
   - Direct streaming from Kimi API
   - Show thinking box if response contains thinking markers
   - Stream the answer with typing cursor

2. **For Research Questions**:
   - Use the existing `InterviewResearchAgent.autonomous_research()` 
   - Show a progress bar based on iterations
   - Display the research steps in a thinking box
   - Stream the final response

3. **Key Constraints**:
   - Must use Moonshot/Kimi API (OpenAI-compatible but not OpenAI)
   - Must work with existing agent (can't rewrite the whole backend)
   - Should be SIMPLE - no complex abstractions
   - Streamlit-based UI

**Current Mess to Replace**:
- `/search-mvp/web_demo/pages/0_🔬_Research_Agent.py` (395 lines)
- `/search-mvp/web_demo/utils/streaming_client.py` (244 lines)

**Desired Outcome**:
- One clean file under 300 lines that just works
- Uses the existing agent for research
- Provides smooth streaming UI
- No over-engineering

Can you help create a clean, simple implementation that actually works?

## Additional Context

The agent already works fine - it's the UI streaming that's the problem. The agent:
- Takes a question
- Runs multiple iterations 
- Returns a final response
- We just need to show this process nicely in the UI

The Kimi API supports streaming via the OpenAI client library:
```python
from openai import OpenAI
client = OpenAI(base_url="https://api.moonshot.ai/v1", api_key=os.getenv("MOONSHOT_API_KEY"))
response = client.chat.completions.create(
    model="kimi-k2-0711-preview",
    messages=messages,
    stream=True
)
```

Please help us simplify this into something that actually works!