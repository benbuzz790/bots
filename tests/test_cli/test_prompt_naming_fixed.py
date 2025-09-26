#!/usr/bin/env python3
"""
Fixed version of prompt naming test with proper max_tokens for Haiku
"""

import re
import time


def generate_prompt_name_haiku_fixed(prompt_text: str) -> str:
    """Generate a name for the prompt using Claude Haiku with proper token limits."""
    try:
        from bots.foundation.anthropic_bots import AnthropicBot
        from bots.foundation.base import Engines

        print("Attempting to create Haiku bot with proper token limits...")
        # Create a Haiku bot with appropriate max_tokens for naming
        naming_bot = AnthropicBot(model_engine=Engines.CLAUDE3_HAIKU, max_tokens=100)
        print("Haiku bot created successfully with max_tokens=100")

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


def test_fixed_naming():
    """Test the fixed prompt naming functionality."""

    # Test cases
    test_prompts = [
        "Write a Python function to calculate fibonacci numbers",
        "Explain quantum computing in simple terms for beginners",
        "Help me debug this code",
        "What's the weather like?",
        "Create a REST API endpoint for user authentication",
    ]

    print("=" * 60)
    print("TESTING FIXED PROMPT NAMING FUNCTIONALITY")
    print("=" * 60)

    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n--- Test {i} ---")
        print(f"Prompt: {prompt}")
        print(f"Length: {len(prompt)} characters")

        try:
            name = generate_prompt_name_haiku_fixed(prompt)
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


if __name__ == "__main__":
    print("FIXED PROMPT NAMING FUNCTIONALITY TEST")
    print("=" * 60)

    test_fixed_naming()

    print("\nTest complete!")
