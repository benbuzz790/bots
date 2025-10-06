#!/usr/bin/env python3
"""
Enhanced test suite for CLI prompt functionality:
1. Save prompts with Haiku naming validation
2. Load prompts with pre-fill functionality
3. Search functionality with edge cases
4. Recency tracking validation
5. Name uniqueness and collision handling
"""

import pytest
import json
import os
import re
import tempfile
import time
from pathlib import Path



pytestmark = pytest.mark.e2e

def validate_snake_case_name(name: str) -> bool:
    """Validate that a name follows snake_case convention."""
    return bool(re.match(r"^[a-z0-9_]+$", name))


def validate_haiku_generated_name(name: str) -> bool:
    """Validate that a name appears to be Haiku-generated (not timestamp fallback)."""
    # Should not be timestamp format (prompt_<digits>)
    if re.match(r"^prompt_\d+$", name):
        return False
    # Should be snake_case
    if not validate_snake_case_name(name):
        return False
    # Should be reasonable length (2-50 chars, typical for descriptive names)
    if len(name) < 2 or len(name) > 50:
        return False
    return True


def test_prompt_naming_comprehensive():
    """Comprehensive test of prompt naming with various input types."""
    print("=== Testing Comprehensive Prompt Naming ===")

    from bots.dev.cli import PromptManager

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_file = f.name

    test_cases = [
        {
            "prompt": "Write a Python function to calculate the factorial of a number using recursion",
            "expected_keywords": ["factorial", "recursive", "python", "function"],
            "description": "Mathematical function prompt",
        },
        {
            "prompt": "Explain quantum computing concepts for beginners",
            "expected_keywords": ["quantum", "computing", "explain", "concepts"],
            "description": "Educational explanation prompt",
        },
        {
            "prompt": "Debug this JavaScript code that's throwing an error",
            "expected_keywords": ["debug", "javascript", "code", "error"],
            "description": "Debugging prompt",
        },
        {
            "prompt": "Create a REST API endpoint with JWT authentication",
            "expected_keywords": ["rest", "api", "endpoint", "auth", "jwt"],
            "description": "API development prompt",
        },
        {
            "prompt": "Help me write unit tests for my React components",
            "expected_keywords": ["unit", "test", "react", "component"],
            "description": "Testing prompt",
        },
    ]

    try:
        pm = PromptManager(prompts_file=temp_file)
        results = []

        for i, test_case in enumerate(test_cases, 1):
            print(f"\nTest {i}: {test_case['description']}")
            print(f"Prompt: {test_case['prompt']}")

            # Save the prompt
            generated_name = pm.save_prompt(test_case["prompt"])
            print(f"Generated name: '{generated_name}'")

            # Validate the name
            is_haiku_generated = validate_haiku_generated_name(generated_name)
            is_snake_case = validate_snake_case_name(generated_name)

            # Check if name contains relevant keywords (loose check)
            name_lower = generated_name.lower()
            keyword_matches = sum(1 for keyword in test_case["expected_keywords"] if keyword in name_lower)

            test_result = {
                "test_case": test_case["description"],
                "prompt": test_case["prompt"],
                "generated_name": generated_name,
                "is_haiku_generated": is_haiku_generated,
                "is_snake_case": is_snake_case,
                "keyword_matches": keyword_matches,
                "total_keywords": len(test_case["expected_keywords"]),
                "success": is_haiku_generated and is_snake_case,
            }

            results.append(test_result)

            # Print validation results
            print(f"  ✅ Haiku generated: {is_haiku_generated}")
            print(f"  ✅ Snake case: {is_snake_case}")
            print(f"  📊 Keyword relevance: {keyword_matches}/{len(test_case['expected_keywords'])}")

            if not test_result["success"]:
                print(f"  ❌ Test failed for: {test_case['description']}")
            else:
                print(f"  ✅ Test passed for: {test_case['description']}")

        # Summary
        passed_tests = sum(1 for r in results if r["success"])
        total_tests = len(results)

        print("\n--- Naming Test Summary ---")
        print(f"Passed: {passed_tests}/{total_tests}")
        print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")

        return passed_tests == total_tests, results

    except Exception as e:
        print(f"❌ Error during comprehensive naming test: {e}")
        return False, []
    finally:
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def test_search_functionality_enhanced():
    """Enhanced search functionality test with edge cases."""
    print("\n=== Testing Enhanced Search Functionality ===")

    from bots.dev.cli import PromptManager

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_file = f.name

    try:
        pm = PromptManager(prompts_file=temp_file)

        # Test prompts with known content for search validation
        test_data = [
            ("Write a Python function for fibonacci numbers", "python"),
            ("Create a JavaScript async function", "javascript"),
            ("Explain machine learning algorithms", "machine learning"),
            ("Debug Python code with pandas", "python"),
            ("Write SQL queries for data analysis", "sql"),
            ("Create React components with hooks", "react"),
        ]

        saved_prompts = {}
        print("Saving test prompts...")
        for prompt, category in test_data:
            name = pm.save_prompt(prompt)
            saved_prompts[name] = (prompt, category)
            print(f"  Saved: '{name}' ({category})")

        # Test cases for search
        search_tests = [
            {"query": "python", "expected_min_results": 2, "description": "Search for Python-related prompts"},
            {"query": "function", "expected_min_results": 2, "description": "Search for function-related prompts"},
            {"query": "javascript", "expected_min_results": 1, "description": "Search for JavaScript prompts"},
            {"query": "nonexistent_term", "expected_min_results": 0, "description": "Search for non-existent term"},
            {"query": "", "expected_min_results": 0, "description": "Empty search (should return recents)"},
        ]

        search_results = []
        for test in search_tests:
            print(f"\n{test['description']}: '{test['query']}'")
            results = pm.search_prompts(test["query"])

            success = len(results) >= test["expected_min_results"]
            search_results.append(success)

            print(f"  Found: {len(results)} results (expected >= {test['expected_min_results']})")
            print(f"  Result: {'✅ PASS' if success else '❌ FAIL'}")

            # Show results for non-empty searches
            if results and test["query"]:
                for name, content in results[:3]:  # Show first 3
                    print(f"    - {name}: {content[:50]}...")

        all_passed = all(search_results)
        print(f"\nSearch tests passed: {sum(search_results)}/{len(search_results)}")

        return all_passed

    except Exception as e:
        print(f"❌ Error during enhanced search test: {e}")
        return False
    finally:
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def test_recency_tracking():
    """Test that recency tracking works correctly."""
    print("\n=== Testing Recency Tracking ===")

    from bots.dev.cli import PromptManager

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_file = f.name

    try:
        pm = PromptManager(prompts_file=temp_file)

        # Save multiple prompts
        prompts = [
            "First prompt for testing recency",
            "Second prompt for testing recency",
            "Third prompt for testing recency",
            "Fourth prompt for testing recency",
            "Fifth prompt for testing recency",
            "Sixth prompt for testing recency",  # This should push first out of recents
        ]

        saved_names = []
        for prompt in prompts:
            name = pm.save_prompt(prompt)
            saved_names.append(name)
            print(f"Saved: {name}")
            time.sleep(0.1)  # Small delay to ensure different timestamps

        # Check recents list (should be last 5)
        recents = pm.prompts_data["recents"]
        print(f"\nRecents list: {recents}")
        print(f"Recents count: {len(recents)} (should be <= 5)")

        # Verify recents are in reverse chronological order (most recent first)
        expected_recents = saved_names[-5:][::-1]  # Last 5, reversed
        recents_match = recents == expected_recents

        print(f"Expected recents: {expected_recents}")
        print(f"Actual recents: {recents}")
        print(f"Recents order correct: {'✅ PASS' if recents_match else '❌ FAIL'}")

        # Test loading a prompt updates recency
        if len(saved_names) >= 3:
            old_prompt_name = saved_names[1]  # Load an older prompt
            print(f"\nLoading older prompt: {old_prompt_name}")
            pm.load_prompt(old_prompt_name)

            new_recents = pm.prompts_data["recents"]
            moved_to_front = new_recents[0] == old_prompt_name
            print(f"Prompt moved to front of recents: {'✅ PASS' if moved_to_front else '❌ FAIL'}")

            return len(recents) <= 5 and moved_to_front

        return len(recents) <= 5

    except Exception as e:
        print(f"❌ Error during recency test: {e}")
        return False
    finally:
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def test_name_uniqueness():
    """Test that duplicate names are handled correctly."""
    print("\n=== Testing Name Uniqueness ===")

    from bots.dev.cli import PromptManager

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_file = f.name

    try:
        pm = PromptManager(prompts_file=temp_file)

        # Save similar prompts that might generate similar names
        similar_prompts = [
            "Write a Python function to calculate fibonacci",
            "Create a Python function for fibonacci sequence",
            "Implement fibonacci in Python",
        ]

        saved_names = []
        for prompt in similar_prompts:
            name = pm.save_prompt(prompt)
            saved_names.append(name)
            print(f"Saved: '{name}' for prompt: {prompt}")

        # Check that all names are unique
        unique_names = len(set(saved_names)) == len(saved_names)
        print(f"\nAll names unique: {'✅ PASS' if unique_names else '❌ FAIL'}")

        # Check for expected naming pattern (base_name, base_name_1, base_name_2, etc.)
        if not unique_names:
            print("Duplicate names found:")
            for name in saved_names:
                count = saved_names.count(name)
                if count > 1:
                    print(f"  '{name}' appears {count} times")

        return unique_names

    except Exception as e:
        print(f"❌ Error during uniqueness test: {e}")
        return False
    finally:
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def test_cli_integration():
    """Test CLI integration aspects."""
    print("\n=== Testing CLI Integration ===")

    try:
        from bots.dev.cli import CLIContext, PromptHandler
        from bots.foundation.anthropic_bots import AnthropicBot


        # Create a mock CLI context
        context = CLIContext()
        context.bot_instance = AnthropicBot()

        # Create prompt handler
        handler = PromptHandler()

        # Test save functionality
        save_result = handler.save_prompt(context.bot_instance, context, ["Test", "prompt", "for", "CLI", "integration"])

        print(f"Save result: {save_result}")
        success = "Saved prompt as:" in save_result
        print(f"Save integration: {'✅ PASS' if success else '❌ FAIL'}")

        # Test load functionality (this would normally be interactive)
        # We'll just test that the method exists and can be called
        try:
            # This will fail because it tries to get input, but we can catch that
            handler.load_prompt(context.bot_instance, context, ["test"])
        except (EOFError, KeyboardInterrupt):
            # Expected when running non-interactively
            pass

        print("Load integration: ✅ PASS (method callable)")

        return success

    except Exception as e:
        print(f"❌ Error during CLI integration test: {e}")
        return False


def show_current_prompts():
    """Show what prompts are currently saved."""
    print("=== Current Saved Prompts ===")

    prompts_file = Path("bots/prompts.json")
    if prompts_file.exists():
        try:
            with open(prompts_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            prompts = data.get("prompts", {})
            recents = data.get("recents", [])

            print(f"Total prompts: {len(prompts)}")
            print(f"Recent prompts: {recents}")

            if prompts:
                print("\nAll prompts:")
                for name, content in prompts.items():
                    preview = content[:80] + "..." if len(content) > 80 else content
                    print(f"  - {name}: {preview}")
            else:
                print("No prompts found.")

        except Exception as e:
            print(f"Error reading prompts file: {e}")
    else:
        print("No prompts file found at bots/prompts.json")


if __name__ == "__main__":
    print("ENHANCED CLI PROMPT FUNCTIONALITY TEST SUITE")
    print("=" * 60)

    # Show existing prompts first
    show_current_prompts()

    # Run all tests
    tests = [
        ("Comprehensive Naming", test_prompt_naming_comprehensive),
        ("Enhanced Search", test_search_functionality_enhanced),
        ("Recency Tracking", test_recency_tracking),
        ("Name Uniqueness", test_name_uniqueness),
        ("CLI Integration", test_cli_integration),
    ]

    results = {}
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        try:
            if test_name == "Comprehensive Naming":
                success, detailed_results = test_func()
                results[test_name] = success
            else:
                success = test_func()
                results[test_name] = success
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with exception: {e}")
            results[test_name] = False

    # Final summary
    print(f"\n{'='*60}")
    print("FINAL TEST RESULTS:")
    print("=" * 60)

    passed_count = 0
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:.<40} {status}")
        if success:
            passed_count += 1

    total_tests = len(results)
    success_rate = (passed_count / total_tests) * 100

    print(f"\nOverall Results: {passed_count}/{total_tests} tests passed ({success_rate:.1f}%)")

    if passed_count == total_tests:
        print("\n🎉 ALL TESTS PASSED! The CLI prompt functionality is working correctly.")
        print("\nTo test the complete user experience:")
        print("1. Run: python -m bots.dev.cli")
        print("2. Save a prompt: /s Write a function to sort a list")
        print("3. Load with search: /p sort")
        print("4. The prompt should pre-fill in your input field for editing!")
    else:
        print(f"\n⚠️  {total_tests - passed_count} test(s) failed. Check the output above for details.")
        print("The CLI may still work, but some functionality might not be optimal.")
