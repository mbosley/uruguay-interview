# Makefile for Uruguay Interview Research Pipeline
# Usage: make help
.PHONY: help clean setup data enrich agent run-agent

# Default target
help:
	@echo "Uruguay Interview Research Pipeline"
	@echo "=================================="
	@echo ""
	@echo "Setup targets:"
	@echo "  setup          Install Python dependencies"
	@echo "  clean          Clean generated files and artifacts"
	@echo ""
	@echo "Data processing targets:"
	@echo "  data           Parse all raw interview files → JSON"
	@echo "  enrich         Annotate interviews with themes/tags"
	@echo "  pipeline       Run full data pipeline (parse + enrich)"
	@echo ""
	@echo "Research agent targets:"
	@echo "  agent          Test the autonomous research agent"
	@echo "  run-agent      Interactive agent session"
	@echo ""
	@echo "Variables:"
	@echo "  QUESTION       Research question for agent (default: healthcare)"
	@echo "  MAX_ITER       Max agent iterations (default: 15)"
	@echo "  PROVIDER       LLM provider (kimi, openai, gemini)"
	@echo "  MODEL          Specific model name"
	@echo ""
	@echo "Examples:"
	@echo "  make pipeline                    # Full data processing"
	@echo "  make enrich PROVIDER=gemini MODEL=gemini-flash"
	@echo "  make enrich PROVIDER=openai MODEL=gpt-4o"
	@echo "  make agent QUESTION='rural education' MAX_ITER=20"
	@echo "  make run-agent                   # Interactive session"

# Variables
PYTHON := python3
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

# LLM provider options
PROVIDER ?= # Use config default
MODEL ?= # Use config default

# Setup and cleanup
setup:
	@echo "🔧 Setting up Python environment..."
	$(PYTHON) -m pip install -r requirements.txt
	@echo "✅ Setup complete"

clean:
	@echo "🧹 Cleaning generated files..."
	rm -f results/research_results_*.json
	rm -f logs/agent_debug.log
	@echo "✅ Clean complete"

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

pipeline: data enrich
	@echo "🚀 Full data pipeline complete!"
	@echo "📊 Summary:"
	@$(PYTHON) src/cli/enriched_cli.py stats

# Research agent targets
agent: $(ENRICHED_CORPUS)
	@echo "🤖 Running autonomous research agent..."
	@echo "📋 Question: $(QUESTION)"
	@mkdir -p results logs
	$(PYTHON) interview_research_agent_improved.py "$(QUESTION)"

# Research mode with extra detailed logging
research: $(ENRICHED_CORPUS)
	@echo "🔬 Running research agent with extra detailed logging..."
	@echo "📋 Question: $(QUESTION)"
	@mkdir -p results logs
	$(PYTHON) interview_research_agent_improved.py --research "$(QUESTION)"

# Original agent (kept for compatibility)
agent-original: $(ENRICHED_CORPUS)
	@echo "🤖 Running autonomous research agent (original version)..."
	@echo "📋 Question: $(QUESTION)"
	@mkdir -p results logs
	$(PYTHON) interview_research_agent.py --question "$(QUESTION)" --max-iterations $(MAX_ITER)

run-agent: $(ENRICHED_CORPUS)
	@echo "🎯 Starting interactive research agent session..."
	@echo "Enter your research question when prompted."
	@mkdir -p results logs
	$(PYTHON) interview_research_agent_improved.py

# Original agent (kept for compatibility)
run-agent-original: $(ENRICHED_CORPUS)
	@echo "🎯 Starting interactive research agent session (original version)..."
	@echo "Enter your research question when prompted."
	@mkdir -p results logs
	@read -p "Research question: " question; \
	$(PYTHON) interview_research_agent.py --question "$$question" --max-iterations $(MAX_ITER)

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
