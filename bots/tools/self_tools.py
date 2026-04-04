import ast
from typing import List, Optional

from bots.dev.decorators import toolify
from bots.foundation.base import Bot


@toolify()
def _get_own_info(_bot: Optional[Bot] = None) -> str:
    """Get information about the bot's current state and configuration.

    Returns:
        str: Information about model, temperature, max_tokens, and available tools
    """
    if _bot is None:
        return "Error: Bot reference not provided"
    bot = _bot

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
def _modify_own_settings(temperature: str = None, max_tokens: str = None, _bot: Optional[Bot] = None) -> str:
    """Modify the bot's temperature or max_tokens settings.

    Parameters:
        temperature (str, optional): New temperature value (0.0-1.0)
        max_tokens (str, optional): New max_tokens value

    Returns:
        str: Confirmation message or error
    """
    if _bot is None:
        return "Error: Bot reference not provided"
    bot = _bot

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
    _bot: Optional[Bot] = None,
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
    import warnings
    from concurrent.futures import ThreadPoolExecutor, as_completed

    from bots.flows import functional_prompts as fp

    if _bot is None:
        return "Error: Bot reference not provided"
    bot = _bot

    # Track recursion depth to prevent infinite recursion
    if not hasattr(bot, "_branch_self_depth"):
        bot._branch_self_depth = 0

    bot._branch_self_depth += 1
    current_depth = bot._branch_self_depth

    # Warn at depth 5 and 10
    if current_depth == 5:
        warning_msg = (
            f"WARNING: branch_self recursion depth is {current_depth}. "
            "This may indicate unintended recursive branching. "
            "Consider reviewing your branching strategy."
        )
        warnings.warn(warning_msg, RuntimeWarning, stacklevel=2)
        print(f"\n⚠️  {warning_msg}\n")
    elif current_depth == 10:
        warning_msg = (
            f"WARNING: branch_self recursion depth is {current_depth}. "
            "Deep recursion detected! This is likely unintended and may cause issues. "
            "Please review your code for infinite recursion patterns."
        )
        warnings.warn(warning_msg, RuntimeWarning, stacklevel=2)
        print(f"\n⚠️⚠️  {warning_msg}\n")

    try:
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
                return "Error: No valid prompts provided"

            # Store original settings
            original_node = bot.conversation
            original_autosave = bot.autosave
            bot.autosave = False

            # Handle tool_use without tool_result issue for parallel tool calls
            # If the current node has tool_calls, we need to add a USER message with
            # tool_results for ALL tool calls before copying (not just branch_self)
            dummy_node_added = False
            dummy_node = None
            if original_node.tool_calls:
                # Check if branch_self is among the tool calls (parallel or not)
                has_branch_self = any(tc.get("name") == "branch_self" for tc in original_node.tool_calls)

                if has_branch_self:
                    # Create dummy tool_results for ALL tool calls in this message
                    # This is required for parallel tool calling compatibility
                    dummy_results = []
                    for tool_call in original_node.tool_calls:
                        if tool_call.get("name") == "branch_self":
                            # branch_self gets a proper "in progress" message
                            dummy_result = bot.tool_handler.generate_response_schema(tool_call, "Branching in progress...")
                        else:
                            # Other parallel tool calls get placeholder results
                            # This ensures Anthropic's requirement that all tool results
                            # must be in a single user message
                            dummy_result = bot.tool_handler.generate_response_schema(
                                tool_call, "[Parallel tool execution - result pending]"
                            )
                        dummy_results.append(dummy_result)

                    # Add a user message node with ALL tool results
                    # Use a placeholder content since Anthropic requires non-empty text
                    dummy_node = original_node._add_reply(
                        role="user",
                        content="[Tool execution in progress]",
                        tool_results=dummy_results,
                    )
                    dummy_node_added = True

                    # Update bot's conversation pointer to this new node
                    bot.conversation = dummy_node

            # Create lock for thread-safe mutations
            replies_lock = threading.Lock()

            # Determine which node to use as parent for branches
            parent_bot_node = bot.conversation

            # Prepare prompts (no prefixing needed - allow_work is handled in execute_branch)
            prefixed_prompts = message_list

            def execute_branch(prompt):
                """Execute a single branch and return the response and node."""
                try:
                    # Create a deep copy of the bot for this branch
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
                    futures = {executor.submit(execute_branch, prompt): prompt for prompt in prefixed_prompts}
                    for future in as_completed(futures):
                        response, node = future.result()
                        responses.append(response)
                        branch_nodes.append(node)
            else:
                # Sequential execution
                for prompt in prefixed_prompts:
                    response, node = execute_branch(prompt)
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

    finally:
        # Decrement depth counter when exiting
        bot._branch_self_depth -= 1


@toolify()
def add_tools(filepath: str, _bot: Optional[Bot] = None) -> str:
    """Add tools from a Python file to the bot's toolkit.

    Parameters:
        filepath (str): Path to Python file containing tool functions

    Returns:
        str: Success message with tool names, or error message
    """
    if _bot is None:
        return "Error: Bot reference not provided"
    bot = _bot

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
def remove_context(prompt: str, _bot: Optional[Bot] = None) -> str:
    """Remove bot-user message pairs from the conversation history based on a condition.

    Use when you need to delete specific messages from your conversation tree
    to reduce context or remove irrelevant information. Uses Haiku to evaluate
    which message pairs match your condition.

    Parameters:
        prompt (str): Natural language condition describing which messages to remove.
            Examples:
            - "remove all messages about file operations"
            - "delete conversations where I was debugging tests"
            - "remove tool calls that failed"
            - "delete messages older than the last save operation"

    Returns:
        str: Success message with count of removed pairs, or error message

    Example:
        remove_context("remove all messages about testing")
    """
    if _bot is None:
        return "Error: Bot reference not provided"
    bot = _bot

    try:
        from bots.foundation.anthropic_bots import AnthropicBot
        from bots.foundation.base import Engines

        # Create a Haiku instance for evaluation
        haiku = AnthropicBot(
            api_key=bot.api_key,
            model_engine=Engines.CLAUDE45_HAIKU,
            max_tokens=4000,
            temperature=0.0,
            autosave=False,
            enable_tracing=False,
        )

        # Get all bot messages
        messages = []
        current = bot.conversation
        while current:
            if current.role == "assistant":
                messages.append(current)
            current = current.parent
        messages.reverse()

        if not messages:
            return "No bot messages in conversation history"

        # Helper function to truncate lines from the middle
        def truncate_lines(text: str, max_lines: int = 20) -> str:
            """Truncate text to max_lines, removing from the middle if needed."""
            if not text:
                return ""

            lines = text.split("\n")
            if len(lines) <= max_lines:
                return text

            # Keep first 10 and last 10 lines
            first_half = max_lines // 2
            second_half = max_lines - first_half
            removed_count = len(lines) - max_lines

            result = "\n".join(lines[:first_half])
            result += f"\n... ({removed_count} lines removed) ...\n"
            result += "\n".join(lines[-second_half:])
            return result

        # Build numbered list of messages
        conversation_list = []
        for i, msg in enumerate(messages):
            msg_parts = []

            # Get parent user message if it exists
            user_content = ""
            if msg.parent and msg.parent.role == "user":
                user_content = msg.parent.content or ""

            # Add user message (not truncated)
            if user_content:
                msg_parts.append(f"User: {user_content}")

            # Add assistant text content (not truncated)
            if msg.content:
                msg_parts.append(f"Assistant: {msg.content}")

            # Add tool calls (truncated if needed)
            if msg.tool_calls:
                tool_calls_str = "Tool Calls:\n"
                for tc in msg.tool_calls:
                    tool_name = tc.get("name", "unknown")
                    tool_input = tc.get("input", {})
                    tool_calls_str += f"  - {tool_name}({tool_input})\n"
                msg_parts.append(truncate_lines(tool_calls_str, max_lines=20))

            # Add tool results (truncated if needed)
            if msg.parent and msg.parent.role == "user" and msg.parent.tool_results:
                tool_results_str = "Tool Results:\n"
                for tr in msg.parent.tool_results:
                    tool_name = tr.get("tool_name")
                    # If tool_name is not present, try to resolve from tool_use_id
                    if not tool_name:
                        tool_use_id = tr.get("tool_use_id")
                        if tool_use_id and msg.parent.parent and msg.parent.parent.tool_calls:
                            # Look up the tool name from the corresponding tool call
                            for tc in msg.parent.parent.tool_calls:
                                if tc.get("id") == tool_use_id:
                                    tool_name = tc.get("name", "unknown")
                                    break
                        if not tool_name:
                            tool_name = "unknown"
                    content = tr.get("content", "")
                    tool_results_str += f"  - {tool_name}: {content}\n"
                msg_parts.append(truncate_lines(tool_results_str, max_lines=20))

            conversation_list.append(f"[{i}] {' | '.join(msg_parts)}")

        # Create the evaluation prompt with the full conversation
        conversation_text = "\n\n".join(conversation_list)

        eval_prompt = f"""You are evaluating a conversation history to identify which message pairs should be removed based on a condition.

Condition: "{prompt}"

Conversation history (numbered):
{conversation_text}

Based on the condition, which message indices should be removed? Consider the full context of the conversation.

Respond with a JSON array of integers representing the indices to remove. For example: [0, 3, 5]
If no messages match the condition, respond with an empty array: []

Your response (JSON array only):"""

        eval_response = haiku.respond(eval_prompt).strip()

        # Parse the response to extract indices
        import json

        try:
            # Try to extract JSON array from response
            if "[" in eval_response and "]" in eval_response:
                start = eval_response.index("[")
                end = eval_response.rindex("]") + 1
                json_str = eval_response[start:end]
                indices_to_remove = json.loads(json_str)
            else:
                indices_to_remove = []
        except (json.JSONDecodeError, ValueError) as e:
            return f"Error parsing Haiku response: {eval_response}\nError: {str(e)}"

        if not indices_to_remove:
            return f"No messages matched the condition: '{prompt}'"

        # Validate indices
        indices_to_remove = [idx for idx in indices_to_remove if 0 <= idx < len(messages)]

        if not indices_to_remove:
            return "No valid message indices to remove"

        # Expand indices to include complete tool call sequences
        expanded_indices = set()
        sequence_info = []

        for idx in indices_to_remove:
            msg_node = messages[idx]

            # Check if this is part of a tool call sequence
            # Case 1: msg_node has tool_calls (it's the initiator)
            if msg_node.tool_calls:
                # Find the next assistant message (the one after tool results)
                for child in msg_node.replies:
                    if child.role == "user" and child.tool_results:
                        for grandchild in child.replies:
                            if grandchild.role == "assistant":
                                try:
                                    next_idx = messages.index(grandchild)
                                    expanded_indices.add(idx)
                                    expanded_indices.add(next_idx)
                                    sequence_info.append(f"Tool call sequence: indices {idx} and {next_idx}")
                                except ValueError:
                                    pass
                        break

            # Case 2: msg_node follows tool results (it's the answer after tool use)
            elif msg_node.parent and msg_node.parent.role == "user" and msg_node.parent.tool_results:
                # This assistant message is responding to tool results
                # Find the assistant that made the tool call
                parent_user = msg_node.parent
                if parent_user.parent and parent_user.parent.role == "assistant" and parent_user.parent.tool_calls:
                    try:
                        prev_idx = messages.index(parent_user.parent)
                        expanded_indices.add(prev_idx)
                        expanded_indices.add(idx)
                        sequence_info.append(f"Tool call sequence: indices {prev_idx} and {idx}")
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

            # Find the child user message (the one that comes AFTER the assistant)
            child_user_node = None
            for reply in msg_node.replies:
                if reply.role == "user":
                    child_user_node = reply
                    break

            # Get the parent (what comes before the assistant)
            parent_node = msg_node.parent

            if not parent_node:
                # Can't remove if there's no parent to reconnect to
                continue

            # Determine what to reconnect to the parent
            if child_user_node:
                # We have a child user message to remove along with the assistant
                # Get the children of the child_user_node (what comes after)
                grandchildren = list(child_user_node.replies)

                # Remove the assistant and its child user from the tree
                # Reconnect grandchildren to parent
                for grandchild in grandchildren:
                    grandchild.parent = parent_node
                    if grandchild not in parent_node.replies:
                        parent_node.replies.append(grandchild)

                # Remove msg_node from parent's replies
                if msg_node in parent_node.replies:
                    parent_node.replies.remove(msg_node)

                # Clear references to avoid memory leaks
                msg_node.replies.clear()
                child_user_node.replies.clear()

                # Update bot.conversation if we removed the current node
                if bot.conversation == msg_node or bot.conversation == child_user_node:
                    # Point to the first grandchild if available, otherwise parent
                    if grandchildren:
                        bot.conversation = grandchildren[-1]  # Last grandchild (most recent)
                    else:
                        bot.conversation = parent_node

                removed_count += 1
            else:
                # No child user message - just remove the assistant message
                # This shouldn't happen in normal conversation flow, but handle it
                # Reconnect any children of msg_node to parent
                for child in list(msg_node.replies):
                    child.parent = parent_node
                    if child not in parent_node.replies:
                        parent_node.replies.append(child)

                # Remove msg_node from parent's replies
                if msg_node in parent_node.replies:
                    parent_node.replies.remove(msg_node)

                msg_node.replies.clear()

                # Update bot.conversation if we removed the current node
                if bot.conversation == msg_node:
                    bot.conversation = parent_node

                removed_count += 1

        # Build result message
        result_parts = [f"Removed {removed_count} message pair(s) matching condition: '{prompt}'"]
        if sequence_info:
            result_parts.append("\nTool call sequences removed as complete units:")
            for info in set(sequence_info):
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
def subagent(tasks: str, max_iterations: str = "20", _bot: Optional[Bot] = None) -> str:
    """Create a subagent that works on a list of tasks iteratively.

    The subagent will work through the tasks one by one, using tools as needed.
    Unlike branch_self, this creates a single linear conversation path.

    Parameters:
        tasks (str): List of tasks as a string array, like ['task 1', 'task 2']
        max_iterations (str): Maximum number of iterations (default: "20")

    Returns:
        str: Summary of completed tasks and final response
    """
    if _bot is None:
        return "Error: Bot reference not provided"
    bot = _bot

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
