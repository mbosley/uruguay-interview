# Uruguay Interview Analysis - Repository Structure

## Core Directories

### `/src` - Source Code
- **`/pipeline`** - Data processing pipeline
  - `/annotation` - AI annotation engines (JSON mode, multipass, XML-based)
  - `/ingestion` - Document processing and interview loading
  - `/extraction` - Data extraction from annotations
  - `/parsing` - Interview text parsing
- **`/database`** - Database models and connection management
- **`/dashboard`** - Streamlit dashboard applications
- **`/cli`** - Command-line interface tools
- **`/config`** - Configuration management

### `/data` - Data Storage (git-ignored)
- **`/raw/interviews`** - Original interview files (.docx, .odt)
- **`/processed`** - Processed data
  - `/interviews_txt` - Plain text versions
  - `/annotations/production` - Final annotations
- **`uruguay_interviews.db`** - SQLite database

### `/config` - Configuration Files
- **`/prompts`** - Annotation prompts (XML schemas)
- **`/schemas`** - XSD validation schemas
- **`settings.py`** - Application settings

### `/scripts` - Utility Scripts
- Production annotation scripts
- Database management utilities
- HTML generation tools
- Dashboard launchers

### `/tests` - Test Suite
- **`/unit`** - Unit tests
- **`/integration`** - Integration tests
- **`/e2e`** - End-to-end tests

### `/docs` - Documentation
- **`/technical`** - Technical documentation
- **`/roadmap`** - Project roadmaps
- **`/database`** - Database schema docs
- User guides and research logs

## Key Files

- **`CLAUDE.md`** - Instructions for Claude Code
- **`requirements.txt`** - Python dependencies
- **`config.yaml`** - Main configuration
- **`run_chat.py`** - Launch chat interface
- **`interview_annotations_index.html`** - HTML visualization index

## Workflow

1. **Ingestion**: Raw interviews → Plain text
2. **Annotation**: AI analysis using multipass JSON system
3. **Storage**: Annotations → SQLite database
4. **Visualization**: Dashboard and HTML outputs

## Current State

- ✅ 36 interviews fully annotated
- ✅ Database populated with all annotations
- ✅ Dashboard functional
- ✅ Ready for MFT integration as 6th dimension