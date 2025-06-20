#!/usr/bin/env python3
"""
Quick launcher for the chat interface
"""
import subprocess
import sys
from pathlib import Path

def main():
    """Launch the chat interface."""
    print("🚀 Launching Uruguay Holistic Chat Interface...")
    print("=" * 50)
    print("📊 Comprehensive interview analysis with narrative features")
    print("💬 View citizen consultation interviews as natural conversations")
    print("🔍 Rich qualitative analysis prominently featured")
    print("📱 Mobile-friendly chat design with holistic insights")
    print("=" * 50)
    
    # Run the interactive chat interface
    app_path = Path(__file__).parent / "src" / "dashboard" / "interactive_chat_interface.py"
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            str(app_path),
            "--server.port", "8508",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Chat interface stopped.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()