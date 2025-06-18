# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a qualitative research project analyzing citizen consultation interviews from Uruguay conducted on May 28-29, 2025. The project focuses on understanding citizen perspectives on national and local priorities through systematic interview analysis.

## Project Structure

- `data/raw/interviews/` - Contains 37 interview transcripts (.docx and .odt files) following the naming pattern: `T - [DATE] [TIME] [ID].[ext]`
- `prompt/annotation-prompt-en.xml` - Comprehensive XML schema defining the annotation framework for qualitative analysis

## Research Focus

The annotation schema indicates this project analyzes:
- National and local priorities as perceived by citizens
- Issues including security, education, healthcare, and community concerns
- Emotional content and narrative features in citizen discourse
- Evidence types and argumentation patterns

## Working with Interview Data

When processing interview files:
- Preserve the original file naming convention
- Handle both .docx and .odt formats
- Note that one file (T- 20250528 1015 59.docx) has a slightly different naming format

## Annotation Framework

The `annotation-prompt-en.xml` file contains:
- Detailed coding instructions for qualitative researchers
- Multi-level analysis structure (interview-level and turn-level)
- Guidelines for capturing priorities, emotions, evidence types, and narratives
- Best practices for consistent annotation across interviews

## Git Workflow & Best Practices

### Commit Message Standards
Follow conventional commit format for clear project history:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature or functionality
- `fix`: Bug fixes
- `docs`: Documentation changes
- `data`: Data processing or analysis updates
- `refactor`: Code restructuring without functionality changes
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(annotation): add automated interview processing pipeline
docs(roadmap): update training framework with validation protocols  
data(processing): convert interviews from Word to plain text
fix(schema): correct priority ranking validation logic
```

### Branch Strategy
- `main`: Production-ready code and documentation
- `develop`: Integration branch for ongoing work
- `feature/description`: New features or major changes
- `hotfix/description`: Critical fixes

### Sensitive Data Handling
- **NEVER commit** raw interview files or participant data
- Use `.gitignore` to exclude sensitive directories:
  ```
  data/raw/
  data/processed/interviews_txt/
  data/processed/annotations/
  *.docx
  *.odt
  ```
- Commit only schemas, scripts, and documentation
- Use placeholder data for examples

### Recommended Workflow
1. Always check status before committing: `git status`
2. Stage specific files: `git add filename` (avoid `git add .`)
3. Review changes: `git diff --staged`
4. Commit with descriptive message
5. Push to appropriate branch

## Documentation Maintenance Guidelines

### Documentation Organization
- **ALWAYS place new documentation in the `docs/` directory**
- **Use timestamped log entries** in the main log files rather than creating new files
- **Four main log files**: USER_GUIDE.md, TECHNICAL_LOG.md, RESEARCH_LOG.md, PROJECT_LOG.md
- **Add timestamped sections** (YYYY-MM-DD HH:MM format) when making significant updates
- Legacy files moved to `docs/legacy/` and `docs/roadmap/` directories

### Documentation Standards
- Use GitHub-flavored Markdown format
- Include clear headers and table of contents for longer documents
- Add cross-references between related documents
- Keep documentation up-to-date with code changes
- Include practical examples and usage instructions

### When Adding Documentation
1. **Choose appropriate log file**:
   - Setup/usage info → `USER_GUIDE.md`
   - Technical implementation → `TECHNICAL_LOG.md`
   - Research methodology/findings → `RESEARCH_LOG.md`
   - Project planning/decisions → `PROJECT_LOG.md`

2. **Add timestamped entry**:
   - Use format: `## YYYY-MM-DD HH:MM - Brief Description`
   - Include relevant technical details, decisions, or findings
   - Reference previous entries when building on earlier work

3. **Update existing entries**:
   - Update USER_GUIDE.md when configuration changes
   - Add to TECHNICAL_LOG.md when implementing new features
   - Document research findings in RESEARCH_LOG.md as analysis progresses

### Documentation Types
- **User Documentation**: How to use features (guides, tutorials)
- **Technical Documentation**: Implementation details, architecture
- **Process Documentation**: Workflows, standards, procedures
- **Research Documentation**: Findings, analysis, methodology
- **Reference Documentation**: API docs, configuration options

### Maintenance Responsibilities
- Update documentation when making code changes
- Review and refresh documentation quarterly
- Remove outdated information promptly
- Ensure all links work and references are accurate
- Keep the documentation index current

## Important Notes

- This is a research project, not a software development project
- Testing framework available via `python run_tests.py pipeline` (see `docs/TECHNICAL_LOG.md`)
- Focus on data analysis and qualitative research methods when assisting
- Respect the sensitivity of interview data and maintain participant confidentiality
- Follow git best practices to maintain clear project history
- **Always update documentation** when making significant changes