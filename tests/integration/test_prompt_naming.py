#!/usr/bin/env python3
"""
Standalone test for the prompt naming functionality from cli.py
Tests both the Haiku naming and fallback mechanisms.
"""

import re
import time
import pytest


pytestmark = pytest.mark.integration

def test_prompt_naming():
    """Test the prompt naming functionality with various scenarios."""

    def generate_prompt_name_haiku(prompt_text: str) -> str:
        """Generate a name for the prompt using Claude Haiku (from cli.py)."""
        try:
            from bots.foundation.anthropic_bots import AnthropicBot
            from bots.foundation.base import Engines

            print("Attempting to create Haiku bot...")
            # Create a quick Haiku bot for naming
            naming_bot = AnthropicBot(model_engine=Engines.CLAUDE3_HAIKU)
            print("Haiku bot created successfully")

            # Truncate prompt if too long for naming
            truncated_prompt = prompt_text[:500] + "..." if len(prompt_text) > 500 else prompt_text

            naming_prompt = f"""Generate a short, descriptive name (2-4 words, snake_case) for this prompt:

{truncated_prompt}

Respond with just the name, no explanation."""

            print("Sending naming request to Haiku...")
            response = naming_bot.respond(naming_prompt)
            print(f"Raw Haiku response: '{response}'")

            # Clean up the response - extract just the name
            name = response.strip().lower()
            print(f"After strip/lower: '{name}'")

            # Remove any non-alphanumeric characters except underscores
            name = re.sub(r"[^a-z0-9_]", "", name)
            print(f"After regex cleanup: '{name}'")

            # Ensure it's not empty
            if not name:
                name = "unnamed_prompt"
                print(f"Empty name, using fallback: '{name}'")

            return name

        except Exception as e:
            print(f"Haiku naming failed with error: {e}")
            print(f"Error type: {type(e).__name__}")
            # Fallback to timestamp-based name
            fallback_name = f"prompt_{int(time.time())}"
            print(f"Using timestamp fallback: '{fallback_name}'")
            return fallback_name

    # Test cases
    test_prompts = [
        "Write a Python function to calculate fibonacci numbers",
        "Explain quantum computing in simple terms for beginners",
        "Create a detailed project plan for building a web application with user authentication, "
        "database integration, and real-time notifications",
        "Help me debug this code",
        "What's the weather like?",
        # Long prompt to test truncation
        "This is a very long prompt that should be truncated when sent to the naming model. " * 20
        + "What do you think about this approach to handling very long prompts in the system?",
    ]

    print("=" * 60)
    print("TESTING PROMPT NAMING FUNCTIONALITY")
    print("=" * 60)

    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n--- Test {i} ---")
        print(f"Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
        print(f"Full length: {len(prompt)} characters")

        try:
            name = generate_prompt_name_haiku(prompt)
            print(f"Generated name: '{name}'")

            # Validate the name format
            if re.match(r"^[a-z0-9_]+$", name):
                print("✓ Name format is valid (snake_case)")
            else:
                print("✗ Name format is invalid")

        except Exception as e:
            print(f"✗ Test failed with error: {e}")

        print("-" * 40)

    print(f"\n{'=' * 60}")
    print("TESTING COMPLETE")
    print("=" * 60)


def test_fallback_only():
    """Test just the fallback mechanism without trying Haiku."""
    print("\n--- Testing Fallback Mechanism Only ---")

    # Simulate the fallback
    fallback_name = f"prompt_{int(time.time())}"
    print(f"Fallback name: '{fallback_name}'")

    # Test that it's a valid format
    if re.match(r"^prompt_\d+$", fallback_name):
        print("✓ Fallback format is valid")
    else:
        print("✗ Fallback format is invalid")


def check_dependencies():
    """Check if required dependencies are available."""
    print("--- Checking Dependencies ---")

    try:
        from bots.foundation.base import Engines

        print("✓ bots.foundation.base imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import bots.foundation.base: {e}")
        return False

    try:
        from bots.foundation.anthropic_bots import AnthropicBot

        print("✓ bots.foundation.anthropic_bots imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import bots.foundation.anthropic_bots: {e}")
        return False

    try:
        # Try to create a bot to test API access
        AnthropicBot(model_engine=Engines.CLAUDE3_HAIKU)
        print("✓ AnthropicBot created successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to create AnthropicBot: {e}")
        print("This might be due to missing API keys or network issues")
        return False


if __name__ == "__main__":
    print("PROMPT NAMING FUNCTIONALITY TEST")
    print("=" * 60)

    # Check dependencies first
    deps_ok = check_dependencies()

    if deps_ok:
        print("\n✓ Dependencies check passed, running full test...")
        test_prompt_naming()
    else:
        print("\n✗ Dependencies check failed, running fallback test only...")
        test_fallback_only()

    print("\nTest complete!")
