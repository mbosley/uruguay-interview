#!/usr/bin/env python3
"""
Convenience wrapper to run the interview research agent with Groq provider
"""

import sys
import subprocess

if __name__ == "__main__":
    # Simply forward to the main agent with --provider=groq
    cmd = ["python", "interview_research_agent_improved.py", "--provider=groq"] + sys.argv[1:]
    subprocess.run(cmd)