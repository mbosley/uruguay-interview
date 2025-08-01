#!/usr/bin/env python3
"""
Simple wrapper to run the research agent from command line
"""

import sys
import asyncio
import os

# Change to parent directory so relative paths work
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.research_agent import InterviewResearchAgent
from src.agent.config import AgentConfig

async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", required=True, help="Research question")
    parser.add_argument("--provider", default="moonshot", help="LLM provider")
    parser.add_argument("--max-iterations", type=int, default=15, help="Max iterations")
    args = parser.parse_args()
    
    # Create config
    config = AgentConfig(
        provider=args.provider,
        max_iterations=args.max_iterations,
        research_mode=False,
        debug=False,
        width=80
    )
    
    # Create and run agent
    agent = InterviewResearchAgent(config)
    results = await agent.research(args.question, max_iterations=args.max_iterations)
    
    # The output is already printed by the logger
    # Just exit cleanly
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))