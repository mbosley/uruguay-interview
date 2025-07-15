# Uruguay Interview Research Agent

## 🎯 Purpose
Autonomous research agent for exploring citizen consultation interviews from Uruguay (May 28-29, 2025) using AI-powered investigation and natural language queries.

## 🚀 Quick Start

```bash
# Setup
make setup

# Run research agent
make agent QUESTION="What do citizens say about healthcare access?"

# Interactive session
make run-agent

# Check status
make status
```

## 🏗️ Architecture

```
Raw Interviews → Parser → Enriched JSON → Research Agent → Insights
(.docx/.odt)               (with AI annotations)    (autonomous exploration)
```

## 📊 Pipeline

### 1. Data Processing
```bash
make data       # Parse raw interviews → JSON
make enrich     # Add AI annotations/themes  
make pipeline   # Full processing pipeline
```

### 2. Research Agent
```bash
make agent                    # Default healthcare question
make healthcare              # Healthcare access research
make education              # Education policy research  
make rural-services         # Rural government services
make security              # Community security concerns
```

### 3. Custom Research
```bash
make agent QUESTION="What challenges do teachers face?" MAX_ITER=20
make run-agent  # Interactive: prompts for your question
```

## 📁 Directory Structure

```
search-mvp/
├── results/                    # Research outputs
│   └── research_results_*.json
├── logs/                      # Debug logs
│   └── agent_debug.log
├── src/
│   ├── cli/                   # Search and data access
│   ├── parser/                # Interview processing
│   ├── scratchpad/            # Exploration sessions
│   └── search/                # Search utilities
├── scripts/                   # Batch processing
├── prompts/                   # AI prompts
├── scratchpads/              # Research sessions
├── interview_research_agent.py # Main agent
├── interview_research_tools.py # Tool definitions
└── Makefile                   # Pipeline automation
```

## 🤖 How the Agent Works

### Autonomous Research Process
1. **Corpus Overview** - Understands available data
2. **Theme Discovery** - Identifies relevant topics
3. **Deep Search** - Explores specific evidence  
4. **Evidence Chains** - Builds connections between findings
5. **Synthesis** - Generates insights with citations

### Research Tools
- `get_corpus_stats` - Overview of interview data
- `list_interview_themes` - Available themes and topics
- `search_interviews` - Text and semantic search
- `get_interview_turn` - Retrieve specific quotes
- `get_whole_interview` - Full interview context

### Example Agent Exploration
```
🔄 Iteration 1/15
💭 Agent thinking: I'll explore rural healthcare access by first understanding the corpus structure...
🔧 Making 1 tool call(s)
  🔍 get_corpus_stats({})
    ✅ Result: 187 characters

🔄 Iteration 2/15
💭 Agent thinking: Now let me examine available themes...
🔧 Making 1 tool call(s)
  🔍 list_interview_themes({})
    ✅ Result: 1577 characters
```

## 📋 Available Commands

### Pipeline Management
- `make setup` - Install dependencies
- `make clean` - Remove generated files
- `make status` - Check pipeline health
- `make check-data` - Verify data files

### Development & Testing  
- `make test-cli` - Test search tools
- `make debug-agent` - Agent with detailed logging
- `make show-logs` - Recent activity

### Research Shortcuts
- `make healthcare` - Healthcare access research
- `make education` - Education policy analysis
- `make rural-services` - Rural government services
- `make security` - Community security concerns

## 🔍 Research Examples

### Healthcare Access
```bash
make healthcare
# → "What do citizens say about healthcare access and quality in Uruguay?"
```

### Custom Investigation
```bash
make agent QUESTION="How do rural communities view education policy?"
```

### Interactive Session
```bash
make run-agent
# Research question: What transportation challenges do citizens face?
```

## 📖 Data Source

- **37 citizen consultation interviews** from Uruguay
- **May 28-29, 2025** consultation period
- **Focus**: National and local priorities from citizen perspectives
- **Themes**: Healthcare, education, security, rural services, governance

## 🎓 Research Capabilities

### What the Agent Can Discover
- **Citizen perspectives** on government services
- **Rural vs urban** service access differences  
- **Policy implementation gaps** between intention and reality
- **Community priorities** and concerns
- **Evidence patterns** across multiple interviews

### Research Output
- **Comprehensive summaries** with specific citations
- **Evidence chains** linking related findings
- **Theme analysis** with supporting quotes
- **Turn-level citations** (e.g., "Interview 072, Turn 49")

## 🔧 Technical Details

### Agent Technology
- **Kimi AI** for conversation and tool use
- **Multi-turn exploration** with conversation continuity
- **Autonomous stopping** when sufficient evidence gathered
- **Forced summarization** if iteration limit reached

### Data Processing
- **Interview parsing** from Word/ODT to structured JSON
- **AI enrichment** with themes, tags, and annotations
- **Fast in-memory search** for real-time exploration
- **Stable turn IDs** for reliable citations

### Built for Researchers
- **Natural language queries** - no complex syntax
- **Autonomous exploration** - discovers relevant evidence
- **Comprehensive citations** - every claim sourced
- **Exportable results** - JSON format for further analysis

---

**Goal**: Enable researchers to ask complex questions about citizen perspectives and receive comprehensive, evidence-based answers through AI-powered exploration of interview data.