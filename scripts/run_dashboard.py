#!/usr/bin/env python3
"""
Launch the Uruguay Interview Analysis Dashboard
"""
import subprocess
import sys
from pathlib import Path

def main():
    """Launch the Streamlit dashboard."""
    # Get the app path
    project_root = Path(__file__).parent.parent
    app_path = project_root / "src" / "dashboard" / "app.py"
    
    if not app_path.exists():
        print(f"Error: Dashboard app not found at {app_path}")
        sys.exit(1)
    
    print("🚀 Launching Uruguay Interview Analysis Dashboard...")
    print("=" * 60)
    print("The dashboard will open in your default web browser.")
    print("To stop the dashboard, press Ctrl+C in this terminal.")
    print("=" * 60)
    
    # Run streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            str(app_path),
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped.")
    except Exception as e:
        print(f"Error launching dashboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()