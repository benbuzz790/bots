import ast
import inspect
from typing import List, Optional

from bots.dev.decorators import toolify
from bots.foundation.base import Bot


def _get_calling_bot() -> Optional[Bot]:
    """Get the Bot instance that called the current tool."""
    frame = inspect.currentframe()
    try:
        # Walk up the call stack to find the Bot instance
        while frame:
            frame = frame.f_back
            if frame and "self" in frame.f_locals:
                obj = frame.f_locals["self"]
                if isinstance(obj, Bot):
                    return obj
    finally:
        del frame
    return None


@toolify()
def get_own_info() -> str:
    """Get information about the bot's current state and configuration.

    Returns:
        str: Information about model, temperature, max_tokens, and available tools
    """
    bot = _get_calling_bot()
    if not bot:
        return "Error: Could not find calling bot"

    info = []
    if hasattr(bot, "name") and bot.name:
        info.append(f"Name: {bot.name}")
    info.append(f"Model: {bot.model_engine}")
    info.append(f"Temperature: {bot.temperature}")
    info.append(f"Max tokens: {bot.max_tokens}")

    if hasattr(bot, "tool_handler") and bot.tool_handler.tools:
        tool_names = [t.__name__ if hasattr(t, "__name__") else str(t) for t in bot.tool_handler.tools]
        info.append(f"Available tools: {', '.join(tool_names)}")
    else:
        info.append("No tools available")

    return "\n".join(info)


@toolify()
def _modify_own_settings(temperature: str = None, max_tokens: str = None) -> str:
    """Modify the bot's temperature or max_tokens settings.

    Parameters:
        temperature (str, optional): New temperature value (0.0-1.0)
        max_tokens (str, optional): New max_tokens value

    Returns:
        str: Confirmation message or error
    """
    bot = _get_calling_bot()
    if not bot:
        return "Error: Could not find calling bot"

    changes = []
    if temperature is not None:
        try:
            temp_val = float(temperature)
            if 0.0 <= temp_val <= 1.0:
                bot.temperature = temp_val
                changes.append(f"Temperature set to {temp_val}")
            else:
                return "Error: Temperature must be between 0.0 and 1.0"
        except ValueError:
            return f"Error: Invalid temperature value: {temperature}"

    if max_tokens is not None:
        try:
            tokens_val = int(max_tokens)
            if tokens_val > 0:
                bot.max_tokens = tokens_val
                changes.append(f"Max tokens set to {tokens_val}")
            else:
                return "Error: Max tokens must be positive"
        except ValueError:
            return f"Error: Invalid max_tokens value: {max_tokens}"

    if changes:
        return "\n".join(changes)
    else:
        return "No changes made"


@toolify()
def branch_self(
    self_prompts: str,
    allow_work: str = "False",
    parallel: str = "False",
    recombine: str = "concatenate",
) -> str:
    """Create multiple conversation branches to explore different approaches or tackle separate tasks.

    Creates isolated conversation branches using deepcopy:
    1. Deepcopy current bot state (uses __getstate__/__setstate__ for proper serialization)
    2. Execute each branch with independent bot instances
    3. Stitch results back into main conversation tree

    Note: Uses deepcopy with __getstate__/__setstate__ which leverages the hybrid
    serialization strategy (source code + dill for helpers). See bots/foundation/tool_handling.md.

    Args:
        self_prompts (str): List of prompts as a string array, like ['task 1', 'task 2', 'task 3']
                           Each prompt becomes a separate conversation branch
        allow_work (str): 'True' to let each branch use tools and continue working until done
                         'False' (default) for single-response branches
        parallel (str): 'True' to let branches work in parallel, 'False' for sequential (default).
        recombine (str): One of ('none', 'concatenate', 'llm_merge', 'llm_vote', 'llm_judge'),
                         default 'concatenate'. Combines the final messages from each branch.

    Returns:
        str: Success message with branch count, or error details if something went wrong
    """
    import copy
    import threading
    from concurrent.futures import ThreadPoolExecutor, as_completed

    from bots.flows import functional_prompts as fp

    bot = _get_calling_bot()
    if not bot:
        return "Error: Could not find calling bot"

    # Parse parameters
    allow_work = allow_work.lower() == "true"
    parallel = parallel.lower() == "true"
    recombine = recombine.lower()

    valid_recombine_options = ["none", "concatenate", "llm_judge", "llm_vote", "llm_merge"]
    if recombine not in valid_recombine_options:
        return f"Error: Invalid recombine option. Valid: {valid_recombine_options}"

    # Process the prompts
    try:
        message_list = _process_string_array(self_prompts)
        if not message_list:
            return "Error: No valid messages provided"
    except Exception as e:
        return f"Error parsing prompts: {str(e)}"

    # Add self-prompt prefix
    prefixed_prompts = [f"(self-prompt): {prompt}" for prompt in message_list]

    try:
        # Store original conversation point and bot settings
        original_node = bot.conversation
        original_autosave = bot.autosave
        bot.autosave = False

        # Handle tool_use without tool_result issue
        # If the current node has tool_calls (the branch_self call itself),
        # we need to add a USER message with tool_results before copying
        dummy_node_added = False
        dummy_node = None

        if original_node.tool_calls:
            # Check if this is the branch_self call
            for tool_call in original_node.tool_calls:
                if tool_call.get("name") == "branch_self":
                    # Create a dummy USER message with tool_result
                    dummy_result = bot.tool_handler.generate_response_schema(tool_call, "Branching in progress...")

                    # Add a user message node with the tool result
                    # Use a placeholder content since Anthropic requires non-empty text
                    dummy_node = original_node._add_reply(
                        role="user",
                        content="[Tool execution in progress]",
                        tool_results=[dummy_result],
                    )
                    dummy_node_added = True

                    # Update bot's conversation pointer to this new node
                    bot.conversation = dummy_node
                    break

        # Create lock for thread-safe mutations
        replies_lock = threading.Lock()

        def execute_branch(prompt, parent_bot_node):
            """Execute a single branch with the given prompt."""
            try:
                # Create a fresh bot copy using deepcopy
                # This uses __getstate__/__setstate__ which calls _serialize()/_deserialize()
                branch_bot = copy.deepcopy(bot)
                branch_bot.autosave = False
                # Callbacks are preserved by deepcopy

                # Store the branching point (branch_bot.conversation is at same point as bot.conversation)
                branching_node = branch_bot.conversation

                # Ensure clean tool handler state for branch
                if hasattr(branch_bot, "tool_handler") and branch_bot.tool_handler:
                    branch_bot.tool_handler.clear()

                if allow_work:
                    # Use iterative approach for work
                    response = branch_bot.respond(prompt)
                    while not fp.conditions.tool_not_used(branch_bot):
                        response = branch_bot.respond("ok")
                else:
                    # Single response
                    response = branch_bot.respond(prompt)

                # Stitch completed conversation back onto parent bot conversation
                # Thread-safe mutation with lock
                with replies_lock:
                    parent_bot_node.replies.extend(branching_node.replies)
                    for node in branching_node.replies:
                        node.parent = parent_bot_node

                return response, branch_bot.conversation

            except Exception:
                import traceback

                traceback.print_exc()
                return None, None

        # Execute branches
        responses = []
        branch_nodes = []

        if parallel:
            # Parallel execution
            with ThreadPoolExecutor() as executor:
                futures = {
                    executor.submit(execute_branch, prompt, bot.conversation): prompt for prompt in prefixed_prompts
                }  # noqa: E501
                for future in as_completed(futures):
                    response, node = future.result()
                    responses.append(response)
                    branch_nodes.append(node)
        else:
            # Sequential execution
            for prompt in prefixed_prompts:
                response, node = execute_branch(prompt, bot.conversation)
                responses.append(response)
                branch_nodes.append(node)

        # Remove dummy node if we added it
        if dummy_node_added and dummy_node:
            # Before removing dummy_node, preserve any branch replies that were attached to it
            # Iterate over dummy_node's replies and move them to original_node
            for child in list(dummy_node.replies):  # Use list() to avoid modification during iteration
                # Update parent reference to point to original_node
                child.parent = original_node
                # Add child to original_node's replies
                original_node.replies.append(child)

            # Clear dummy_node's replies to avoid dangling references
            dummy_node.replies.clear()

            # Now safe to remove the dummy node from the conversation tree
            original_node.replies.remove(dummy_node)
            # Restore bot's conversation pointer
            bot.conversation = original_node

        # Restore original bot settings
        bot.autosave = original_autosave

        # Count successful branches
        success_count = sum(1 for r in responses if r is not None)

        # Create success message, handle recombination if requested
        combined = "No recombinator selected"
        if recombine != "none" and responses:
            valid_responses = [r for r in responses if r is not None]

            if valid_responses:
                from bots.flows.recombinators import recombinators as recomb

                # Get the appropriate recombinator method
                if recombine == "concatenate":
                    combined, _ = recomb.concatenate(valid_responses, [])
                elif recombine == "llm_judge":
                    combined, _ = recomb.llm_judge(valid_responses, [], judge_bot=bot)
                elif recombine == "llm_vote":
                    combined, _ = recomb.llm_vote(valid_responses, [], vote_bot=bot)
                elif recombine == "llm_merge":
                    combined, _ = recomb.llm_merge(valid_responses, [], merge_bot=bot)
                else:
                    combined = "Unknown recombination method"

        exec_type = "parallel" if parallel else "sequential"
        work_type = "iterative" if allow_work else "single-response"
        result_content = (
            f"Successfully completed {success_count}/{len(message_list)} "
            f"{exec_type} {work_type} branches. "
            f"Recombination result:\n\n{combined}"
        )

        return result_content

    except Exception as e:
        import traceback

        traceback.print_exc()
        return f"Error in branch_self: {str(e)}"


@toolify()
def add_tools(filepath: str) -> str:
    """Add tools from a Python file to the bot's toolkit.

    Parameters:
        filepath (str): Path to Python file containing tool functions

    Returns:
        str: Success message with tool names, or error message
    """
    bot = _get_calling_bot()
    if not bot:
        return "Error: Could not find calling bot"

    try:
        import importlib.util
        import os

        if not os.path.exists(filepath):
            return f"Error: File not found: {filepath}"

        # Load the module
        spec = importlib.util.spec_from_file_location("custom_tools", filepath)
        if spec is None or spec.loader is None:
            return f"Error: Could not load module from {filepath}"

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Find all callable functions in the module
        tools = []
        for name in dir(module):
            obj = getattr(module, name)
            if callable(obj) and not name.startswith("_"):
                tools.append(obj)

        if not tools:
            return f"No tools found in {filepath}"

        # Add tools to bot
        bot.add_tools(*tools)

        tool_names = [t.__name__ for t in tools]
        return f"Added {len(tools)} tools: {', '.join(tool_names)}"

    except Exception as e:
        return f"Error loading tools: {str(e)}"


@toolify()
def list_context() -> str:
    """List all bot messages in the conversation with labels for removal.

    Use this before remove_context to see what messages are in your conversation.
    Shows bot messages only (since removal happens in user-bot pairs) with:
    - A label [A], [B], [C], etc. for reference
    - Truncated tool calls (if any) with parameters
    - Truncated response text

    Returns:
        str: Formatted list of bot messages with labels, or error message

    Example output:
        [A] Bot: <tool_name param="value..."> | "Response text..."
        [B] Bot: "Response text without tools..."
    """
    bot = _get_calling_bot()
    if not bot:
        return "Error: Could not find calling bot"

    try:
        # Walk back through conversation to root
        messages = []
        current = bot.conversation
        while current:
            if current.role == "assistant":
                messages.append(current)
            current = current.parent

        # Reverse to get chronological order
        messages.reverse()

        if not messages:
            return "No bot messages in conversation history"

        # Format with labels
        lines = []
        for i, msg in enumerate(messages):
            # Generate label: A-Z, then AA-AZ, BA-BZ, etc. (Excel-style column naming)
            if i < 26:
                label = chr(65 + i)  # A, B, C, ..., Z
            else:
                # After Z, use AA, AB, AC, ..., AZ, BA, BB, etc.
                # Subtract 26 to start the two-letter sequence from 0
                adjusted_i = i - 26
                first_letter = chr(65 + (adjusted_i // 26))  # A, B, C, ...
                second_letter = chr(65 + (adjusted_i % 26))  # A-Z cycling
                label = first_letter + second_letter

            # Format tool calls if present
            tool_str = ""
            if msg.tool_calls:
                tool_parts = []
                for tc in msg.tool_calls[:2]:  # Show first 2 tool calls
                    name = tc.get("name", "unknown")
                    # Truncate parameters
                    params_str = str(tc.get("input", {}))[:50]
                    if len(str(tc.get("input", {}))) > 50:
                        params_str += "..."
                    tool_parts.append(f"<{name} {params_str}>")
                if len(msg.tool_calls) > 2:
                    tool_parts.append(f"... +{len(msg.tool_calls) - 2} more")
                tool_str = " ".join(tool_parts) + " | "

            # Truncate content
            content = msg.content or ""
            if len(content) > 100:
                content = content[:100] + "..."

            lines.append(f'[{label}] Bot: {tool_str}"{content}"')

        return "\n".join(lines)

    except Exception as e:
        return f"Error listing context: {str(e)}"


@toolify()
def remove_context(labels: str) -> str:
    """Remove bot-user message pairs from the conversation history.

    Use when you need to delete specific messages from your conversation tree
    to reduce context or remove irrelevant information. This is a demo tool
    that removes message pairs by stitching the tree after deletion.

    Note: This tool has limitations with branched conversations and will
    attempt to handle the simplest case (linear conversation paths).

    Tool call sequences are automatically removed as complete units. If you
    remove any message in a tool call sequence (question -> tool call ->
    result -> answer), the entire sequence is removed to maintain integrity.

    Parameters:
        labels (str): String representation of a list of labels to remove.
            Format: "['A', 'B', 'C']"
            Use list_context() first to see available labels.

    Returns:
        str: Success message with count of removed pairs, or error message

    Example:
        remove_context("['A', 'C']")
    """
    bot = _get_calling_bot()
    if not bot:
        return "Error: Could not find calling bot"

    try:
        # Parse labels
        label_list = _process_string_array(labels)
        if not label_list:
            return "Error: No valid labels provided"

        # Get all bot messages
        messages = []
        current = bot.conversation
        while current:
            if current.role == "assistant":
                messages.append(current)
            current = current.parent
        messages.reverse()

        # Map labels to indices
        indices_to_remove = []
        for label in label_list:
            label = label.upper()

            if len(label) == 1 and label.isalpha():
                # Single letter: A-Z (indices 0-25)
                idx = ord(label) - 65
            elif len(label) == 2 and label[0].isalpha() and label[1].isalpha():
                # Two letters: AA, AB, ..., AZ, BA, BB, etc.
                first_letter_idx = ord(label[0]) - 65
                second_letter_idx = ord(label[1]) - 65
                idx = 26 + (first_letter_idx * 26) + second_letter_idx
            else:
                return f"Error: Invalid label format: {label}"

            if 0 <= idx < len(messages):
                indices_to_remove.append(idx)
            else:
                return f"Error: Label {label} out of range (only {len(messages)} messages)"

        # Expand indices to include complete tool call sequences
        expanded_indices = set()
        sequence_info = []

        for idx in indices_to_remove:
            msg_node = messages[idx]
            user_node = msg_node.parent

            if not user_node or user_node.role != "user":
                continue

            grandparent = user_node.parent
            if not grandparent:
                continue

            # Check if this is part of a tool call sequence
            # Sequence: assistant_with_tool -> user_with_results -> assistant_answer

            # Case 1: msg_node has tool_calls (it's the initiator)
            if msg_node.tool_calls:
                # Find the next assistant message (the one after tool results)
                for child in msg_node.replies:
                    if child.role == "user" and child.tool_results:
                        for grandchild in child.replies:
                            if grandchild.role == "assistant":
                                # Find index of this grandchild
                                try:
                                    next_idx = messages.index(grandchild)
                                    expanded_indices.add(idx)
                                    expanded_indices.add(next_idx)
                                    # Use inline label generation to avoid long lines
                                    if idx < 26:
                                        label1 = chr(65 + idx)
                                    else:
                                        label1 = chr(65 + ((idx - 26) // 26)) + chr(65 + ((idx - 26) % 26))
                                    if next_idx < 26:
                                        label2 = chr(65 + next_idx)
                                    else:
                                        label2 = chr(65 + ((next_idx - 26) // 26)) + chr(65 + ((next_idx - 26) % 26))
                                    info = f"Tool call sequence: labels {label1} and {label2}"
                                    sequence_info.append(info)
                                except ValueError:
                                    pass
                        break

            # Case 2: msg_node follows tool results (it's the answer after tool use)
            elif grandparent.role == "assistant" and grandparent.tool_calls and user_node.tool_results:
                # Find index of grandparent (the initiator)
                try:
                    prev_idx = messages.index(grandparent)
                    expanded_indices.add(prev_idx)
                    expanded_indices.add(idx)
                    # Use inline label generation
                    if prev_idx < 26:
                        label1 = chr(65 + prev_idx)
                    else:
                        label1 = chr(65 + ((prev_idx - 26) // 26)) + chr(65 + ((prev_idx - 26) % 26))
                    if idx < 26:
                        label2 = chr(65 + idx)
                    else:
                        label2 = chr(65 + ((idx - 26) // 26)) + chr(65 + ((idx - 26) % 26))
                    sequence_info.append(f"Tool call sequence: labels {label1} and {label2}")
                except ValueError:
                    pass

            # Case 3: Normal message (not part of tool sequence)
            else:
                expanded_indices.add(idx)

        # Remove messages (in reverse order to maintain indices)
        indices_to_remove = sorted(expanded_indices, reverse=True)
        removed_count = 0

        for idx in indices_to_remove:
            msg_node = messages[idx]
            user_node = msg_node.parent

            if not user_node or user_node.role != "user":
                continue

            grandparent = user_node.parent
            if not grandparent:
                continue

            # Remove user_node from grandparent's replies
            if user_node in grandparent.replies:
                grandparent.replies.remove(user_node)

            # If bot message has children, reconnect them to grandparent
            for child in msg_node.replies:
                child.parent = grandparent
                grandparent.replies.append(child)

            removed_count += 1

            # Update bot.conversation if we removed the current node
            if bot.conversation == msg_node or bot.conversation == user_node:
                bot.conversation = grandparent

        # Build result message
        result_parts = [f"Removed {removed_count} message pair(s)"]
        if sequence_info:
            result_parts.append("\nTool call sequences removed as complete units:")
            for info in set(sequence_info):  # Use set to deduplicate
                result_parts.append(f"  - {info}")

        return "\n".join(result_parts)

    except Exception as e:
        import traceback

        traceback.print_exc()
        return f"Error removing context: {str(e)}"


def _process_string_array(input_str: str) -> List[str]:
    """Parse a string representation of an array into a list.

    Handles formats like:
    - "['item1', 'item2']"
    - '["item1", "item2"]'
    - "item1, item2"

    Parameters:
        input_str (str): String to parse

    Returns:
        List[str]: Parsed list of strings
    """
    try:
        # Try JSON parsing first
        import json

        result = json.loads(input_str)
        if isinstance(result, list):
            return [str(item) for item in result]
    except (json.JSONDecodeError, ValueError):
        pass

    try:
        # Try ast.literal_eval
        result = ast.literal_eval(input_str)
        if isinstance(result, (list, tuple)):
            return [str(item) for item in result]
    except (ValueError, SyntaxError):
        pass

    # Fall back to comma-separated
    if "," in input_str:
        return [item.strip().strip("'\"") for item in input_str.split(",")]

    # Single item
    return [input_str.strip().strip("'\"")]


def _verbose_callback(responses, nodes):
    """Callback for verbose branch_self output."""
    print("\n=== Branch completed ===")
    print(f"Response: {responses[-1][:200]}..." if len(responses[-1]) > 200 else f"Response: {responses[-1]}")
    print(f"Node: {nodes[-1]}")


def _remove_dummy_from_tree(node, dummy_content):
    """Remove dummy nodes from conversation tree.

    Parameters:
        node: Current node to check
        dummy_content: Content string to identify dummy nodes
    """
    if not node:
        return

    # Check children
    for child in list(node.replies):  # Use list() to avoid modification during iteration
        if child.content == dummy_content:
            # Remove this child and promote its children
            node.replies.remove(child)
            for grandchild in child.replies:
                grandchild.parent = node
                node.replies.append(grandchild)
        else:
            # Recursively check this child
            _remove_dummy_from_tree(child, dummy_content)


@toolify()
def subagent(tasks: str, max_iterations: str = "20") -> str:
    """Create a subagent that works on a list of tasks iteratively.

    The subagent will work through the tasks one by one, using tools as needed.
    Unlike branch_self, this creates a single linear conversation path.

    Parameters:
        tasks (str): List of tasks as a string array, like ['task 1', 'task 2']
        max_iterations (str): Maximum number of iterations (default: "20")

    Returns:
        str: Summary of completed tasks and final response
    """
    bot = _get_calling_bot()
    if not bot:
        return "Error: Could not find calling bot"

    try:
        task_list = _process_string_array(tasks)
        if not task_list:
            return "Error: No valid tasks provided"

        max_iter = int(max_iterations)
    except Exception as e:
        return f"Error parsing parameters: {str(e)}"

    try:
        import copy

        from bots.flows import functional_prompts as fp

        # Create a copy of the bot for the subagent
        subagent_bot = copy.deepcopy(bot)
        subagent_bot.autosave = False

        responses = []
        for i, task in enumerate(task_list, 1):
            # Execute task
            response = subagent_bot.respond(f"Task {i}/{len(task_list)}: {task}")
            responses.append(response)

            # Allow tool use
            iterations = 0
            while not fp.conditions.tool_not_used(subagent_bot) and iterations < max_iter:
                response = subagent_bot.respond("ok")
                responses.append(response)
                iterations += 1

        # Stitch subagent conversation back to main bot
        bot.conversation.replies.extend(subagent_bot.conversation.replies)
        for node in subagent_bot.conversation.replies:
            node.parent = bot.conversation

        return f"Completed {len(task_list)} tasks. Final response:\n\n{responses[-1]}"

    except Exception as e:
        import traceback

        traceback.print_exc()
        return f"Error in subagent: {str(e)}"
