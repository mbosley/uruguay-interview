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
# Edit config.yaml to set your preferred AI provider and settings
```

### Configuration

The project uses a centralized configuration system:

```yaml
# config.yaml
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

## 📁 Project Structure

```
uruguay-interview/
├── config/                 # Configuration files
│   ├── prompts/           # AI prompts and schemas
│   ├── database/          # Database schemas
│   └── dashboards/        # Dashboard configurations
├── src/                   # Source code
│   ├── pipeline/          # Core annotation pipeline
│   ├── analysis/          # Analysis components
│   ├── dashboards/        # Dashboard generation
│   ├── followup/          # WhatsApp AI system
│   └── research/          # Academic research components
├── data/                  # Data directory (gitignored)
├── tests/                 # Test suite
├── scripts/               # Operational scripts
├── notebooks/             # Jupyter notebooks
├── docs/                  # Documentation
└── deliverables/          # Stakeholder outputs
```

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
- **[Master Project Roadmap](docs/roadmap/PROJECT_ROADMAP.md)** - Complete project overview, timeline, and training framework
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