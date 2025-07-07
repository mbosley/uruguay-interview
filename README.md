# Uruguay Active Listening: AI-Powered Interview Analysis Framework

An advanced AI framework for analyzing citizen consultation interviews at scale, developed for the Uruguay Government's 5-year active listening initiative. This system processes qualitative interviews through sophisticated annotation pipelines, enabling both real-time policy insights and groundbreaking academic research.

## 📑 Quick Links

**Core Documentation:**
[📋 Master Roadmap](docs/roadmap/PROJECT_ROADMAP.md) | [🤖 Annotation Framework](docs/roadmap/ANNOTATION_FRAMEWORK_ROADMAP.md) | [💬 WhatsApp AI](docs/roadmap/WHATSAPP_AI_FOLLOWUP_ROADMAP.md) | [👥 Digital Twins](docs/roadmap/DIGITAL_TWIN_RESEARCH_ROADMAP.md) | [📊 Quantitative Insights](docs/roadmap/QUANTITATIVE_INSIGHTS_FRAMEWORK.md)

**Development:**
[💻 Dev Guidelines](CLAUDE.md) | [📚 Documentation Hub](docs/README.md) | [⚙️ Setup Guide](docs/USER_GUIDE.md) | [🔧 Technical Log](docs/TECHNICAL_LOG.md) | [📊 Research Log](docs/RESEARCH_LOG.md)

## 🎯 Project Overview

This framework addresses the challenge of analyzing 5000+ citizen interviews over 5 years, transforming rich qualitative data into actionable policy insights while preserving the authenticity of citizen voices.

### Key Features

- **Two-Layer Architecture**: Rich qualitative annotations (Layer 1) + Structured quantitative extraction (Layer 2)
- **AI-Powered Annotation**: Advanced LLM-based interview analysis with quality validation
- **Real-time Dashboards**: Executive, researcher, and public-facing insights
- **WhatsApp AI Follow-ups**: Automated conversational engagement with participants
- **Digital Twin Research**: Individual-level political reasoning models
- **Scalable Infrastructure**: Handles 1000+ interviews per month

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL 13+
- Redis 6+
- Pandoc (for document conversion)

### Installation

```bash
# Clone the repository
git clone https://github.com/mbosley/uruguay-interview.git
cd uruguay-interview

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .

# Copy environment variables
cp .env.example .env
# Edit .env with your API keys

# Configure the pipeline (optional - defaults work out of box)
# Edit settings.yaml to set your preferred AI provider and settings
```

### Configuration

The project uses a centralized configuration system:

```yaml
# settings.yaml
ai:
  provider: gemini              # Options: openai, anthropic, gemini
  model: gemini-2.0-flash      # Cheapest option at $0.000875/interview
  temperature: 0.3
```

See [Configuration Guide](docs/CONFIGURATION.md) for detailed settings.

### Basic Usage

```bash
# Show current configuration
python -m src.cli.annotate info

# Annotate a single interview
python -m src.cli.annotate annotate data/processed/interviews_txt/20250528_0900_058.txt

# Batch process multiple interviews
python -m src.cli.annotate batch --limit 10

# Compare costs across providers
python -m src.cli.annotate costs

# Use different AI provider
python -m src.cli.annotate annotate interview.txt --provider openai --model gpt-4o-mini
```

### Running MFT-Enhanced Analysis

The Moral Foundations Theory (MFT) dimension is now integrated into the standard pipeline:

```bash
# Run full pipeline with MFT analysis
make check      # Ensures database has MFT tables
make annotate   # Runs production annotation with all 6 dimensions

# Or run MFT pipeline directly
python scripts/run_mft_pipeline.py
```

See [MFT Pipeline Guide](docs/HOW_TO_RUN_MFT.md) for detailed instructions.

## 📁 Project Structure

### Core Directories

#### `/src` - Source Code
- **`/pipeline`** - Data processing pipeline
  - `/annotation` - AI annotation engines (JSON mode, multipass, MFT analyzer)
  - `/ingestion` - Document processing and interview loading
  - `/extraction` - Data extraction from annotations
  - `/parsing` - Interview text parsing
- **`/database`** - Database models and connection management
- **`/dashboard`** - Streamlit dashboard applications
- **`/cli`** - Command-line interface tools
- **`/config`** - Configuration management
- **`/analysis`** - Analysis components
- **`/followup`** - WhatsApp AI system
- **`/research`** - Academic research components

#### `/data` - Data Storage (git-ignored)
- **`/raw/interviews`** - Original interview files (.docx, .odt)
- **`/processed`** - Processed data
  - `/interviews_txt` - Plain text versions
  - `/annotations/production` - Final annotations
- **`/exports`** - Export files (CSV, Excel)
- **`uruguay_interviews.db`** - SQLite database

#### `/config` - Configuration Files
- **`/prompts`** - Annotation prompts and schemas
- **`/schemas`** - XSD validation schemas
- **`settings.py`** - Application settings
- **`settings.yaml`** - Main application settings

#### `/scripts` - Utility Scripts
- **`annotate_interviews.py`** - Production annotation with MFT
- Database management utilities
- Export and visualization tools
- Dashboard launchers

#### `/tests` - Test Suite
- **`/unit`** - Unit tests
- **`/integration`** - Integration tests
- **`/e2e`** - End-to-end tests
- **`/fixtures`** - Test data

#### `/docs` - Documentation
- **`/technical`** - Technical documentation
- **`/roadmap`** - Project roadmaps
- **`/database`** - Database schema docs
- **`/legacy`** - Archived documentation
- **`/pitch`** - Project proposals

#### `/archive` - Obsolete Files
- Historical versions of scripts, models, and components
- See `/archive/README.md` for details

### Key Files

- **`CLAUDE.md`** - Instructions for Claude Code and development guidelines
- **`requirements.txt`** - Python dependencies
- **`Makefile`** - Common operations and automation
- **`settings.yaml`** - Main application settings
- **`demos/`** - Demo files and standalone visualizations

### Workflow

1. **Ingestion**: Raw interviews (.docx/.odt) → Plain text
2. **Annotation**: AI analysis using 6-dimensional framework (including MFT)
3. **Storage**: Structured data → SQLite database
4. **Visualization**: Interactive dashboards and HTML outputs

### Current State

- ✅ 37 interviews fully annotated with MFT dimension
- ✅ Database populated with complete annotations
- ✅ Interactive research dashboard functional
- ✅ Production pipeline optimized for scale

## 🔧 Core Components

### 1. Annotation Pipeline

The heart of the system, processing interviews through multiple stages:

```python
from src.pipeline import AnnotationPipeline

pipeline = AnnotationPipeline()
annotation = pipeline.process_interview("path/to/interview.docx")
```

### 2. Quality Assurance

Comprehensive validation to ensure annotation accuracy:

```python
from src.pipeline.quality import QualityValidator

validator = QualityValidator()
quality_report = validator.validate_annotation(annotation)
```

### 3. Dashboard Generation

Real-time insights for different stakeholders:

```python
from src.dashboards import ExecutiveDashboard

dashboard = ExecutiveDashboard()
dashboard.update_with_latest_data()
dashboard.export("deliverables/government/dashboards/executive.html")
```

## 🔍 Analysis Framework

The system implements a comprehensive 6-dimensional analysis framework:

1. **Functional Analysis** - What speakers are doing (e.g., problem identification, solution proposing)
2. **Content Analysis** - Topics discussed and geographic scope (national/local)
3. **Evidence Analysis** - Types of support provided (personal experience, statistics, etc.)
4. **Emotional Analysis** - Emotional tone and intensity in discourse
5. **Uncertainty Tracking** - Confidence levels in coding decisions
6. **Moral Foundations Theory** - Moral concerns invoked (care/harm, fairness, loyalty, etc.)

## 📊 Data Flow

1. **Input**: Raw interview files (DOCX/ODT)
2. **Processing**: Text extraction → AI annotation → Quality validation
3. **Storage**: Layer 1 (JSON) → Layer 2 (SQL)
4. **Analysis**: Quantitative insights + Qualitative context
5. **Output**: Dashboards, reports, research datasets

## 🛡️ Security & Privacy

- All interview data is excluded from version control
- Participant identifiers are anonymized
- API keys stored in environment variables
- Encrypted data transmission for WhatsApp integration

## 📚 Documentation Index

### 🗺️ Project Roadmaps
- **[Project Roadmap](ROADMAP.md)** - Complete project overview, timeline, and training framework
- **[AI Annotation Framework Roadmap](docs/roadmap/ANNOTATION_FRAMEWORK_ROADMAP.md)** - Core annotation engine development plan
- **[WhatsApp AI Follow-up Roadmap](docs/roadmap/WHATSAPP_AI_FOLLOWUP_ROADMAP.md)** - Conversational AI system for continuous engagement
- **[Digital Twin Research Roadmap](docs/roadmap/DIGITAL_TWIN_RESEARCH_ROADMAP.md)** - Individual political reasoning models

### 📊 Frameworks & Methodologies
- **[Quantitative Insights Framework](docs/roadmap/QUANTITATIVE_INSIGHTS_FRAMEWORK.md)** - From SQL tables to policy insights
- **[Annotation Schema](config/prompts/annotation_prompt_v1.xml)** - Detailed XML schema for interview annotation

### 🛠️ Technical Documentation
- **[Configuration Guide](config/settings.py)** - System configuration and settings
- **[Technical Architecture](docs/technical/architecture.md)** - System design and components *(coming soon)*
- **[API Documentation](docs/technical/api.md)** - API endpoints and usage *(coming soon)*
- **[Deployment Guide](docs/technical/deployment.md)** - Production deployment instructions *(coming soon)*

### 📖 Development Resources
- **[Development Guidelines](CLAUDE.md)** - Git workflow, coding standards, and best practices
- **[Training Materials](docs/training/)** - Capacity building curriculum *(coming soon)*
- **[Research Methodology](docs/research/methodology.md)** - Academic research approaches *(coming soon)*

## 🤝 Contributing

This project follows conventional commit standards. See [CLAUDE.md](CLAUDE.md) for development guidelines.

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Set up pre-commit hooks
pre-commit install

# Run tests
pytest

# Run linting
ruff check .
black --check .
```

## 📈 Roadmap

### Phase 1: Foundation (Current)
- ✅ Core pipeline implementation
- ✅ Basic annotation functionality
- 🔄 Quality validation system

### Phase 2: Production Scale
- WhatsApp AI integration
- Advanced dashboards
- Batch processing optimization

### Phase 3: Research Innovation
- Digital twin methodology
- Synthetic survey generation
- Cross-method validation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Uruguay Government's Presidency Office
- Citizen participants in the active listening initiative
- Research team: Juan Pablo Luna, Mitchell Bosley, and collaborators

## 📞 Contact

For questions about the framework or collaboration opportunities, please open an issue on GitHub.

---

*Building the future of democratic participation through AI-powered citizen listening*