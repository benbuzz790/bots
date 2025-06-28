import io
import tempfile
import unittest
import os
import shutil
from unittest.mock import patch
import bots.tools.self_tools as self_tools
from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import Engines

class TestSelfTools(unittest.TestCase):
    """Test suite for self_tools module functionality.

    This test suite verifies the behavior of self-introspection and branching
    tools, with particular focus on the debug printing functionality added
    to the branch_self function.

    Attributes:
        temp_dir (str): Temporary directory path for test file operations
        bot (AnthropicBot): Test bot instance with Claude 3.5 Sonnet configuration
    """

    def setUp(self) -> None:
        """Set up test environment before each test.

        Creates a temporary directory and initializes a test AnthropicBot instance
        with Claude 3.5 Sonnet configuration and self_tools loaded.
        """
        self.temp_dir = tempfile.mkdtemp()
        self.bot = AnthropicBot(name="TestBot", max_tokens=1000, model_engine=Engines.CLAUDE35_SONNET_20240620)
        self.bot.add_tools(self_tools)

    def tearDown(self) -> None:
        """Clean up test environment after each test."""
        try:
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(f"Warning: Could not clean up temp directory: {e}")

    def test_get_own_info(self) -> None:
        """Test that get_own_info returns valid bot information."""
        response = self.bot.respond("Please use get_own_info to tell me about yourself")
        follow_up = self.bot.respond("What information did you get about yourself?")
        self.assertNotIn("Error: Could not find calling bot", response)
        self.assertIn("name", follow_up.lower())
        self.assertIn("TestBot", follow_up)

    def test_branch_self_basic_functionality(self) -> None:
        """Test that branch_self function works correctly when called as a tool."""
        response = self.bot.respond("Please create 2 branches with prompts ['Hello world', 'Goodbye world'] using branch_self")
        self.assertNotIn("Error: Could not find calling bot", response)
        self.assertIn("branch", response.lower())
        self.assertIn("two", response.lower())
        follow_up = self.bot.respond("What happened with the branching?")
        self.assertIn("branch", follow_up.lower())

    def test_branch_self_debug_printing(self) -> None:
        """Test that branch_self function works correctly with multiple prompts."""
        response = self.bot.respond("Please create 2 branches with prompts ['Test prompt 1', 'Test prompt 2'] using branch_self")
        self.assertIn("branch", response.lower())

    def test_branch_self_method_restoration(self) -> None:
        """Test that the original respond method is properly restored after branching."""
        # Store the original method's underlying function and instance
        original_func = self.bot.respond.__func__
        original_self = self.bot.respond.__self__
        # Execute branch_self which should temporarily overwrite respond method
        self.bot.respond("Use branch_self with prompts ['Test restoration']")
        # Verify the respond method was restored to the original
        self.assertIs(self.bot.respond.__func__, original_func, "respond method function was not properly restored after branch_self")
        self.assertIs(self.bot.respond.__self__, original_self, "respond method instance was not properly restored after branch_self")

    def test_branch_self_with_allow_work_true(self) -> None:
        """Test branch_self with allow_work=True parameter."""
        response = self.bot.respond("Please create 1 branch with prompts ['Simple task'] using branch_self with allow_work=True")
        self.assertIn("branch", response.lower())

    def test_branch_self_error_handling(self) -> None:
        """Test branch_self error handling with invalid input."""
        response = self.bot.respond("Use branch_self with invalid prompts: 'not a list'")
        self.assertIn("invalid", response.lower())

    def test_branch_self_empty_prompts(self) -> None:
        """Test branch_self with empty prompt list."""
        response = self.bot.respond("Use branch_self with prompts []")
        self.assertIn("empty", response.lower())

    def test_debug_output_format(self) -> None:
        """Test that debug output follows the expected format."""
        captured_output = io.StringIO()
        with patch("sys.stdout", captured_output):
            self.bot.respond("Use branch_self with prompts ['Format test']")
        debug_output = captured_output.getvalue()
        lines = debug_output.split("\n")
        # Find debug sections
        debug_start_lines = [i for i, line in enumerate(lines) if "=== BRANCH" in line and "DEBUG ===" in line]
        debug_end_lines = [i for i, line in enumerate(lines) if "=== END BRANCH" in line and "DEBUG ===" in line]
        # Should have matching start and end markers
        self.assertEqual(len(debug_start_lines), len(debug_end_lines))
        # Each debug section should be properly formatted
        for start_idx, end_idx in zip(debug_start_lines, debug_end_lines):
            section = lines[start_idx:end_idx + 1]
            section_text = "\n".join(section)
            # Should contain required elements
            self.assertIn("PROMPT:", section_text)
            self.assertIn("RESPONSE:", section_text)
            self.assertIn("=" * 50, section_text)  # Separator line

    def test_nested_branch_self_tool_result_isolation(self) -> None:
        """Test that tool results from nested branches don't leak to parent nodes.

    This test creates a scenario where:
    1. Main bot creates 2 subdirectories using branch_self
    2. Each subdirectory branch creates 2 more subdirectories using nested branch_self
    3. Verifies that tool results from nested branches don't contaminate parent nodes
    """
        # Change to temp directory for file operations
        original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        try:
            # Store initial tool handler state
            initial_tool_results_count = len(self.bot.tool_handler.results)
            initial_conversation_tool_results_count = len(self.bot.conversation.tool_results)
            # Create a simpler nested branching scenario
            response = self.bot.respond("""
        Please use branch_self with these prompts:
        ['Create directory dir1, then use branch_self to create 2 subdirs: sub1_1 and sub1_2',
         'Create directory dir2, then use branch_self to create 2 subdirs: sub2_1 and sub2_2']
        Set allow_work=True.
        """)
            # Verify the branching completed successfully
            self.assertIn("branch", response.lower())
            self.assertNotIn("error", response.lower())
            # Critical test: Check tool result isolation
            # After nested branching, the main conversation should not have accumulated
            # tool results from all the nested branches
            final_tool_results_count = len(self.bot.tool_handler.results)
            final_conversation_tool_results_count = len(self.bot.conversation.tool_results)
            # The tool results should not have exploded due to nested branching
            tool_results_increase = final_tool_results_count - initial_tool_results_count
            conversation_tool_results_increase = final_conversation_tool_results_count - initial_conversation_tool_results_count
            print(f"Tool results increased by: {tool_results_increase}")
            print(f"Conversation tool results increased by: {conversation_tool_results_increase}")
            print(f"Main conversation replies count: {len(self.bot.conversation.replies)}")
            # These assertions will likely fail with the current bug, demonstrating the issue
            self.assertLess(tool_results_increase, 15, f"Tool results increased by {tool_results_increase}, suggesting nested tool results leaked to parent")
            self.assertLess(conversation_tool_results_increase, 15, f"Conversation tool results increased by {conversation_tool_results_increase}, suggesting nested tool results leaked to parent")
            # Verify conversation structure integrity
            main_replies_count = len(self.bot.conversation.replies)
            self.assertLess(main_replies_count, 8, f"Main conversation has {main_replies_count} replies, suggesting nested branch contamination")
        finally:
            # Always restore original directory
            os.chdir(original_cwd)

    def test_branch_self_tool_result_contamination_detailed(self) -> None:
        """Detailed test to examine tool result contamination in nested branch_self calls.

    This test specifically examines the tool_handler.results and conversation.tool_results
    to detect if results from nested branches are incorrectly being applied to parent nodes.
    """
        # Change to temp directory for file operations
        original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        try:
            # Capture initial state
            initial_tool_results = list(self.bot.tool_handler.results)
            initial_conversation_tool_results = list(self.bot.conversation.tool_results)
            initial_conversation_id = id(self.bot.conversation)
            initial_conversation_content = self.bot.conversation.content
            print(f"Initial state:")
            print(f"  Tool handler results: {len(initial_tool_results)}")
            print(f"  Conversation tool results: {len(initial_conversation_tool_results)}")
            print(f"  Conversation ID: {initial_conversation_id}")
            print(f"  Conversation content length: {len(initial_conversation_content)}")
            # Execute a simple nested branch scenario
            response = self.bot.respond("""
        Use branch_self with prompts: ['Use get_own_info tool, then use branch_self with prompts ["Use get_own_info again"]']
        Set allow_work=True.
        """)
            # Capture final state
            final_tool_results = list(self.bot.tool_handler.results)
            final_conversation_tool_results = list(self.bot.conversation.tool_results)
            final_conversation_id = id(self.bot.conversation)
            final_conversation_content = self.bot.conversation.content
            print(f"\nFinal state:")
            print(f"  Tool handler results: {len(final_tool_results)}")
            print(f"  Conversation tool results: {len(final_conversation_tool_results)}")
            print(f"  Conversation ID: {final_conversation_id}")
            print(f"  Conversation content length: {len(final_conversation_content)}")
            print(f"  Response: {response[:200]}...")
            # Analyze tool results
            tool_results_added = len(final_tool_results) - len(initial_tool_results)
            conversation_tool_results_added = len(final_conversation_tool_results) - len(initial_conversation_tool_results)
            print(f"\nChanges:")
            print(f"  Tool results added: {tool_results_added}")
            print(f"  Conversation tool results added: {conversation_tool_results_added}")
            print(f"  Conversation ID changed: {initial_conversation_id != final_conversation_id}")
            print(f"  Conversation content changed: {initial_conversation_content != final_conversation_content}")
            # Examine the actual tool results to see if there's contamination
            if tool_results_added > 0:
                print(f"\nNew tool results:")
                for i, result in enumerate(final_tool_results[len(initial_tool_results):]):
                    print(f"  {i}: {type(result).__name__} - {str(result)[:100]}...")
            if conversation_tool_results_added > 0:
                print(f"\nNew conversation tool results:")
                for i, result in enumerate(final_conversation_tool_results[len(initial_conversation_tool_results):]):
                    print(f"  {i}: {type(result).__name__} - {str(result)[:100]}...")
            # The key issue: nested branch_self calls should not cause tool results
            # from sub-branches to be added to the main conversation's tool_results
            # We expect some tool results from the main branch_self call, but not from nested calls
            # Check for excessive tool result contamination
            self.assertLess(conversation_tool_results_added, 10, f"Too many tool results added to main conversation: {conversation_tool_results_added}")
            # Check for excessive tool handler contamination
            self.assertLess(tool_results_added, 15, f"Too many tool results added to tool handler: {tool_results_added}")
            # Document the conversation ID change issue (this is likely part of the bug)
            if initial_conversation_id != final_conversation_id:
                print(f"\nWARNING: Conversation object changed during nested branching!")
                print(f"  This suggests the conversation state management has issues.")
            # Verify the bot is still functional after nested branching
            # Verify the bot is still functional after nested branching
            # Verify the bot is still functional after nested branching
            follow_up = self.bot.respond("What is 2+2?")
            self.assertIn("4", follow_up)
        finally:
            os.chdir(original_cwd)

    def test_parallel_vs_sequential_branching_comparison(self) -> None:
        """Compare parallel vs sequential branching to identify tool result contamination differences."""
        original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        try:
            print("\n=== TESTING SEQUENTIAL BRANCHING ===")
            # Test sequential branching (uses branch_while)
            bot1 = AnthropicBot(name="SequentialBot", 
                                model_engine=Engines.CLAUDE35_SONNET_20240620,
                                max_tokens=1000,
                                )
            bot1.add_tools(self_tools)
            initial_tool_results_seq = len(bot1.tool_handler.results)
            response_seq = bot1.respond("""
        Use branch_self with prompts: ['Use get_own_info tool, then use branch_self with prompts ["Use get_own_info again"]']
        Set allow_work=True and parallel=False.
        """)
            final_tool_results_seq = len(bot1.tool_handler.results)
            print(f"Sequential - Initial tool results: {initial_tool_results_seq}")
            print(f"Sequential - Final tool results: {final_tool_results_seq}")
            print(f"Sequential - Tool results added: {final_tool_results_seq - initial_tool_results_seq}")
            print(f"Sequential - Response success: {'branch' in response_seq.lower() and 'error' not in response_seq.lower()}")
            # Try follow-up
            try:
                follow_up_seq = bot1.respond("What is 2+2?")
                print(f"Sequential - Follow-up success: True")
            except Exception as e:
                print(f"Sequential - Follow-up failed: {str(e)[:100]}")
            print("\n=== TESTING PARALLEL BRANCHING ===")
            # Test parallel branching (uses par_branch_while)
            bot2 = AnthropicBot(name="ParallelBot", max_tokens=1000, model_engine=Engines.CLAUDE35_SONNET_20240620)
            bot2.add_tools(self_tools)
            initial_tool_results_par = len(bot2.tool_handler.results)
            response_par = bot2.respond("""
        Use branch_self with prompts: ['Use get_own_info tool, then use branch_self with prompts ["Use get_own_info again"]']
        Set allow_work=True and parallel=True.
        """)
            final_tool_results_par = len(bot2.tool_handler.results)
            print(f"Parallel - Initial tool results: {initial_tool_results_par}")
            print(f"Parallel - Final tool results: {final_tool_results_par}")
            print(f"Parallel - Tool results added: {final_tool_results_par - initial_tool_results_par}")
            print(f"Parallel - Response success: {'branch' in response_par.lower() and 'error' not in response_par.lower()}")
            # Try follow-up
            try:
                follow_up_par = bot2.respond("What is 2+2?")
                print(f"Parallel - Follow-up success: True")
            except Exception as e:
                print(f"Parallel - Follow-up failed: {str(e)[:100]}")
            print("\n=== COMPARISON ===")
            seq_contamination = final_tool_results_seq - initial_tool_results_seq
            par_contamination = final_tool_results_par - initial_tool_results_par
            print(f"Sequential contamination: {seq_contamination}")
            print(f"Parallel contamination: {par_contamination}")
            print(f"Difference: {abs(seq_contamination - par_contamination)}")
            # The hypothesis is that sequential should have more contamination
            if seq_contamination > par_contamination:
                print("HYPOTHESIS CONFIRMED: Sequential has more tool result contamination")
            else:
                print("HYPOTHESIS REJECTED: Parallel has equal or more contamination")
        finally:
            os.chdir(original_cwd)

    def test_deeper_nesting_stress_test(self) -> None:
        """Test deeper nesting to see if we can still trigger the original issue."""
        original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        try:
            print("\n=== TESTING DEEPER NESTING ===")
            bot = AnthropicBot(name="DeepNestBot", max_tokens=1000, model_engine=Engines.CLAUDE35_SONNET_20240620)
            bot.add_tools(self_tools)
            initial_tool_results = len(bot.tool_handler.results)
            initial_conversation_tool_results = len(bot.conversation.tool_results)
            # Create a more complex nested scenario
            response = bot.respond("""
        Use branch_self with prompts: [
            'Use get_own_info, then use branch_self with prompts ["Use get_own_info, then use branch_self with prompts [\\"Use get_own_info again\\"]"]',
            'Use get_own_info, then use branch_self with prompts ["Use get_own_info, then use branch_self with prompts [\\"Use get_own_info again\\"]"]'
        ]
        Set allow_work=True.
        """)
            final_tool_results = len(bot.tool_handler.results)
            final_conversation_tool_results = len(bot.conversation.tool_results)
            print(f"Initial tool results: {initial_tool_results}")
            print(f"Final tool results: {final_tool_results}")
            print(f"Tool results added: {final_tool_results - initial_tool_results}")
            print(f"Initial conversation tool results: {initial_conversation_tool_results}")
            print(f"Final conversation tool results: {final_conversation_tool_results}")
            print(f"Conversation tool results added: {final_conversation_tool_results - initial_conversation_tool_results}")
            print(f"Response contains 'branch': {'branch' in response.lower()}")
            print(f"Response contains 'error': {'error' in response.lower()}")
            # The critical test - can we still use the bot normally?
            try:
                follow_up = bot.respond("What is 5+5?")
                print(f"Follow-up success: True")
                print(f"Follow-up contains '10': {'10' in follow_up}")
            except Exception as e:
                print(f"Follow-up failed: {str(e)[:150]}")
                # If it fails, let's see what tool results are causing the issue
                print(f"Current tool handler results count: {len(bot.tool_handler.results)}")
                print(f"Current conversation tool results count: {len(bot.conversation.tool_results)}")
                # Check if there are orphaned tool results
                if bot.conversation.tool_results:
                    print("Conversation tool results found:")
                    for i, result in enumerate(bot.conversation.tool_results):
                        if isinstance(result, dict) and 'tool_use_id' in result:
                            print(f"  {i}: tool_use_id = {result['tool_use_id']}")
                return False
            return True
        finally:
            os.chdir(original_cwd)
if __name__ == "__main__":
    unittest.main()