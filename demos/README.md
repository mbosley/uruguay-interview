# Demos Directory

This directory contains demonstration files and quick-start scripts for the Uruguay Interview Analysis project.

## Contents

### `interview_annotations_index.html`
A standalone HTML file that provides a visual index of all annotated interviews. Open this file in a web browser to browse through the interview annotations with a user-friendly interface.

### `run_chat.py`
A quick launcher script for the interactive chat interface dashboard. This provides an AI-powered conversational interface for exploring the interview data.

**Usage:**
```bash
python demos/run_chat.py
```

## Running Demos

From the project root:

```bash
# Launch the chat interface
python demos/run_chat.py

# Open the HTML index (on macOS)
open demos/interview_annotations_index.html

# Or view in browser by navigating to:
# file:///path/to/uruguay-interview/demos/interview_annotations_index.html
```

## Note

These are standalone demonstration files. For the full dashboard experience, use:
```bash
make dashboard
```