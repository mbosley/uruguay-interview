# LLM Provider Configuration

The research agent now supports multiple LLM providers through a flexible configuration system. This allows you to easily switch between different hosting options for Kimi K2 based on your needs.

## Available Providers

### Moonshot (Default)
- **Speed**: ~30 tokens/second
- **API Key**: `MOONSHOT_API_KEY`
- **Model**: `kimi-k2-0711-preview`
- **Description**: Official Moonshot AI hosting
- **Best for**: Standard research tasks, reliable service

### Groq (Ultra-fast)
- **Speed**: ~185 tokens/second (6x faster!)
- **API Key**: `GROQ_API_KEY`
- **Model**: `moonshotai/kimi-k2-instruct`
- **Description**: Groq's LPU-powered hosting
- **Best for**: Time-sensitive research, parallel sub-agents

## Configuration Methods

### 1. Auto-detection (Default)
The system automatically detects which provider to use based on available API keys:
```bash
export MOONSHOT_API_KEY="your-key"  # Will use Moonshot
export GROQ_API_KEY="your-key"      # Will use Groq (if both set, Moonshot takes precedence)
```

### 2. Environment Variable
Set the `KIMI_PROVIDER` environment variable:
```bash
export KIMI_PROVIDER=groq
make run-agent QUESTION="your research question"
```

### 3. Command Line Flag
Specify provider directly when running:
```bash
# Direct invocation
python interview_research_agent_improved.py --provider=groq "your question"

# Using make
make run-agent PROVIDER=groq QUESTION="your question"
```

### 4. Programmatic
When using the agent in Python code:
```python
from interview_research_agent_improved import InterviewResearchAgent

agent = InterviewResearchAgent(
    provider="groq",  # or "moonshot"
    verbose=True
)
```

## Setting Up Providers

### Moonshot Setup
1. Get your API key from [Moonshot Platform](https://platform.moonshot.cn/)
2. Set the environment variable:
   ```bash
   export MOONSHOT_API_KEY="your-key-here"
   ```

### Groq Setup
1. Get your API key from [Groq Console](https://console.groq.com/)
2. Set the environment variable:
   ```bash
   export GROQ_API_KEY="your-key-here"
   ```

## Performance Comparison

| Provider | Speed | Best Use Case |
|----------|-------|---------------|
| Moonshot | 30 tok/s | Standard research, reliable service |
| Groq | 185 tok/s | Fast iteration, parallel sub-agents |

When using parallel sub-agents, Groq's speed advantage becomes even more pronounced, as multiple agents can complete their research much faster.

## Examples

### Fast Research with Groq
```bash
# Single question
make run-agent PROVIDER=groq QUESTION="What are the main healthcare concerns?"

# Research mode with detailed logging
python interview_research_agent_improved.py --provider=groq --research "education challenges"
```

### Parallel Sub-agent Research
```bash
# Groq is ideal for parallel research tasks
python test_parallel_research.py  # Will use provider based on env/auto-detection
```

### Checking Available Providers
```bash
# List all providers and their status
python list_providers.py
```

Output:
```
Available LLM Providers:
============================================================

moonshot:
  Status: ✅ (MOONSHOT_API_KEY)
  Model: kimi-k2-0711-preview
  Speed: 30 tok/s
  Description: Moonshot AI hosting

groq:
  Status: ✅ (GROQ_API_KEY)
  Model: moonshotai/kimi-k2-instruct
  Speed: 185 tok/s
  Description: Groq hosting (ultra-fast)

🎯 Current provider: groq
   (Set KIMI_PROVIDER env var to change)
```

## Adding New Providers

To add a new provider, edit `config/providers.py`:

```python
PROVIDERS = {
    "moonshot": ProviderConfig(...),
    "groq": ProviderConfig(...),
    "your_provider": ProviderConfig(
        name="your_provider",
        base_url="https://api.yourprovider.com/v1",
        api_key_env="YOUR_PROVIDER_API_KEY",
        model_name="model-name-at-provider",
        description="Your provider description",
        tokens_per_second=100  # Optional
    ),
}
```

The system will automatically detect and use the new provider based on API key availability.

## Troubleshooting

### Provider not found
If you see "Provider not found", check:
1. The provider name is spelled correctly
2. The provider is defined in `config/providers.py`

### API key not found
If you see "API_KEY not found", ensure:
1. The environment variable is set correctly
2. You've reloaded your shell/terminal after setting it
3. The key name matches what's in the provider config

### Slow performance with Groq
If Groq isn't performing as expected:
1. Check your API rate limits
2. Ensure you're using the correct model name
3. Verify network connectivity to Groq's servers