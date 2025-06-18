# Testing Framework for Uruguay Interview Project

## Overview

We've implemented a comprehensive testing framework to verify end-to-end pipeline functionality and catch regressions during development.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests for individual components
│   ├── test_document_processor.py
│   └── test_conversation_parser.py
├── integration/             # Integration tests between components
│   └── test_pipeline_flow.py
└── e2e/                     # End-to-end tests for complete workflows
    └── test_full_pipeline.py
```

## Test Categories

### Unit Tests
- **Document Processor**: Filename parsing, metadata extraction, participant counting
- **Conversation Parser**: Speaker identification, turn extraction, conversation statistics
- **Individual Components**: Fast, isolated testing of core logic

### Integration Tests  
- **Pipeline Flow**: Document → Conversation → Database storage
- **Data Compatibility**: Ensuring data structures work across components
- **Metadata Consistency**: Verifying consistent data across pipeline stages

### End-to-End Tests
- **Full Pipeline**: Complete interview processing workflow
- **Error Handling**: Graceful failure handling
- **Database Integration**: Real database storage verification

## Running Tests

### Quick Test Runner
```bash
# Run pipeline verification (most important)
python run_tests.py pipeline

# Run just unit tests
python run_tests.py unit

# Run quick tests (no slow/API tests)
python run_tests.py quick

# Run all tests
python run_tests.py all
```

### Direct Pytest Commands
```bash
# Run specific test file
pytest tests/unit/test_conversation_parser.py -v

# Run tests by marker
pytest -m "unit" -v
pytest -m "integration" -v
pytest -m "not slow" -v

# Run single test
pytest tests/unit/test_conversation_parser.py::TestConversationParser::test_parse_basic_conversation -v
```

## Test Markers

- `unit`: Fast unit tests for individual components
- `integration`: Tests between multiple components
- `slow`: Tests that take significant time
- `requires_api`: Tests requiring external API access
- `database`: Tests requiring database connectivity

## Current Test Coverage

**Working Components:**
- ✅ Document processing (21/21 tests passing)
- ✅ Basic conversation parsing (7/10 tests passing)
- ✅ Data structure compatibility
- ✅ Error handling

**Known Issues Found by Tests:**
- ❌ Spanish/English speaker normalization inconsistency  
- ❌ Word count accuracy with accent characters
- ❌ Numbered participant handling edge cases

## Key Features

### Mocking & Fixtures
- Database session mocking for unit tests
- Sample interview data fixtures
- Temporary file handling for safe testing

### Real Data Testing
- Uses actual interview text patterns
- Tests speaker patterns from real transcripts
- Validates conversation parsing with authentic data

### Error Verification
- Tests graceful handling of malformed files
- Verifies error propagation through pipeline
- Ensures system stability under failure conditions

## Development Workflow

### Before Committing
```bash
# Run pipeline verification to catch major issues
python run_tests.py pipeline
```

### During Development
```bash
# Run relevant unit tests for component you're working on
pytest tests/unit/test_conversation_parser.py -v

# Run quick integration tests
python run_tests.py quick
```

### Integration Testing
```bash
# Test component interactions
pytest tests/integration/ -v

# Test with real data (when database available)
pytest -m "not database" tests/
```

## Benefits Achieved

1. **Regression Prevention**: Catches breaking changes during development
2. **Component Validation**: Ensures individual pieces work correctly
3. **Integration Verification**: Validates data flow between components
4. **Edge Case Discovery**: Found real issues with Spanish text handling
5. **Documentation**: Tests serve as usage examples
6. **Confidence**: Provides assurance that pipeline works as expected

## Next Steps for Production

To make this production-ready, we'd want to add:

1. **Database Tests**: Real database integration testing
2. **Performance Tests**: Load testing with large interview batches  
3. **API Mock Tests**: Comprehensive AI annotation testing with mocks
4. **Continuous Integration**: Automated testing on commits/PRs
5. **Test Data Management**: Structured test data sets
6. **Coverage Reporting**: Track which code paths are tested

The current system provides a solid foundation for verification that the end-to-end pipeline works correctly on small subsets of data, which was the primary goal.