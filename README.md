# Uruguay Active Listening: AI-Powered Interview Analysis Framework

An advanced AI framework for analyzing citizen consultation interviews at scale, developed for the Uruguay Government's 5-year active listening initiative. This system processes qualitative interviews through sophisticated annotation pipelines, enabling both real-time policy insights and groundbreaking academic research.

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
# Edit .env with your API keys and configuration
```

### Basic Usage

```bash
# Convert interview documents to text
python scripts/convert_interviews.sh

# Run annotation pipeline on a single interview
uruguay-pipeline --interview data/raw/interviews/interview_001.docx

# Batch process multiple interviews
uruguay-batch --input-dir data/raw/interviews --output-dir data/processed/annotations

# Check annotation quality
uruguay-quality --annotations-dir data/processed/annotations

# Generate dashboards
uruguay-export --type dashboard --output deliverables/government/dashboards
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

## 📚 Documentation

- [Project Roadmap](docs/roadmap/PROJECT_ROADMAP.md)
- [Quantitative Insights Framework](docs/roadmap/QUANTITATIVE_INSIGHTS_FRAMEWORK.md)
- [Technical Architecture](docs/technical/architecture.md)
- [Training Materials](docs/training/)

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