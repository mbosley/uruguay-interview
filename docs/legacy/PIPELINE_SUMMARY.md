# Uruguay Interview Analysis Pipeline - Summary

## Overview

We've successfully built a comprehensive end-to-end pipeline for analyzing citizen consultation interviews. The system processes interviews through multiple stages: ingestion → annotation → extraction → database storage → visualization.

## Components Implemented

### 1. Configuration System (`config.yaml`)
- Centralized configuration for all pipeline settings
- Support for multiple AI providers (OpenAI, Anthropic, Google Gemini)
- Environment variable overrides
- Cost management and budget controls

### 2. Document Ingestion (`src/pipeline/ingestion/`)
- Supports TXT, DOCX, and ODT formats
- Extracts metadata from filenames
- Validates interview content
- Handles both single files and batch processing

### 3. AI Annotation Engine (`src/pipeline/annotation/`)
- XML-based annotation using existing schema
- Support for three AI providers:
  - **Google Gemini** (default) - $0.000875/interview
  - **OpenAI GPT-4** models - from $0.000875/interview
  - **Anthropic Claude** - $0.1613/interview
- Retry logic and error handling
- Quality validation

### 4. Data Extraction (`src/pipeline/extraction/`)
- Parses XML annotations into structured data
- Extracts:
  - National and local priorities
  - Emotions and sentiment
  - Themes and concerns
  - Geographic mentions
  - Demographic indicators
- Calculates quality metrics

### 5. Database Integration (`src/database/`)
- PostgreSQL database with SQLAlchemy ORM
- Comprehensive schema for all data types
- Repository pattern for clean data access
- Daily summary aggregations
- Full audit trail

### 6. Command-Line Interface (`src/cli/annotate.py`)
- Complete CLI for all operations
- Available commands:
  - `info` - Show configuration
  - `annotate` - Process single interview
  - `batch` - Process multiple interviews
  - `pipeline` - Run full pipeline on single file
  - `pipeline-batch` - Run full pipeline on directory
  - `costs` - Compare provider costs
  - `init-db` - Initialize database
  - `db-status` - Check database statistics

## Usage Examples

### Basic Pipeline Usage

```bash
# Show current configuration
python -m src.cli.annotate info

# Initialize database
python -m src.cli.annotate init-db

# Process a single interview through full pipeline
python -m src.cli.annotate pipeline data/processed/interviews_txt/20250528_0900_058.txt

# Process batch with cost check
python -m src.cli.annotate pipeline-batch --limit 10

# Process without saving to database (dry run)
python -m src.cli.annotate pipeline interview.txt --no-save-db
```

### Cost Comparison

```bash
# Compare all providers
python -m src.cli.annotate costs

# Current configuration (Gemini 2.0 Flash):
# - Cost per interview: $0.000875
# - Cost for 5,000 interviews: $4.38
```

### Configuration Override

```bash
# Use different AI provider
export AI_PROVIDER=openai
export AI_MODEL=gpt-4o-mini

# Or via command line
python -m src.cli.annotate annotate interview.txt --provider openai --model gpt-4o-mini
```

## Pipeline Flow

```
1. Document Ingestion
   ├── Read file (TXT/DOCX/ODT)
   ├── Extract metadata
   └── Validate content

2. AI Annotation
   ├── Create XML prompt with interview
   ├── Call AI API (Gemini/OpenAI/Anthropic)
   ├── Validate XML response
   └── Retry on errors

3. Data Extraction
   ├── Parse XML annotation
   ├── Extract priorities, themes, emotions
   ├── Calculate quality metrics
   └── Structure for database

4. Database Storage
   ├── Save interview record
   ├── Save annotation with XML
   ├── Save extracted entities
   └── Update daily summaries

5. Output Generation
   ├── XML annotation files
   ├── JSON extracted data
   └── Database records
```

## Key Features

### Two-Layer Architecture
- **Layer 1**: Rich qualitative XML annotations preserving context
- **Layer 2**: Structured quantitative extraction for analysis

### Quality Assurance
- Confidence scoring for all annotations
- Validation of XML against schema
- Completeness metrics
- Error tracking and retry logic

### Cost Optimization
- Default to cheapest provider (Gemini 2.0 Flash)
- Budget limits and warnings
- Cost estimation before processing
- ~$4.38 for 5,000 interviews

### Scalability
- Batch processing capabilities
- Database connection pooling
- Configurable concurrency
- Progress tracking

## Database Schema

Key tables:
- `interviews` - Core interview records
- `annotations` - AI-generated annotations with XML
- `priorities` - National and local priorities
- `emotions` - Emotional expressions
- `themes` - Discussion themes
- `concerns` - Citizen concerns
- `suggestions` - Policy suggestions
- `daily_summaries` - Aggregated statistics

## Next Steps

1. **Dashboard Development** (src/dashboards/)
   - Executive dashboard with KPIs
   - Researcher interface for exploration
   - Public dashboard for transparency

2. **WhatsApp Integration** (src/followup/)
   - AI-powered follow-up conversations
   - Automated engagement system

3. **Advanced Analytics** (src/analysis/)
   - Trend detection
   - Geographic clustering
   - Demographic analysis

4. **Quality Improvements**
   - Active learning for better annotations
   - Human-in-the-loop validation
   - Cross-reference validation

## Testing

Run tests with:
```bash
pytest tests/test_pipeline_integration.py -v
```

The pipeline includes comprehensive error handling and logging throughout.