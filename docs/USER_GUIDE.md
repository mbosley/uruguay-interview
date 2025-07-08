# User Guide & Setup

*Practical instructions for setting up, configuring, and using the Uruguay Interview Analysis system.*

---

## Quick Start

### 1. System Requirements
- Python 3.11+
- PostgreSQL database
- API keys for AI providers (OpenAI/Anthropic)

### 2. Installation
```bash
git clone [repository]
pip install -r requirements.txt
```

### 3. Configuration
Edit `settings.yaml`:
```yaml
database:
  url: "postgresql://user:password@localhost:5432/uruguay_interviews"
ai:
  provider: "openai"  # or "anthropic"
  model: "gpt-4o-mini"
```

### 4. Database Setup
```bash
python scripts/init_database.py
```

### 5. Run Pipeline
```bash
# Process interviews
python -m src.pipeline.full_pipeline

# Launch dashboard
python scripts/run_dashboard.py
```

---

## Current System Capabilities (as of 2025-06-16)

### Pipeline Processing
- **Input**: Interview files (.txt, .docx) in `data/processed/interviews_txt/`
- **Processing**: Document ingestion → AI annotation → Data extraction → Conversation parsing → Database storage
- **Output**: Structured interview data with conversation turns

### Dashboard Features
- **Overview**: Key metrics, sentiment distribution, geographic analysis
- **Priorities**: National/local priority analysis with filtering
- **Themes**: Theme exploration and co-occurrence analysis  
- **Interview Detail**: Individual interview exploration with conversation flow
- **Conversation Flow**: Turn-by-turn dialogue visualization

### Testing & Validation
```bash
# Run pipeline verification
python run_tests.py pipeline

# Run specific test types
python run_tests.py unit
python run_tests.py integration
```

### Data Structure
The system processes:
- **37 interviews** from Uruguay consultation (May 28-29, 2025)
- **Multi-speaker conversations** with automatic speaker identification
- **Qualitative annotations** (priorities, themes, emotions)
- **Conversation turns** for digital twin research

---

## Configuration Options

### AI Provider Setup
```yaml
# OpenAI
ai:
  provider: "openai"
  model: "gpt-4o-mini"
  api_key: "${OPENAI_API_KEY}"

# Anthropic  
ai:
  provider: "anthropic"
  model: "claude-3-sonnet"
  api_key: "${ANTHROPIC_API_KEY}"
```

### Database Configuration
```yaml
database:
  url: "postgresql://user:pass@host:port/db"
  # or for SQLite testing:
  url: "sqlite:///test.db"
```

### Processing Settings
```yaml
pipeline:
  batch_size: 10
  max_workers: 4
  confidence_threshold: 0.85
```

---

## Troubleshooting

### Common Issues
1. **Database Connection**: Verify PostgreSQL is running and credentials are correct
2. **API Limits**: Check AI provider API key and rate limits
3. **File Processing**: Ensure interview files are in correct format and location
4. **Dashboard Loading**: Check database contains processed interview data

### Validation Steps
```bash
# Check database connectivity
python -c "from src.database.connection import get_database_connection; print('OK')"

# Verify conversation parsing
python tests/unit/test_conversation_parser.py

# Test pipeline components
python run_tests.py pipeline
```

### Performance Notes
- Processing ~50 interviews takes approximately 10-15 minutes
- Dashboard loads data from cache (5-minute refresh)
- Conversation parsing adds ~2-3 seconds per interview

---

## Usage Patterns

### For Researchers
1. Process interviews through pipeline
2. Explore results in dashboard overview
3. Analyze conversation flows for specific interviews
4. Export data for statistical analysis

### For Developers
1. Run tests before making changes: `python run_tests.py pipeline`
2. Update documentation when adding features
3. Follow git commit standards in CLAUDE.md
4. Use modular pipeline components for testing

### For System Administrators
1. Monitor database storage and performance
2. Manage API usage and costs
3. Backup processed data regularly
4. Update dependencies and security patches

---

## [Future usage updates and configuration changes will be added here]

---