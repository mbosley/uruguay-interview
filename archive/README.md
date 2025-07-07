# Archive Directory

This directory contains obsolete or superseded files from earlier iterations of the project. These files are preserved for historical reference but are no longer actively used.

## Contents

### `/scripts/`
- **Annotation Scripts**: Earlier versions of the annotation pipeline before MFT integration
  - `fast_annotate.py` - Early optimization attempt
  - `final_production_annotate.py` - Previous production version
  - `optimized_batch_annotate.py` - Batch processing experiment
  - `production_annotate_all.py` - Full dataset annotation script
  - `robust_annotate.py` - Error-handling focused version

### `/database/`
- **Database Models**: Previous schema versions before consolidation
  - `models_original.py` - Initial database schema
  - `models_enhanced.py` - Enhanced schema with turn analysis
  - `models_turns.py` - Turn-specific models

### `/pipeline/`
- **Annotator Implementations**: Earlier annotation engine versions
  - `instructor_*.py` - Instructor library-based implementations
  - `json_mode_annotator.py` - Early JSON mode implementation
  - `progressive_annotator.py` - Progressive annotation experiment

### `/dashboard/`
- **Dashboard Versions**: Earlier UI implementations
  - `app_original.py` - Initial dashboard
  - `enhanced_app.py` - Enhanced features version
  - `chat_interface.py` - Original chat interface
  - `interactive_chat_interface.py` - Interactive features added

## Current Replacements

| Archived File | Current Replacement |
|--------------|-------------------|
| `production_annotate_all.py` | `scripts/annotate_interviews.py` |
| `models_enhanced.py` | `src/database/models.py` |
| `enhanced_json_annotator.py` | `src/pipeline/annotation/json_annotator.py` |
| `holistic_chat_interface.py` | `src/dashboard/chat_interface.py` |

## Note

These files are kept for reference and should not be imported or used in the current codebase. All imports have been updated to use the new file locations and names.