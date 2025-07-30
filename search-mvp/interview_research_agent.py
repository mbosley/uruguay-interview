#!/usr/bin/env python3
"""
Interview Research Agent - Main Entry Point

This is the primary entry point for the interview research agent.
It parses command-line arguments and initiates the research process.
"""

import argparse
import asyncio
import json
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.agent.config import AgentConfig, get_session_id
from src.agent.research_agent import InterviewResearchAgent


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Interview Research Agent - Analyzes interview data to answer research questions'
    )
    
    # Required arguments
    parser.add_argument(
        'research_question',
        type=str,
        help='The research question to explore'
    )
    
    # Optional arguments
    parser.add_argument(
        '--max-iterations',
        type=int,
        default=30,
        help='Maximum number of iterations (default: 30)'
    )
    
    parser.add_argument(
        '--provider',
        type=str,
        choices=['openai', 'groq', 'deepseek', 'together', 'openrouter', 'moonshot'],
        help='LLM provider to use (if not specified, uses environment default)'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        help='Model to use (if not specified, uses provider default)'
    )
    
    parser.add_argument(
        '--research',
        action='store_true',
        help='Enable research mode (shows scratchpad and additional logging)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging for troubleshooting'
    )
    
    parser.add_argument(
        '--width',
        type=int,
        default=80,
        help='Maximum output width (default: 80 characters)'
    )
    
    parser.add_argument(
        '--session-id',
        type=str,
        help='Session ID for tracking (auto-generated if not provided)'
    )
    
    # Sub-agent arguments (not typically used directly)
    parser.add_argument(
        '--sub-agent',
        action='store_true',
        help=argparse.SUPPRESS  # Hidden argument for sub-agents
    )
    
    parser.add_argument(
        '--depth',
        type=int,
        default=0,
        help=argparse.SUPPRESS  # Hidden argument for sub-agents
    )
    
    parser.add_argument(
        '--parent',
        type=str,
        help=argparse.SUPPRESS  # Hidden argument for sub-agents
    )
    
    parser.add_argument(
        '--max-depth',
        type=int,
        default=2,
        help=argparse.SUPPRESS  # Hidden argument for sub-agents
    )
    
    parser.add_argument(
        '--enable-sub-agents',
        action='store_true',
        help='Enable delegation to sub-agents (experimental feature)'
    )
    
    return parser.parse_args()


async def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Create configuration
    config = AgentConfig.from_args(args)
    
    # Create agent
    agent = InterviewResearchAgent(config)
    
    try:
        # Conduct research
        results = await agent.research(
            args.research_question,
            args.max_iterations
        )
        
        # For sub-agents, return JSON to parent
        if config.is_sub_agent:
            from src.agent.report_generator import ReportGenerator
            generator = ReportGenerator()
            formatted_results = generator.format_sub_agent_results(results)
            print(json.dumps(formatted_results, ensure_ascii=False))
        else:
            # For main agent, the report has already been streamed to output
            # No need to print it again
            pass
            
    except KeyboardInterrupt:
        print("\nResearch interrupted by user")
        return 1
    except Exception as e:
        import traceback
        if config.is_sub_agent:
            # Return error as JSON for parent
            print(json.dumps({
                "error": str(e),
                "traceback": traceback.format_exc()
            }))
        else:
            print(f"\nError: {e}")
            if config.research_mode:
                traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    # Run the async main function
    exit_code = asyncio.run(main())
    exit(exit_code)