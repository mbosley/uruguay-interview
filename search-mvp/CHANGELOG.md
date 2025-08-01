# Changelog

All notable changes to the Uruguay Interview Research System will be documented in this file.

## [Unreleased] - 2025-01-30

### Added
- **Hyperlink-friendly citation format**: Changed from `(064:23)` to `[[064:23]]` format for easy conversion to hyperlinks
- **Debug mode**: Added `--debug` flag for detailed execution logging and troubleshooting
- **Configurable output width**: Added `--width` parameter to control text wrapping (default: 80 characters)
- **Full scratchpad note display**: Shows complete notes when added to scratchpad instead of truncated versions
- **Informative search previews**: Enhanced preview generation for search results showing match counts and interview spread
- **Modular architecture**: Refactored monolithic `interview_research_agent_improved.py` (1939 lines) into clean modules:
  - `src/agent/research_agent.py`: Core agent logic
  - `src/agent/logger.py`: Enhanced logging with colors
  - `src/agent/config.py`: Configuration management
  - `src/agent/tools.py`: Tool execution
  - `src/agent/events.py`: Event handling
  - `src/agent/prompts.py`: System prompts
  - `src/agent/report_generator.py`: Report generation

### Changed
- **Improved logging**: Tool calls now show descriptive messages instead of raw JSON arguments
- **Better visual demarcators**: Section separators now match the configured width setting
- **Enhanced CLI output**: Clearer formatting with proper text wrapping for all output types
- **Consistent report generation**: Always generates UN-style reports when sufficient data (≥3 tool calls)

### Fixed
- **"expected str instance, dict found" error**: Fixed in both summary generation and `get_interview_turn` tool
- **EventStore attribute error**: Fixed by using `publish()` instead of `add_event()`
- **Debug mode naming conflict**: Renamed internal attribute to avoid conflict with `debug()` method
- **Report generation trigger**: Fixed inconsistent triggering by removing content-based conditions
- **Theme extraction**: Fixed extraction from dict objects in interview previews

### Technical Details

#### Citation Format Update
```python
# Old format
citation = "(064:23)"  # Hard to make into hyperlinks

# New format
citation = "[[064:23]]"  # Easy to parse and convert to links
```

#### Enhanced Logging Examples
```python
# Old: Raw JSON
🔧 search_interviews({"query": "healthcare access", "max_results": 10})

# New: Descriptive
🔧 Searching for "healthcare access"
```

#### Modular Structure Benefits
- Easier maintenance and testing
- Clear separation of concerns
- Reduced cognitive load when working on specific features
- Better code reusability

## Previous Versions

### [1.0.0] - 2025-01-25
- Initial release with web interface and command-line tools
- Basic research agent functionality
- Interview corpus analysis tools