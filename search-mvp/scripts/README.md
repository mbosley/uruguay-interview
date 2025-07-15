# Batch Interview Annotation

This directory contains scripts for processing the Uruguay interview corpus.

## batch_annotate_interviews.py

Automatically generates rich, searchable annotations for interview transcripts using the Kimi/Moonshot API.

### Prerequisites

1. **Moonshot API Key**: Get your API key from [Moonshot AI](https://platform.moonshot.ai/)
2. **Environment Setup**: Set your API key as an environment variable:
   ```bash
   export MOONSHOT_API_KEY=your_api_key_here
   ```

### Usage

```bash
# Test run (no API calls)
python batch_annotate_interviews.py --dry-run

# Process specific interviews
python batch_annotate_interviews.py --interviews 071 072 073

# Process all interviews
python batch_annotate_interviews.py

# Only generate corpus summary
python batch_annotate_interviews.py --summary-only
```

### Output

The script creates annotations in `data/processed/annotations/searchable/`:

- `{interview_id}_annotation.json` - Rich annotation for each interview
- `_corpus_summary.json` - Aggregated statistics across all interviews

### Annotation Schema

Each annotation includes:

- **Tags**: Demographics, themes, emotions, locations, evidence types
- **Thematic Analysis**: 2-4 major themes with detailed analysis
- **Notable Quotes**: Key quotes with turn IDs for citation
- **Conversation Structure**: Flow mapping and patterns
- **Research Value**: Quality assessment and research potential

### Rate Limiting

The script includes 3-second delays between API calls to be respectful to the Moonshot API. Processing all 36 interviews takes approximately 3-5 minutes.

### Error Handling

- **Invalid JSON responses** are wrapped with error metadata
- **API failures** are logged and can be retried
- **Already processed interviews** are automatically skipped
- **Progress tracking** allows for resuming interrupted batches

### Dependencies

- `openai` - For Moonshot API compatibility
- Standard library modules (json, pathlib, argparse, etc.)