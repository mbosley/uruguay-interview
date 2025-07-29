#!/usr/bin/env python3
"""
Simple script to list available LLM providers
"""

from dotenv import load_dotenv
from config.providers import list_providers

if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()
    list_providers()