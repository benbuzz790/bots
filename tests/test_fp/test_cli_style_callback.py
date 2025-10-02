"""End-to-end test simulating CLI usage of par_branch_while."""

from bots.flows.functional_prompts import conditions, par_branch_while
from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import Engines


def test_cli_like_callback_usage():
    """Simulate how the CLI creates and uses callbacks with par_branch_while."""

    # Simulate CLI context (unpicklable)
    class CLIContext:
        def __init__(self):
            self.message_count = 0
            self.verbose = True

        def create_callback(self):
            # This creates a closure that captures self, making it unpicklable
            def callback(responses, nodes):
                self.message_count += len(responses)
                if self.verbose:
                    for i, response in enumerate(responses):
                        print(f"  Branch {i+1}: {response[:60]}...")

            return callback

    # Create CLI context and callback
    context = CLIContext()
    cli_callback = context.create_callback()

    # Verify callback is unpicklable
    import pickle

    try:
        pickle.dumps(cli_callback)
        print("ERROR: Callback should not be picklable!")
        return False
    except Exception:
        print("✓ Confirmed: CLI-style callback is not picklable")

    # Create bot
    bot = AnthropicBot(api_key=None, model_engine=Engines.CLAUDE37_SONNET_20250219, name="CLIBot", autosave=False)

    # Use par_branch_while with CLI-style callback
    print("\nExecuting par_branch_while with CLI-style callback...")
    prompts = ["Analyze approach A", "Analyze approach B", "Analyze approach C"]

    try:
        responses, nodes = par_branch_while(
            bot, prompts, stop_condition=conditions.tool_not_used, continue_prompt="ok", callback=cli_callback
        )

        print(f"\n✓ SUCCESS: Completed with {len(responses)} responses")
        print(f"✓ Context tracked {context.message_count} messages")
        print(f"✓ All responses valid: {all(r is not None for r in responses)}")
        print(f"✓ All nodes valid: {all(n is not None for n in nodes)}")

        # Verify results
        assert len(responses) == 3
        assert all(r is not None for r in responses)
        assert context.message_count == 3

        print("\n✓ ALL ASSERTIONS PASSED")
        return True

    except Exception as e:
        print(f"\n✗ FAILED: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("CLI-STYLE CALLBACK TEST")
    print("=" * 70)
    success = test_cli_like_callback_usage()
    exit(0 if success else 1)
