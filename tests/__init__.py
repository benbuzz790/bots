"""Test Suite for the Bots Framework

This package contains tests for the bots framework, following these key principles:
- No mocking: All tests run against real APIs
- Tests handle real-world conditions and timing
- Failures provide valuable information about API behavior
- Focus on practical reliability and reproducibility

The test suite covers:
- Foundation layer (base classes, LLM implementations)
- Flows layer (functional patterns, task flows)
- Tools layer (built-in tool implementations)
- Dev layer (development utilities)

Note: API keys must be properly configured in environment variables before running tests.
See README.md for setup instructions.
"""
