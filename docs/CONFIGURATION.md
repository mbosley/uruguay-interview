# Configuration Guide

## Overview

The Uruguay Interview Analysis project uses a centralized configuration system based on YAML files and environment variables. This allows for easy management of settings across different environments and deployment scenarios.

## Configuration File

The main configuration file is `config.yaml` in the project root. It controls all aspects of the pipeline:

### AI Model Configuration

```yaml
ai:
  provider: gemini              # Options: openai, anthropic, gemini
  model: gemini-2.0-flash      # Model-specific options
  temperature: 0.3             # Generation temperature (0-1)
  max_retries: 3               # Retry attempts on failure
  batch_size: 10               # Interviews per batch
  max_concurrent: 1            # Concurrent API calls
```

#### Available Models

**Google Gemini:**
- `gemini-2.0-flash` - Fastest and most cost-effective ($0.000875/interview)
- `gemini-2.5-flash-preview` - Preview with free tier
- `gemini-1.5-pro` - 2M context window for long interviews

**OpenAI:**
- `gpt-4.1-nano` - Cheapest option ($0.000875/interview)
- `gpt-4o-mini` - Balanced performance ($0.001312/interview)
- `gpt-4o` - Full capabilities ($0.021875/interview)

**Anthropic:**
- `claude-3-opus-20240229` - Most capable ($0.1613/interview)
- `claude-3-sonnet-20240229` - Balanced option

### Document Processing

```yaml
processing:
  input_dir: data/raw/interviews
  output_dir: data/processed
  supported_formats: [txt, docx, odt]
  encoding: utf-8
  min_interview_length: 100    # Minimum words
  max_interview_length: 50000  # Maximum words
```

### Annotation Settings

```yaml
annotation:
  prompt_version: v1
  prompt_file: config/prompts/annotation_prompt_v1.xml
  require_all_sections: true
  min_confidence_score: 0.7
  save_xml: true
  save_json: true
  include_metadata: true
```

### Database Configuration

```yaml
database:
  host: localhost
  port: 5432
  name: uruguay_interviews
  user: postgres
  schema: public
  pool_size: 10
  echo: false  # SQL logging
```

### Quality Control

```yaml
quality:
  min_annotation_completeness: 0.8
  flag_low_confidence: true
  review_sample_rate: 0.1  # 10% manual review
  check_factual_consistency: true
  cross_reference_responses: true
```

### Cost Management

```yaml
cost_management:
  daily_limit: 10.0
  monthly_limit: 200.0
  prefer_cached_results: true
  use_cheapest_model: false
  alert_at_percentage: 80
```

## Environment Variables

Environment variables override configuration file settings:

### API Keys (Required)
```bash
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
export GOOGLE_API_KEY="your-key"
```

### Model Overrides (Optional)
```bash
export AI_PROVIDER="gemini"
export AI_MODEL="gemini-2.0-flash"
export AI_TEMPERATURE="0.3"
export AI_MAX_RETRIES="3"
```

### Database
```bash
export DATABASE_URL="postgresql://user:pass@host:5432/db"
```

## Using Configuration in Code

### Loading Configuration

```python
from src.config.config_loader import get_config

# Get global configuration
config = get_config()

# Access settings
provider = config.ai.provider
model = config.ai.model
```

### Annotation Engine with Config

```python
from src.pipeline.annotation.annotation_engine import AnnotationEngine

# Uses configuration automatically
engine = AnnotationEngine()

# Or override specific settings
engine = AnnotationEngine(
    model_provider="openai",
    model_name="gpt-4o-mini"
)
```

### CLI Usage

```bash
# Show current configuration
python -m src.cli.annotate info

# Use custom config file
python -m src.cli.annotate --config my-config.yaml annotate interview.txt

# Override provider/model
python -m src.cli.annotate annotate interview.txt --provider openai --model gpt-4o-mini

# Batch processing with config
python -m src.cli.annotate batch --limit 10

# Show cost comparison
python -m src.cli.annotate costs
```

## Configuration Precedence

Settings are applied in this order (later overrides earlier):

1. Default values in code
2. `config.yaml` file
3. Environment variables
4. Command-line arguments

## Development vs Production

### Development Configuration

```yaml
development:
  debug: true
  test_mode: true
  test_sample_size: 5
  enable_cache: true
```

### Production Configuration

```yaml
development:
  debug: false
  test_mode: false
  enable_cache: true

monitoring:
  log_level: WARNING
  alert_on_errors: true
```

## Cost Optimization Tips

1. **Use Gemini 2.0 Flash or GPT-4.1-nano** for the lowest costs
2. **Enable caching** to avoid re-processing
3. **Set budget limits** to prevent overruns
4. **Use batch processing** for better efficiency

## Troubleshooting

### Configuration Not Loading

```bash
# Check config file location
python -c "from src.config.config_loader import ConfigLoader; print(ConfigLoader()._find_config_file())"

# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

### API Key Issues

```bash
# Check if keys are set
python -c "import os; print('GOOGLE_API_KEY' in os.environ)"
```

### Override Not Working

Ensure you're using the correct precedence order. Command-line args override everything:

```bash
# This will use OpenAI regardless of config.yaml
python -m src.cli.annotate annotate file.txt --provider openai
```