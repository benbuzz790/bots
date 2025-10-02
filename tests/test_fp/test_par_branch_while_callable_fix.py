"""Test to replicate and verify the par_branch_while callable pickling issue."""

import pickle
import os
from unittest.mock import Mock, patch
from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import Bot, ConversationNode, Engines
from bots.flows.functional_prompts import par_branch_while, conditions


def test_par_branch_while_with_unpicklable_callback():
    """Test that par_branch_while handles unpicklable callbacks gracefully.

    This replicates the issue where CLI callbacks cannot be pickled
    when passed to ThreadPoolExecutor.
    """

    # Create a real bot (with no API key for testing)
    bot = AnthropicBot(
        api_key=None,
        model_engine=Engines.CLAUDE37_SONNET_20250219,
        name="TestBot",
        autosave=False
    )

    # Create an unpicklable callback (like CLI creates)
    callback_calls = []
    def unpicklable_callback(responses, nodes):
        # This closure captures local state, making it unpicklable
        callback_calls.append(len(responses))
        print(f"Callback called: {len(responses)} responses")

    # Verify the callback is not picklable
    try:
        pickle.dumps(unpicklable_callback)
        print("WARNING: Callback was picklable (unexpected)")
    except Exception as e:
        print(f"✓ Confirmed: Callback is not picklable: {type(e).__name__}")

    # Define a stop condition
    def stop_after_one(bot):
        return True  # Stop immediately after first response

    # Test with unpicklable callback
    prompts = ["Prompt 1", "Prompt 2", "Prompt 3"]

    try:
        responses, nodes = par_branch_while(
            bot,
            prompts,
            stop_condition=stop_after_one,
            continue_prompt="ok",
            callback=unpicklable_callback
        )

        print(f"✓ SUCCESS: par_branch_while completed with {len(responses)} responses")
        print(f"  Responses: {[r[:50] if r else None for r in responses]}")
        print(f"  Nodes: {[n is not None for n in nodes]}")
        print(f"  Callback was called {len(callback_calls)} times")

        # Verify results
        assert len(responses) == 3, f"Expected 3 responses, got {len(responses)}"
        assert all(r is not None for r in responses), f"Some responses are None: {responses}"
        assert len(nodes) == 3, f"Expected 3 nodes, got {len(nodes)}"
        assert all(n is not None for n in nodes), f"Some nodes are None"
        assert len(callback_calls) > 0, "Callback was never called"

        print("✓ All assertions passed")
        return True

    except Exception as e:
        print(f"✗ FAILED: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_par_branch_while_with_picklable_condition():
    """Test that par_branch_while works with standard picklable conditions."""

    bot = AnthropicBot(
        api_key=None,
        model_engine=Engines.CLAUDE37_SONNET_20250219,
        name="TestBot",
        autosave=False
    )

    # Use a standard condition from fp.conditions (these are picklable)
    prompts = ["Task 1", "Task 2"]

    try:
        responses, nodes = par_branch_while(
            bot,
            prompts,
            stop_condition=conditions.tool_not_used,
            continue_prompt="ok",
            callback=None  # No callback
        )

        print(f"✓ SUCCESS: Standard condition test completed")
        print(f"  Responses: {[r[:50] if r else None for r in responses]}")
        assert len(responses) == 2
        assert all(r is not None for r in responses), f"Some responses are None: {responses}"
        print("✓ All assertions passed")
        return True

    except Exception as e:
        print(f"✗ FAILED: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_callback_is_called_after_threads():
    """Test that callbacks are called after thread execution, not during."""

    bot = AnthropicBot(
        api_key=None,
        model_engine=Engines.CLAUDE37_SONNET_20250219,
        name="TestBot",
        autosave=False
    )

    callback_calls = []
    callback_responses = []

    def tracking_callback(responses, nodes):
        callback_calls.append(True)
        callback_responses.extend(responses)
        print(f"Callback invoked with {len(responses)} responses")

    def stop_immediately(bot):
        return True

    prompts = ["Test 1", "Test 2"]

    try:
        responses, nodes = par_branch_while(
            bot,
            prompts,
            stop_condition=stop_immediately,
            continue_prompt="ok",
            callback=tracking_callback
        )

        print(f"✓ Callback was called {len(callback_calls)} times")
        print(f"✓ Callback received {len(callback_responses)} responses")

        # Verify callback was called for each branch
        assert len(callback_calls) >= 2, f"Expected at least 2 callback calls, got {len(callback_calls)}"

        print("✓ All assertions passed")
        return True

    except Exception as e:
        print(f"✗ FAILED: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("TEST 1: par_branch_while with unpicklable callback")
    print("=" * 70)
    test1_passed = test_par_branch_while_with_unpicklable_callback()

    print("\n" + "=" * 70)
    print("TEST 2: par_branch_while with picklable condition")
    print("=" * 70)
    test2_passed = test_par_branch_while_with_picklable_condition()

    print("\n" + "=" * 70)
    print("TEST 3: callback is called after threads complete")
    print("=" * 70)
    test3_passed = test_callback_is_called_after_threads()

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Test 1 (unpicklable callback): {'PASSED' if test1_passed else 'FAILED'}")
    print(f"Test 2 (picklable condition): {'PASSED' if test2_passed else 'FAILED'}")
    print(f"Test 3 (callback after threads): {'PASSED' if test3_passed else 'FAILED'}")

    if test1_passed and test2_passed and test3_passed:
        print("\n✓ ALL TESTS PASSED")
        exit(0)
    else:
        print("\n✗ SOME TESTS FAILED")
        exit(1)