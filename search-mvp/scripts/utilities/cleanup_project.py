#!/usr/bin/env python3
"""
Clean up and organize the search-mvp directory
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def create_directory_structure():
    """Create organized directory structure"""
    directories = [
        "tests/unit",
        "tests/integration", 
        "tests/fixtures",
        "scripts/analysis",
        "scripts/utilities",
        "archived/old_versions",
        "archived/experiments"
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created/verified: {dir_path}")

def organize_test_files():
    """Move test files to tests directory"""
    test_files = [
        ("test_*.py", "tests/unit"),
        ("test_frontend_trace.md", "tests"),
        ("demo_*.md", "tests/fixtures"),
    ]
    
    for pattern, destination in test_files:
        files = list(Path(".").glob(pattern))
        for file in files:
            if file.is_file():
                dest_path = Path(destination) / file.name
                print(f"📁 Moving {file} → {dest_path}")
                shutil.move(str(file), str(dest_path))

def organize_agent_files():
    """Organize agent implementations"""
    # Keep only the main agents in root
    agent_versions = {
        "interview_research_agent.py": "archived/old_versions/interview_research_agent_v1.py",
        "interview_research_agent_web.py": "archived/experiments/",
        "interview_research_agent_groq.py": "archived/experiments/",
    }
    
    for source, dest in agent_versions.items():
        if Path(source).exists():
            if dest.endswith("/"):
                dest_path = Path(dest) / source
            else:
                dest_path = Path(dest)
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            print(f"📦 Archiving {source} → {dest_path}")
            shutil.move(source, str(dest_path))

def organize_utility_scripts():
    """Move utility scripts to appropriate directories"""
    utilities = [
        ("compare_providers.py", "scripts/utilities/"),
        ("list_providers.py", "scripts/utilities/"),
        ("create_html_report.py", "scripts/analysis/"),
        ("create_interactive_report.py", "scripts/analysis/"),
        ("consolidate_themes.py", "scripts/analysis/"),
        ("parallel_execution_enhancement.py", "scripts/utilities/"),
    ]
    
    for script, dest_dir in utilities:
        if Path(script).exists():
            dest_path = Path(dest_dir) / script
            print(f"🔧 Moving {script} → {dest_path}")
            shutil.move(script, str(dest_path))

def create_readme():
    """Create README with project structure"""
    readme_content = """# Uruguay Interview Research - Search MVP

## Project Structure

```
search-mvp/
├── api_server.py              # FastAPI server with WebSocket support
├── interview_research_agent_improved.py  # Main research agent
├── interview_research_tools.py          # Tool definitions
├── mock_research_agent.py     # Mock agent for testing
├── unified_logger.py          # Unified logging server
├── config/                    # Configuration files
│   └── providers.py          # LLM provider configurations
├── docs/                      # Documentation
├── logs/                      # Application logs
├── results/                   # Research results
├── scripts/                   # Utility scripts
│   ├── analysis/             # Data analysis scripts
│   └── utilities/            # Helper utilities
├── src/                       # Source code modules
│   ├── cli/                  # CLI interfaces
│   └── tools/                # Tool implementations
├── tests/                     # Test files
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   └── fixtures/             # Test data
├── unified_logs/              # Unified frontend/backend logs
├── uruguay-research-ui/       # React frontend
└── web_demo/                  # Streamlit demo app
```

## Quick Start

1. **Start the API server:**
   ```bash
   source venv/bin/activate
   python api_server.py
   ```

2. **Start the React frontend:**
   ```bash
   cd uruguay-research-ui
   npm start
   ```

3. **Start unified logging (optional):**
   ```bash
   python unified_logger.py
   ```

## Main Components

- **API Server** (`api_server.py`): FastAPI server providing research endpoints and WebSocket streaming
- **Research Agent** (`interview_research_agent_improved.py`): Core agent that analyzes interviews
- **Frontend** (`uruguay-research-ui/`): React app with real-time research visualization
- **Mock Agent** (`mock_research_agent.py`): For testing frontend without LLM calls

## Testing

Run the event contract test to verify frontend/backend compatibility:
```bash
python tests/unit/test_event_contract.py
```

View unified logs:
```bash
python view_unified_logs.py
```
"""
    
    with open("README_PROJECT.md", "w") as f:
        f.write(readme_content)
    print("📝 Created README_PROJECT.md")

def cleanup_cache_and_temp():
    """Remove cache and temporary files"""
    patterns = [
        "__pycache__",
        "*.pyc",
        ".DS_Store",
        "*.log",
        ".pytest_cache"
    ]
    
    for pattern in patterns:
        for path in Path(".").rglob(pattern):
            if path.is_file():
                path.unlink()
                print(f"🗑️  Removed file: {path}")
            elif path.is_dir():
                shutil.rmtree(path)
                print(f"🗑️  Removed directory: {path}")

def create_gitignore():
    """Create comprehensive .gitignore"""
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv

# Logs
*.log
logs/
unified_logs/

# Results and data
results/
scratchpads/
data/raw/
data/processed/

# IDEs
.vscode/
.idea/
*.swp
*.swo
.DS_Store

# Dependencies
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Build
build/
dist/
*.egg-info/

# Environment
.env
.env.local
.env.*.local

# Testing
.pytest_cache/
coverage/
.coverage
htmlcov/

# Temporary
*.tmp
*.temp
*.bak
"""
    
    with open(".gitignore", "w") as f:
        f.write(gitignore_content)
    print("📝 Created/updated .gitignore")

def main():
    """Run all cleanup tasks"""
    print("🧹 Starting project cleanup...")
    print("=" * 50)
    
    # Create directory structure
    print("\n📁 Creating directory structure...")
    create_directory_structure()
    
    # Organize files
    print("\n📂 Organizing test files...")
    organize_test_files()
    
    print("\n📦 Organizing agent files...")
    organize_agent_files()
    
    print("\n🔧 Organizing utility scripts...")
    organize_utility_scripts()
    
    # Create documentation
    print("\n📝 Creating documentation...")
    create_readme()
    create_gitignore()
    
    # Clean cache (optional - ask user)
    try:
        response = input("\n🗑️  Remove cache and temporary files? (y/N): ")
        if response.lower() == 'y':
            cleanup_cache_and_temp()
    except EOFError:
        print("\n⏭️  Skipping cache cleanup (non-interactive mode)")
    
    print("\n✨ Cleanup complete!")
    print("\nNext steps:")
    print("1. Review the changes")
    print("2. Update any import paths in your code")
    print("3. Commit the organized structure")

if __name__ == "__main__":
    main()