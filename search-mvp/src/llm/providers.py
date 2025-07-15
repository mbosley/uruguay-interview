#!/usr/bin/env python3
"""
Model-agnostic LLM providers for interview processing
Supports OpenAI, Kimi/Moonshot, and Google Gemini
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text completion"""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Get the model identifier"""
        pass

class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider"""
    
    def __init__(self, model="gpt-4o", api_key=None):
        self.model = model
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
    
    def generate(self, prompt: str, temperature=0.7, max_tokens=4096, **kwargs) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    
    def get_model_name(self) -> str:
        return f"openai-{self.model}"

class KimiProvider(LLMProvider):
    """Kimi/Moonshot provider"""
    
    def __init__(self, model="kimi-k2-0711-preview", api_key=None):
        self.model = model
        self.client = OpenAI(
            api_key=api_key or os.getenv("MOONSHOT_API_KEY"),
            base_url="https://api.moonshot.ai/v1"
        )
    
    def generate(self, prompt: str, temperature=0.7, max_tokens=4096, **kwargs) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    
    def get_model_name(self) -> str:
        return f"kimi-{self.model}"

class GeminiProvider(LLMProvider):
    """Google Gemini provider"""
    
    def __init__(self, model="gemini-1.5-flash", api_key=None):
        self.model = model
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key or os.getenv("GOOGLE_API_KEY"))
            self.client = genai.GenerativeModel(model)
        except ImportError:
            raise ImportError("google-generativeai package required for Gemini. Install with: pip install google-generativeai")
    
    def generate(self, prompt: str, temperature=0.7, max_tokens=4096, **kwargs) -> str:
        try:
            # Configure generation parameters
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }
            
            response = self.client.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            return response.text
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise
    
    def get_model_name(self) -> str:
        return f"gemini-{self.model}"

def create_provider(provider_type: str, model: str = None, **kwargs) -> LLMProvider:
    """Factory function to create LLM providers"""
    
    provider_type = provider_type.lower()
    
    if provider_type == "openai":
        return OpenAIProvider(model=model or "gpt-4o", **kwargs)
    
    elif provider_type == "kimi" or provider_type == "moonshot":
        return KimiProvider(model=model or "kimi-k2-0711-preview", **kwargs)
    
    elif provider_type == "gemini":
        return GeminiProvider(model=model or "gemini-1.5-flash", **kwargs)
    
    else:
        raise ValueError(f"Unknown provider type: {provider_type}. Supported: openai, kimi, gemini")

# Convenience functions
def get_default_provider() -> LLMProvider:
    """Get default provider (Kimi)"""
    return KimiProvider()

def get_fast_provider() -> LLMProvider:
    """Get fastest provider for quick tasks"""
    try:
        return GeminiProvider(model="gemini-1.5-flash")
    except ImportError:
        return OpenAIProvider(model="gpt-4o-mini")

def get_powerful_provider() -> LLMProvider:
    """Get most capable provider for complex tasks"""
    try:
        return GeminiProvider(model="gemini-1.5-pro")
    except ImportError:
        return OpenAIProvider(model="gpt-4o")