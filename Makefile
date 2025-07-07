# Uruguay Interview Analysis Pipeline
# Professional Makefile-driven automation for qualitative research

# Configuration
SHELL := /bin/bash
.DEFAULT_GOAL := help
.PHONY: help clean setup check status annotate validate extract dashboard deploy test

# Directories
DATA_DIR := data
RAW_DIR := $(DATA_DIR)/raw/interviews
PROCESSED_DIR := $(DATA_DIR)/processed
ANNOTATIONS_DIR := $(PROCESSED_DIR)/annotations
PRODUCTION_DIR := $(ANNOTATIONS_DIR)/production
REPORTS_DIR := $(DATA_DIR)/reports
LOGS_DIR := logs

# Python environment
PYTHON := python3
VENV := venv
PIP := $(VENV)/bin/pip
PYTHON_VENV := $(VENV)/bin/python

# Pipeline configuration
MAX_WORKERS := 6
BUDGET_LIMIT := 1.00
TIMEOUT := 1800  # 30 minutes

# Color output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

## Display help information
help:
	@echo "$(BLUE)Uruguay Interview Analysis Pipeline$(NC)"
	@echo "======================================"
	@echo ""
	@echo "$(GREEN)Main Targets:$(NC)"
	@echo "  setup         - Initialize environment and dependencies"
	@echo "  check         - Verify system readiness (includes MFT setup)"
	@echo "  status        - Show current pipeline status"
	@echo "  annotate      - Run production annotation with 6 dimensions (includes MFT)"
	@echo "  validate      - Validate annotation quality"
	@echo "  extract       - Extract structured data from annotations"
	@echo "  extract-enhanced - Extract comprehensive data for enhanced schema"
	@echo "  dashboard     - Generate research dashboard"
	@echo "  deploy        - Full pipeline deployment with MFT"
	@echo ""
	@echo "$(GREEN)Utility Targets:$(NC)"
	@echo "  clean         - Clean temporary files and logs"
	@echo "  test          - Run test suite"
	@echo "  diagnose      - Diagnose remaining work"
	@echo ""
	@echo "$(GREEN)Configuration:$(NC)"
	@echo "  Workers: $(MAX_WORKERS), Budget: $$$(BUDGET_LIMIT), Timeout: $(TIMEOUT)s"

## Initialize environment and dependencies
setup: $(VENV)/bin/activate requirements-check
	@echo "$(GREEN)✅ Environment setup complete$(NC)"

$(VENV)/bin/activate:
	@echo "$(YELLOW)Setting up Python virtual environment...$(NC)"
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

requirements-check: $(VENV)/bin/activate requirements.txt
	@$(PIP) install -r requirements.txt > /dev/null 2>&1

## Create necessary directories
dirs:
	@mkdir -p $(LOGS_DIR) $(REPORTS_DIR) $(PRODUCTION_DIR)

## Ensure database exists with MFT tables
db-check: setup
	@echo "$(YELLOW)Checking database setup...$(NC)"
	@test -f "$(DATA_DIR)/uruguay_interviews.db" || (echo "$(RED)❌ Database not found$(NC)" && exit 1)
	@$(PYTHON_VENV) -c "import sqlite3; conn = sqlite3.connect('$(DATA_DIR)/uruguay_interviews.db'); cursor = conn.cursor(); cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name='turn_moral_foundations'\"); result = cursor.fetchone(); exit(0 if result else 1)" || \
		(echo "$(YELLOW)⚠️  MFT tables not found, creating...$(NC)" && $(PYTHON_VENV) scripts/add_mft_tables.py)
	@echo "✅ Database ready with MFT support"

## Verify system readiness
check: setup dirs db-check
	@echo "$(BLUE)🔍 System Readiness Check$(NC)"
	@echo "=============================="
	@$(PYTHON_VENV) -c "import openai; print('✅ OpenAI library available')" || (echo "$(RED)❌ OpenAI library missing$(NC)" && exit 1)
	@test -n "$$OPENAI_API_KEY" && echo "✅ OpenAI API key configured" || (echo "$(RED)❌ OPENAI_API_KEY not set$(NC)" && exit 1)
	@test -d "$(RAW_DIR)" && echo "✅ Raw data directory exists" || (echo "$(RED)❌ Raw data directory missing$(NC)" && exit 1)
	@test -d "$(PROCESSED_DIR)/interviews_txt" && echo "✅ Processed interviews available" || (echo "$(RED)❌ Processed interviews missing$(NC)" && exit 1)
	@count=$$(ls $(PROCESSED_DIR)/interviews_txt/*.txt 2>/dev/null | wc -l); echo "✅ Found $$count interview files"
	@echo "$(GREEN)✅ System ready for annotation$(NC)"

## Show current pipeline status
status: setup
	@echo "$(BLUE)📊 Pipeline Status (with MFT)$(NC)"
	@echo "============================"
	@$(PYTHON_VENV) scripts/pipeline_status.py
	@echo ""
	@echo "$(BLUE)🧬 MFT Integration Status:$(NC)"
	@$(PYTHON_VENV) -c "import sqlite3; conn = sqlite3.connect('$(DATA_DIR)/uruguay_interviews.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM turn_moral_foundations'); mft_count = cursor.fetchone()[0]; print(f'  MFT annotations: {mft_count} turns')" 2>/dev/null || echo "  MFT annotations: 0 turns"

## Run production annotation pipeline
annotate: check $(PRODUCTION_DIR)/annotation.lock

$(PRODUCTION_DIR)/annotation.lock: setup
	@echo "$(BLUE)🚀 Running Production Annotation with MFT (6 Dimensions)$(NC)"
	@echo "=================================================="
	@echo "Workers: $(MAX_WORKERS), Budget: $$$(BUDGET_LIMIT)"
	@echo "Dimensions: Functional, Content, Evidence, Emotional, Uncertainty, MFT"
	@mkdir -p $(LOGS_DIR)
	@timeout $(TIMEOUT) $(PYTHON_VENV) scripts/production_annotate_with_mft.py \
		--max-workers $(MAX_WORKERS) \
		--budget-limit $(BUDGET_LIMIT) \
		--output-dir $(PRODUCTION_DIR) \
		--log-file $(LOGS_DIR)/annotation_mft_$$(date +%Y%m%d_%H%M%S).log \
		|| (echo "$(YELLOW)⚠️  Annotation process stopped (timeout or completion)$(NC)")
	@touch $@

## Validate annotation quality
validate: $(PRODUCTION_DIR)/validation.lock

$(PRODUCTION_DIR)/validation.lock: $(PRODUCTION_DIR)/annotation.lock
	@echo "$(BLUE)🔍 Validating Annotation Quality$(NC)"
	@echo "=================================="
	@$(PYTHON_VENV) scripts/robust_validate.py \
		--input-dir $(PRODUCTION_DIR) \
		--output-dir $(REPORTS_DIR) \
		--log-file $(LOGS_DIR)/validation_$$(date +%Y%m%d_%H%M%S).log
	@touch $@

## Extract structured data from annotations
extract: $(PRODUCTION_DIR)/extraction.lock

$(PRODUCTION_DIR)/extraction.lock: $(PRODUCTION_DIR)/validation.lock
	@echo "$(BLUE)📊 Extracting Structured Data$(NC)"
	@echo "=============================="
	@$(PYTHON_VENV) scripts/robust_extract.py \
		--input-dir $(PRODUCTION_DIR) \
		--output-dir $(PROCESSED_DIR)/extracted \
		--log-file $(LOGS_DIR)/extraction_$$(date +%Y%m%d_%H%M%S).log
	@touch $@

## Extract enhanced data for comprehensive database schema
extract-enhanced: $(PRODUCTION_DIR)/enhanced_extraction.lock

$(PRODUCTION_DIR)/enhanced_extraction.lock: $(PRODUCTION_DIR)/validation.lock
	@echo "$(BLUE)🔬 Extracting Enhanced Data$(NC)"
	@echo "================================"
	@echo "Extracting comprehensive data for enhanced database schema..."
	@$(PYTHON_VENV) scripts/extract_enhanced_data.py
	@touch $@

## Generate research dashboard
dashboard: $(PRODUCTION_DIR)/dashboard.lock

$(PRODUCTION_DIR)/dashboard.lock: $(PRODUCTION_DIR)/extraction.lock
	@echo "$(BLUE)📈 Generating Research Dashboard$(NC)"
	@echo "================================="
	@$(PYTHON_VENV) scripts/robust_dashboard.py \
		--input-dir $(PROCESSED_DIR)/extracted \
		--output-dir $(DATA_DIR)/dashboard \
		--log-file $(LOGS_DIR)/dashboard_$$(date +%Y%m%d_%H%M%S).log
	@touch $@

## Run complete pipeline deployment
deploy: check annotate validate extract extract-enhanced dashboard
	@echo "$(GREEN)🎯 Pipeline Deployment Complete$(NC)"
	@echo "=================================="
	@$(PYTHON_VENV) scripts/deployment_summary.py

## Run test suite
test: setup
	@echo "$(BLUE)🧪 Running Test Suite$(NC)"
	@echo "====================="
	@$(PYTHON_VENV) -m pytest tests/ -v --tb=short

## Diagnose remaining work
diagnose: setup
	@echo "$(BLUE)🔍 Diagnosing Remaining Work$(NC)"
	@echo "============================"
	@$(PYTHON_VENV) scripts/diagnose_remaining_interviews.py

## Clean temporary files and reset locks
clean:
	@echo "$(YELLOW)🧹 Cleaning temporary files...$(NC)"
	@rm -f $(PRODUCTION_DIR)/*.lock
	@rm -rf $(LOGS_DIR)/*.log.tmp
	@rm -rf __pycache__/ */__pycache__/ */*/__pycache__/
	@rm -rf .pytest_cache/
	@find . -name "*.pyc" -delete
	@echo "$(GREEN)✅ Cleanup complete$(NC)"

## Clean everything including outputs (DANGEROUS)
clean-all: clean
	@echo "$(RED)⚠️  WARNING: This will delete ALL pipeline outputs$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo ""; \
		echo "$(YELLOW)Removing all outputs...$(NC)"; \
		rm -rf $(PRODUCTION_DIR)/*; \
		rm -rf $(REPORTS_DIR)/*; \
		rm -rf $(PROCESSED_DIR)/extracted/*; \
		rm -rf $(DATA_DIR)/dashboard/*; \
		echo "$(GREEN)✅ All outputs removed$(NC)"; \
	else \
		echo ""; \
		echo "$(GREEN)Cancelled$(NC)"; \
	fi

## Show detailed pipeline configuration
config:
	@echo "$(BLUE)🔧 Pipeline Configuration$(NC)"
	@echo "============================"
	@echo "Python: $$($(PYTHON) --version)"
	@echo "Virtual env: $(VENV)"
	@echo "Max workers: $(MAX_WORKERS)"
	@echo "Budget limit: $$$(BUDGET_LIMIT)"
	@echo "Timeout: $(TIMEOUT)s"
	@echo "Data directory: $(DATA_DIR)"
	@echo "Logs directory: $(LOGS_DIR)"
	@echo ""
	@echo "$(GREEN)Environment Variables:$(NC)"
	@env | grep -E "(OPENAI|ANTHROPIC|GOOGLE)_" || echo "No API keys configured"

## Monitor pipeline progress in real-time
monitor: setup
	@echo "$(BLUE)📊 Real-time Pipeline Monitor$(NC)"
	@echo "=============================="
	@$(PYTHON_VENV) scripts/pipeline_monitor.py

## Resume annotation from where it left off
resume: check
	@echo "$(BLUE)🔄 Resuming Annotation Pipeline$(NC)"
	@echo "==============================="
	@rm -f $(PRODUCTION_DIR)/annotation.lock
	@$(MAKE) annotate

## Quick status check for CI/automation
ci-status: setup
	@completed=$$(ls $(PRODUCTION_DIR)/*_final_annotation.json 2>/dev/null | wc -l); \
	total=$$(ls $(PROCESSED_DIR)/interviews_txt/*.txt 2>/dev/null | wc -l); \
	echo "$$completed/$$total"

# Development targets
dev-setup: setup
	@$(PIP) install pytest black flake8 mypy
	@echo "$(GREEN)✅ Development environment ready$(NC)"

lint: dev-setup
	@echo "$(BLUE)🔍 Code Quality Check$(NC)"
	@$(VENV)/bin/black --check scripts/ src/ || echo "$(YELLOW)⚠️  Run 'make format' to fix formatting$(NC)"
	@$(VENV)/bin/flake8 scripts/ src/ || echo "$(YELLOW)⚠️  Fix linting issues$(NC)"

format: dev-setup
	@echo "$(BLUE)🎨 Formatting Code$(NC)"
	@$(VENV)/bin/black scripts/ src/

# Show pipeline statistics
stats: setup
	@echo "$(BLUE)📈 Pipeline Statistics$(NC)"
	@echo "========================"
	@$(PYTHON_VENV) scripts/pipeline_stats.py