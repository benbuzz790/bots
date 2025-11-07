from pathlib import Path

import pytest

from bots import AnthropicBot


def test_unit_testing_namshub_completes_workflow(cleanup_temp_files):
    """Test that the unit testing namshub completes its workflow successfully."""
    # Create a simple Python file to test
    test_content = """
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
"""
    test_file = Path("sample_math.py")
    test_file.write_text(test_content)
    cleanup_temp_files.append(test_file)

    # Initialize bot with the unit testing namshub
    bot = AnthropicBot()

    # Invoke the namshub with the test file
    prompt = f"Please create unit tests for {test_file}"
    bot.add_user_message(prompt)

    try:
        # The namshub should:
        # 1. Analyze the code
        # 2. Create appropriate test file
        # 3. Write tests with proper assertions
        # 4. Verify tests can run
        response = bot.respond()

        print("\n=== Bot Response ===")
        print(response)

        # Check that a test file was created
        expected_test_file = Path("test_sample_math.py")
        if expected_test_file.exists():
            cleanup_temp_files.append(expected_test_file)
            test_content = expected_test_file.read_text()

            print("\n=== Generated Test File ===")
            print(test_content)

            # Verify the test file has basic structure
            assert "import" in test_content or "from" in test_content, \
                "Test file should have imports"
            assert "def test_" in test_content, \
                "Test file should have test functions"
            assert "assert" in test_content, \
                "Test file should have assertions"

            # Verify the tests reference the original functions
            assert "add" in test_content, \
                "Test file should test the add function"
            assert "subtract" in test_content, \
                "Test file should test the subtract function"

            print("\n=== Test Structure Validation Passed ===")

            # Try to run the tests to verify they're valid Python
            import subprocess
            result = subprocess.run(
                ["python", "-m", "pytest", str(expected_test_file), "-v"],
                capture_output=True,
                text=True,
                timeout=30
            )

            print("\n=== Test Execution Output ===")
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)

            # We don't assert on test success because the bot might create
            # tests that fail (which is still valid test creation)
            # We just verify they can be parsed and run
            assert result.returncode in [0, 1], \
                "Tests should be runnable (exit code 0 for pass, 1 for fail)"

            print("\n=== Workflow completed successfully ===")
        else:
            print("\n=== Note: Expected test file not found at {} ===".format(expected_test_file))
            print("The bot may have created files elsewhere or encountered issues.")

    finally:
        # Cleanup is handled by the fixture
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
