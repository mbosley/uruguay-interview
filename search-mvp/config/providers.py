"""
LLM Provider Configuration
Supports multiple providers with consistent interface
"""

import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class ProviderConfig:
    """Configuration for an LLM provider"""
    name: str
    base_url: str
    api_key_env: str
    model_name: str
    description: str
    tokens_per_second: Optional[int] = None
    cost_per_1k_input: Optional[float] = None  # Cost per 1000 input tokens in USD
    cost_per_1k_output: Optional[float] = None  # Cost per 1000 output tokens in USD

# Provider configurations
PROVIDERS = {
    "moonshot": ProviderConfig(
        name="moonshot",
        base_url="https://api.moonshot.ai/v1",
        api_key_env="MOONSHOT_API_KEY",
        model_name="kimi-k2-0711-preview",
        description="Moonshot AI hosting",
        tokens_per_second=30,
        cost_per_1k_input=0.0006,   # $0.60 per million = $0.0006 per 1k tokens
        cost_per_1k_output=0.0025   # $2.50 per million = $0.0025 per 1k tokens
    ),
    "groq": ProviderConfig(
        name="groq",
        base_url="https://api.groq.com/openai/v1",
        api_key_env="GROQ_API_KEY",
        model_name="moonshotai/kimi-k2-instruct",
        description="Groq hosting (ultra-fast)",
        tokens_per_second=185,
        cost_per_1k_input=0.001,  # $1 per million = $0.001 per 1k tokens
        cost_per_1k_output=0.003  # $3 per million = $0.003 per 1k tokens
    ),
    # Easy to add more providers
    # "together": ProviderConfig(
    #     name="together",
    #     base_url="https://api.together.xyz/v1",
    #     api_key_env="TOGETHER_API_KEY",
    #     model_name="moonshotai/kimi-k2",
    #     description="Together AI hosting"
    # ),
}

def get_provider_config(provider_name: str = None) -> ProviderConfig:
    """
    Get provider configuration, with smart fallback
    
    Priority:
    1. Explicitly requested provider
    2. Environment variable KIMI_PROVIDER
    3. First available provider based on API keys
    4. Default to moonshot
    """
    # Check explicit provider
    if provider_name and provider_name in PROVIDERS:
        return PROVIDERS[provider_name]
    
    # Check environment variable
    env_provider = os.getenv("KIMI_PROVIDER")
    if env_provider and env_provider in PROVIDERS:
        return PROVIDERS[env_provider]
    
    # Auto-detect based on available API keys
    # Prefer Groq if available (faster)
    if os.getenv("GROQ_API_KEY"):
        return PROVIDERS["groq"]
    
    # Then check other providers
    for name, config in PROVIDERS.items():
        if os.getenv(config.api_key_env):
            return config
    
    # Default to moonshot
    return PROVIDERS["moonshot"]

def list_providers():
    """List available providers and their status"""
    print("Available LLM Providers:")
    print("=" * 60)
    
    for name, config in PROVIDERS.items():
        api_key_set = "✅" if os.getenv(config.api_key_env) else "❌"
        speed = f"{config.tokens_per_second} tok/s" if config.tokens_per_second else "N/A"
        
        print(f"\n{name}:")
        print(f"  Status: {api_key_set} ({config.api_key_env})")
        print(f"  Model: {config.model_name}")
        print(f"  Speed: {speed}")
        print(f"  Description: {config.description}")
        
        # Show cost information if available
        if hasattr(config, 'cost_per_1k_input') and config.cost_per_1k_input is not None:
            input_cost = config.cost_per_1k_input
            output_cost = config.cost_per_1k_output
            if input_cost == 0 and output_cost == 0:
                print(f"  Cost: Free")
            elif input_cost == output_cost:
                print(f"  Cost: ${input_cost:.4f}/1k tokens")
            else:
                print(f"  Cost: ${input_cost:.4f}/1k in, ${output_cost:.4f}/1k out")
    
    current = get_provider_config()
    print(f"\n🎯 Current provider: {current.name}")
    print(f"   (Set KIMI_PROVIDER env var to change)")

if __name__ == "__main__":
    list_providers()