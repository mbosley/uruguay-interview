# Makefile for Uruguay Interview Research Pipeline
# Usage: make help
.PHONY: help clean setup data enrich agent run-agent run-api run-ui run-demo run-all

# Default target
help:
	@echo "Uruguay Interview Research System"
	@echo "================================="
	@echo ""
	@echo "🚀 Quick Start (Web Interface):"
	@echo "  run-api        Start the FastAPI backend server"
	@echo "  run-ui         Start the React web interface"
	@echo "  run-demo       Start the Streamlit demo app"
	@echo "  run-all        Run API + React UI together"
	@echo ""
	@echo "📦 Setup targets:"
	@echo "  setup          Install Python dependencies"
	@echo "  setup-ui       Install React UI dependencies"
	@echo "  setup-all      Install all dependencies"
	@echo "  clean          Clean generated files and artifacts"
	@echo ""
	@echo "🔬 Data processing targets:"
	@echo "  data           Parse all raw interview files → JSON"
	@echo "  enrich         Annotate interviews with themes/tags"
	@echo "  consolidate    Consolidate themes into meta-themes"
	@echo "  pipeline       Run full data pipeline (parse + enrich + consolidate)"
	@echo ""
	@echo "🤖 Research agent targets:"
	@echo "  agent          Run the autonomous research agent"
	@echo "  recursive      Agent with delegation capabilities highlighted"
	@echo "  test-recursive Test recursive sub-agent spawning"
	@echo ""
	@echo "📊 Variables:"
	@echo "  QUESTION       Research question for agent (default: healthcare)"
	@echo "  MAX_ITER       Max agent iterations (default: 30)"
	@echo "  PROVIDER       LLM provider for agent (moonshot, groq)"
	@echo "  MODEL          Specific model name (for enrichment)"
	@echo "  DEBUG          Enable debug logging (set to any value)"
	@echo ""
	@echo "💡 Examples:"
	@echo "  make run-api                     # Start API server"
	@echo "  make run-ui                      # Start React UI (in new terminal)"
	@echo "  make run-demo                    # Start Streamlit demo"
	@echo "  make agent                       # Run with default question"
	@echo "  make agent QUESTION='rural education' MAX_ITER=20"
	@echo "  make agent PROVIDER=groq         # Fast CLI research"
	@echo "  make agent PROVIDER=openai       # Cost-efficient o4-mini"
	@echo "  make agent DEBUG=1               # With debug logging"

# Variables
VENV := venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/python -m pip
PROJECT_ROOT := ..
DATA_DIR := $(PROJECT_ROOT)/data
RAW_DIR := $(DATA_DIR)/raw/interviews
PROCESSED_DIR := $(DATA_DIR)/processed
STRUCTURED_DIR := $(PROCESSED_DIR)/structured
ENRICHED_DIR := $(PROCESSED_DIR)/enriched
CORPUS_JSON := $(STRUCTURED_DIR)/_corpus.json
ENRICHED_CORPUS := $(ENRICHED_DIR)/_enriched_corpus_summary.json

# Default research question and max iterations
QUESTION ?= "What do citizens say about healthcare access and quality in Uruguay?"
MAX_ITER ?= 30
DEBUG ?= # Set to any value to enable debug mode

# LLM provider options (moonshot, groq, openai)
PROVIDER ?= # Use config default
MODEL ?= # Use config default

# Virtual environment
$(VENV):
	@echo "🐍 Creating virtual environment..."
	@python3 -m venv $(VENV) --upgrade-deps
	@$(VENV)/bin/python -m ensurepip --upgrade
	@echo "✅ Virtual environment created"

# Setup and cleanup
setup: $(VENV)
	@echo "🔧 Setting up Python environment..."
	@$(PIP) install --upgrade pip
	@$(PIP) install -r requirements.txt
	@echo "✅ Setup complete"

clean:
	@echo "🧹 Cleaning generated files..."
	rm -f results/research_results_*.json
	rm -f logs/agent_debug.log
	@echo "✅ Clean complete"

# Clean virtual environment
clean-venv:
	@echo "🗑️  Removing virtual environment..."
	rm -rf $(VENV)
	@echo "✅ Virtual environment removed"

# Full clean including venv
clean-all: clean clean-venv
	@echo "✨ Full cleanup complete"

clean-data:
	@echo "🧹 Cleaning processed data files..."
	rm -f $(PROCESSED_DIR)/*.json
	rm -rf $(ENRICHED_DIR)/*.json
	rm -rf $(DATA_DIR)/processed/interviews_txt/
	rm -rf $(DATA_DIR)/processed/annotations/
	@echo "✅ Data clean complete"

# Data processing pipeline
data: $(CORPUS_JSON)

$(CORPUS_JSON):
	@echo "📄 Parsing raw interview files..."
	@mkdir -p $(STRUCTURED_DIR)
	$(PYTHON) scripts/process_all_interviews.py
	@echo "✅ Interview parsing complete"

enrich: $(ENRICHED_CORPUS)

$(ENRICHED_CORPUS): $(CORPUS_JSON)
	@echo "🏷️  Enriching interviews with annotations..."
	@mkdir -p $(ENRICHED_DIR)
	$(PYTHON) scripts/batch_annotate_interviews.py --output-dir $(ENRICHED_DIR) \
		$(if $(PROVIDER),--provider $(PROVIDER)) \
		$(if $(MODEL),--model $(MODEL))
	@echo "🔀 Merging annotations with interview data..."
	$(PYTHON) scripts/merge_annotations.py --annotations-dir $(ENRICHED_DIR) --output-dir $(ENRICHED_DIR)
	@echo "✅ Interview enrichment complete"

# Consolidate themes into meta-themes
consolidate: $(ENRICHED_CORPUS)
	@echo "🏷️  Consolidating themes into meta-themes..."
	$(PYTHON) consolidate_themes.py $(if $(PROVIDER),--provider $(PROVIDER))
	@echo "✅ Theme consolidation completed!"

pipeline: data enrich consolidate
	@echo "🚀 Full data pipeline complete!"
	@echo "📊 Summary:"
	@$(PYTHON) src/cli/enriched_cli.py stats

# Research agent targets
agent: $(ENRICHED_CORPUS)
	@echo "🤖 Running autonomous research agent..."
	@echo "📋 Question: $(QUESTION)"
	@if [ -n "$(PROVIDER)" ]; then \
		echo "Provider: $(PROVIDER)"; \
	fi
	@mkdir -p results logs
	@if [ -n "$(PROVIDER)" ]; then \
		if [ -n "$(DEBUG)" ]; then \
			$(PYTHON) interview_research_agent.py --research --debug --provider=$(PROVIDER) --max-iterations $(MAX_ITER) "$(QUESTION)"; \
		else \
			$(PYTHON) interview_research_agent.py --research --provider=$(PROVIDER) --max-iterations $(MAX_ITER) "$(QUESTION)"; \
		fi \
	else \
		if [ -n "$(DEBUG)" ]; then \
			$(PYTHON) interview_research_agent.py --research --debug --max-iterations $(MAX_ITER) "$(QUESTION)"; \
		else \
			$(PYTHON) interview_research_agent.py --research --max-iterations $(MAX_ITER) "$(QUESTION)"; \
		fi \
	fi

# Original agent (kept for compatibility)
agent-original: $(ENRICHED_CORPUS)
	@echo "🎯 Starting interactive research agent session (original version)..."
	@echo "Enter your research question when prompted."
	@mkdir -p results logs
	@read -p "Research question: " question; \
	$(PYTHON) interview_research_agent.py --question "$$question" --max-iterations $(MAX_ITER)

# Recursive agent testing
test-recursive: $(ENRICHED_CORPUS)
	@echo "🚀 Testing recursive agent functionality..."
	@echo "This will run a broad research question that should trigger delegation"
	@mkdir -p results logs
	$(PYTHON) test_recursive_agent.py

# Run agent with delegation capabilities highlighted
recursive: $(ENRICHED_CORPUS)
	@echo "🚀 Running agent with recursive delegation (max depth: 2)..."
	@echo "📋 Question: $(QUESTION)"
	@echo "💡 Tip: Use a broad question to trigger sub-agent delegation"
	@mkdir -p results logs
	$(PYTHON) interview_research_agent.py --research "$(QUESTION)"

# Development and testing targets
test-cli: $(ENRICHED_CORPUS)
	@echo "🔍 Testing CLI tools..."
	$(PYTHON) src/cli/enriched_cli.py stats
	$(PYTHON) src/cli/enriched_cli.py themes
	$(PYTHON) src/cli/enriched_cli.py search rural

test-parser:
	@echo "🧪 Testing interview parser..."
	$(PYTHON) src/parser/test_parser.py

# Quality checks
check-data:
	@echo "📊 Checking data quality..."
	@if [ -f $(CORPUS_JSON) ]; then \
		echo "✅ Base corpus JSON exists"; \
		$(PYTHON) -c "import json; data=json.load(open('$(CORPUS_JSON)')); print(f'Found {len(data)} interviews')"; \
	else \
		echo "❌ Base corpus JSON missing - run 'make data'"; \
	fi
	@if [ -f $(ENRICHED_CORPUS) ]; then \
		echo "✅ Enriched interviews exist"; \
		$(PYTHON) src/cli/enriched_cli.py stats; \
	else \
		echo "❌ Enriched interviews missing - run 'make enrich'"; \
	fi

# Show current status
status:
	@echo "📋 Pipeline Status"
	@echo "=================="
	@make check-data
	@echo ""
	@if [ -f logs/agent_debug.log ]; then \
		echo "🤖 Last agent run:"; \
		tail -n 3 logs/agent_debug.log; \
	else \
		echo "🤖 No agent runs yet"; \
	fi
	@echo ""
	@echo "📁 Recent research results:"
	@ls -1t results/research_results_*.json 2>/dev/null | head -3 || echo "  No results yet"

# Research shortcuts for common questions
healthcare:
	@make agent QUESTION="What do citizens say about healthcare access and quality in Uruguay?"

education:
	@make agent QUESTION="What are citizen perspectives on education policy and classroom reality?"

rural-services:
	@make agent QUESTION="What do rural communities say about government services?"

security:
	@make agent QUESTION="What security concerns do citizens raise in small communities?"


# Debug and development
debug-agent: $(ENRICHED_CORPUS)
	@echo "🐛 Running agent in debug mode..."
	@echo "🔍 Will show detailed logs and conversation flow"
	@mkdir -p results logs
	$(PYTHON) interview_research_agent.py --question "$(QUESTION)" --max-iterations 5

show-logs:
	@if [ -f logs/agent_debug.log ]; then \
		echo "📋 Recent agent activity:"; \
		tail -n 20 logs/agent_debug.log; \
	else \
		echo "❌ No debug logs found"; \
	fi

# Web Interface Targets
# =====================

# Start the FastAPI backend server
run-api: $(VENV)
	@echo "🚀 Starting API server on http://localhost:8000"
	@echo "📚 API docs available at http://localhost:8000/docs"
	@$(PYTHON) api_server.py

# Start the React frontend
run-ui:
	@echo "🎨 Starting React UI on http://localhost:3000"
	@echo "⚠️  Make sure API server is running (make run-api)"
	@cd uruguay-research-ui && npm start

# Start the Streamlit demo
run-demo: $(VENV)
	@echo "📊 Starting Streamlit demo on http://localhost:8501"
	@cd web_demo && ../$(PYTHON) -m streamlit run app.py

# Run both API and UI together (requires two terminals)
run-all:
	@echo "🚀 Starting full stack application..."
	@echo "API: http://localhost:8000"
	@echo "UI:  http://localhost:3000"
	@echo ""
	@echo "Press Ctrl+C to stop both services"
	@trap 'kill 0' INT; \
	$(PYTHON) api_server.py & \
	cd uruguay-research-ui && npm start & \
	wait

# Setup UI dependencies
setup-ui:
	@echo "📦 Installing React UI dependencies..."
	@cd uruguay-research-ui && npm install

# Setup all dependencies
setup-all: setup setup-ui
	@echo "✅ All dependencies installed!"

# Start unified logger
run-logger: $(VENV)
	@echo "📝 Starting unified logger on http://localhost:8001"
	@$(PYTHON) unified_logger.py

# View unified logs
view-logs: $(VENV)
	@$(PYTHON) view_unified_logs.py
