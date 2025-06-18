# Uruguay Interview Project Documentation

## Overview

This directory contains comprehensive documentation for the Uruguay Active Listening project, a qualitative research initiative analyzing citizen consultation interviews.

## Core Documentation (Living Logs)

### Primary Documents
- **[USER_GUIDE.md](USER_GUIDE.md)** - Setup, configuration, and usage instructions
- **[TECHNICAL_LOG.md](TECHNICAL_LOG.md)** - Technical implementation, architecture, and development history
- **[RESEARCH_LOG.md](RESEARCH_LOG.md)** - Research methodology, findings, and analytical approaches  
- **[PROJECT_LOG.md](PROJECT_LOG.md)** - Project planning, roadmap updates, and strategic decisions

### Legacy Documentation
- [legacy/](legacy/) - Archived standalone documentation files
- [roadmap/](roadmap/) - Historical project roadmaps and planning documents
- [technical/](technical/) - Archived technical implementation guides

## Quick Start

### For New Users
1. **Setup**: Follow [USER_GUIDE.md](USER_GUIDE.md)
2. **Understanding**: Review latest entries in [TECHNICAL_LOG.md](TECHNICAL_LOG.md)
3. **Research Context**: Check [RESEARCH_LOG.md](RESEARCH_LOG.md)

### For Developers
1. **Current Status**: Latest entry in [TECHNICAL_LOG.md](TECHNICAL_LOG.md)
2. **Testing**: Run `python run_tests.py pipeline`
3. **Implementation**: See technical log for architecture decisions

### For Researchers
1. **Project Status**: Latest entry in [PROJECT_LOG.md](PROJECT_LOG.md)
2. **Methodology**: Review [RESEARCH_LOG.md](RESEARCH_LOG.md)
3. **Findings**: Check research log for analysis results

## Documentation Standards

All documentation in this project follows these standards:

- **Markdown Format**: All docs use GitHub-flavored Markdown
- **Clear Structure**: Hierarchical organization with consistent naming
- **Cross-References**: Links between related documents
- **Up-to-Date**: Documentation updated with code changes
- **Practical Focus**: Emphasis on actionable information

## Contributing to Documentation

When adding new documentation:

1. **Place in appropriate subdirectory** based on content type
2. **Update this index** to include new documents
3. **Use clear, descriptive filenames** in UPPER_SNAKE_CASE
4. **Include cross-references** to related documents
5. **Follow existing formatting** and structure patterns

## Project Context

This documentation supports a qualitative research project analyzing 37 citizen consultation interviews from Uruguay (May 28-29, 2025). The system processes interview transcripts through AI annotation to extract priorities, themes, and conversation patterns for research analysis.

Key capabilities documented here:
- Interview document processing and ingestion
- AI-powered qualitative annotation
- Structured data extraction and storage
- Conversation turn parsing for digital twin research
- Interactive dashboard visualization
- Quality assurance and testing frameworks