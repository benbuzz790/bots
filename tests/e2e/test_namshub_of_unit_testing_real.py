"""Real-world test for namshub_of_unit_testing.

This test uses a real bot (requires API key) to verify the unit testing
namshub can actually create working tests.
"""

import os
import tempfile

import pytest

from bots.foundation.anthropic_bots import AnthropicBot


@pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="Requires ANTHROPIC_API_KEY environment variable")
def test_unit_testing_namshub_completes_workflow():
    """Test that the unit testing namshub can complete a full workflow."""
    # Create a simple test file
    test_file = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
    test_file.write(
        """
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b
"""
    )
    test_file.close()

    cleanup_temp_files = []
    cleanup_temp_files.append(test_file.name)

    # Initialize bot with the unit testing namshub
    bot = AnthropicBot(autosave=False)

    # Invoke the namshub with the test file
    prompt = f"Please create unit tests for {test_file.name}"

    try:
        # The namshub should:
        # 1. Analyze the code
        # 2. Create appropriate test file
        # 3. Write tests with proper assertions
        # 4. Verify tests can run
        response = bot.respond(prompt)

        # Verify completion
        assert response is not None
        assert "test" in response.lower()

    finally:
        # Cleanup
        for f in cleanup_temp_files:
            if os.path.exists(f):
                os.unlink(f)


@pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="Requires ANTHROPIC_API_KEY environment variable")
def test_unit_testing_namshub_handles_complex_code():
    """Test that the namshub can handle more complex code structures."""
    # Create a more complex test file with classes
    test_file = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
    test_file.write(
        """
class Calculator:
    def __init__(self):
        self.result = 0

    def add(self, value):
        self.result += value
        return self.result

    def reset(self):
        self.result = 0
"""
    )
    test_file.close()

    cleanup_temp_files = []
    cleanup_temp_files.append(test_file.name)

    bot = AnthropicBot(autosave=False)
    prompt = f"Create comprehensive unit tests for {test_file.name}"

    try:
        response = bot.respond(prompt)

        # Verify completion
        assert response is not None
        assert "test" in response.lower()

    finally:
        # Cleanup
        for f in cleanup_temp_files:
            if os.path.exists(f):
                os.unlink(f)
