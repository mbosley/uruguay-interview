#!/usr/bin/env python3
"""
Test runner for Uruguay interview project.
Provides different test execution modes for development workflow.
"""
import subprocess
import sys
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Run a command and report results."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)
    
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode == 0:
        print(f"✅ {description} - PASSED")
    else:
        print(f"❌ {description} - FAILED")
    
    return result.returncode == 0


def run_unit_tests():
    """Run unit tests only."""
    return run_command(
        ["python", "-m", "pytest", "tests/unit/", "-m", "unit"],
        "Unit Tests"
    )


def run_integration_tests():
    """Run integration tests."""
    return run_command(
        ["python", "-m", "pytest", "tests/integration/", "-m", "integration"],
        "Integration Tests"
    )


def run_quick_tests():
    """Run quick tests (unit + integration, no slow tests)."""
    return run_command(
        ["python", "-m", "pytest", "tests/", "-m", "not slow and not requires_api"],
        "Quick Tests (Unit + Integration)"
    )


def run_pipeline_verification():
    """Run pipeline verification tests."""
    return run_command(
        ["python", "-m", "pytest", "tests/unit/test_conversation_parser.py", 
         "tests/unit/test_document_processor.py", "-v"],
        "Pipeline Component Verification"
    )


def run_all_tests():
    """Run all tests."""
    return run_command(
        ["python", "-m", "pytest", "tests/", "-v"],
        "All Tests"
    )


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="Test runner for Uruguay interview project")
    parser.add_argument(
        "test_type",
        choices=["unit", "integration", "quick", "pipeline", "all"],
        help="Type of tests to run"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    print("Uruguay Interview Project - Test Runner")
    print(f"Python: {sys.version}")
    print(f"Working directory: {Path.cwd()}")
    
    # Map test types to functions
    test_runners = {
        "unit": run_unit_tests,
        "integration": run_integration_tests,
        "quick": run_quick_tests,
        "pipeline": run_pipeline_verification,
        "all": run_all_tests
    }
    
    success = test_runners[args.test_type]()
    
    print(f"\n{'='*60}")
    if success:
        print("🎉 All selected tests PASSED!")
        sys.exit(0)
    else:
        print("💥 Some tests FAILED!")
        sys.exit(1)


if __name__ == "__main__":
    main()