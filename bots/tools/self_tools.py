import ast
import inspect
import json
import uuid
from typing import List, Optional

from bots.dev.decorators import toolify
from bots.foundation.base import Bot


def _get_calling_bot() -> Optional[Bot]:
    """Helper function to get a reference to the calling bot.
    Returns:
        Optional[Bot]: Reference to the calling bot or None if not found
    """
    frame = inspect.currentframe()
    while frame:
        if frame.f_code.co_name == "_cvsn_respond" and "self" in frame.f_locals:
            potential_bot = frame.f_locals["self"]
            if isinstance(potential_bot, Bot):
                return potential_bot
        frame = frame.f_back
    return None


@toolify()
def get_own_info() -> str:
    """Get information about yourself.
    Use when you need to inspect your current configuration (not tools).
    Returns:
        str: JSON string containing bot information including:
        - name: Your name
        - role: Your role
        - role_description: Your role description
        - model_engine: Current model engine
        - temperature: Current temperature setting
        - max_tokens: Maximum tokens setting
        - tool_count: Number of available tools
    """
    bot = _get_calling_bot()
    if not bot:
        return "Error: Could not find calling bot"
    info = {
        "name": bot.name,
        "role": bot.role,
        "role_description": bot.role_description,
        "model_engine": bot.model_engine.value,
        "temperature": bot.temperature,
        "max_tokens": bot.max_tokens,
        "tool_count": len(bot.tool_handler.tools) if bot.tool_handler else 0,
    }
    return json.dumps(info)


@toolify()
def _modify_own_settings(temperature: str = None, max_tokens: str = None) -> str:
    """Modify your settings.
    Use when you need to adjust your configuration parameters.
    Parameters:
        temperature (str, optional): New temperature value as string
            (0.0 to 1.0)
        max_tokens (str, optional): New maximum tokens value as string
            (must be > 0)
    Returns:
        str: Description of changes made or error message
    """
    import inspect

    from bots.foundation.base import Bot

    def _get_calling_bot_local():
        frame = inspect.currentframe()
        while frame:
            if frame.f_code.co_name == "_cvsn_respond" and "self" in frame.f_locals:
                potential_bot = frame.f_locals["self"]
                if isinstance(potential_bot, Bot):
                    return potential_bot
            frame = frame.f_back
        return None

    bot = _get_calling_bot_local()
    if not bot:
        return "Error: Could not find calling bot"
    if temperature is not None:
        temp_float = float(temperature)
        if not 0.0 <= temp_float <= 1.0:
            return "Error: Temperature must be between 0.0 and 1.0"
        bot.temperature = temp_float
    if max_tokens is not None:
        tokens_int = int(max_tokens)
        if tokens_int <= 0:
            return "Error: Max tokens must be a positive integer"
        bot.max_tokens = tokens_int
    return f"Settings updated successfully. Current settings: temperature={bot.temperature}, max_tokens={bot.max_tokens}"


@toolify()
def branch_self(self_prompts: str, allow_work: str = "False", parallel: str = "False", recombine: str = "concatenate") -> str:
    """Create multiple conversation branches to explore different approaches or tackle separate tasks.

    Simplified approach that creates isolated conversation branches:
    1. Save current bot state to temporary file
    2. Execute each branch with independent bot instances
    3. Stitch results back into main conversation tree
    Args:
        self_prompts (str): List of prompts as a string array, like ['task 1', 'task 2', 'task 3']
                           Each prompt becomes a separate conversation branch
        allow_work (str): 'True' to let each branch use tools and continue working until done
                         'False' (default) for single-response branches
        parallel (str): 'True' to let branches work in parallel, 'False' for sequential (default).
        recombine (str): One of ('none', 'concatenate', 'llm_merge', 'llm_vote', 'llm_judge'), default 'concatenate'.
                         Combines the final messages from each branch using that method.

    Returns:
        str: Success message with branch count, or error details if something went wrong
    """
    import os
    from concurrent.futures import ThreadPoolExecutor, as_completed

    from bots.flows import functional_prompts as fp
    from bots.foundation.base import Bot

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

        # Tag the current node so we can find it after load
        # This prevents recursive branching issues
        branch_tag = f"_branch_self_anchor_{uuid.uuid4().hex[:8]}"
        setattr(original_node, branch_tag, True)

        # Create a modified conversation node with dummy tool results
        # This prevents 'tool_use without tool_result' errors in branches
        if original_node.tool_calls:
            dummy_results = []
            for tool_call in original_node.tool_calls:
                if tool_call.get("name") == "branch_self":
                    # Use bot's tool_handler to generate provider-appropriate format
                    dummy_result = bot.tool_handler.generate_response_schema(
                        tool_call,
                        "Branching in progress..."
                    )
                    dummy_results.append(dummy_result)

            if dummy_results:
                # Temporarily add dummy results for saving
                original_results = getattr(original_node, "tool_results", [])
                original_node._add_tool_results(dummy_results)

                # Save bot state with dummy results and tag
                temp_id = str(uuid.uuid4())[:8]
                worker_id = os.environ.get("PYTEST_XDIST_WORKER", "main")
                temp_file = f"branch_self_{temp_id}_{worker_id}.bot"
                bot.save(temp_file)

                # Restore original results (remove dummy results from current bot)
                original_node.tool_results = original_results
            else:
                # No dummy results needed, save normally
                temp_id = str(uuid.uuid4())[:8]
                worker_id = os.environ.get("PYTEST_XDIST_WORKER", "main")
                temp_file = f"branch_self_{temp_id}_{worker_id}.bot"
                bot.save(temp_file)
        else:
            # No tool calls, save normally
            temp_id = str(uuid.uuid4())[:8]
            worker_id = os.environ.get("PYTEST_XDIST_WORKER", "main")
            temp_file = f"branch_self_{temp_id}_{worker_id}.bot"
            bot.save(temp_file)

        def execute_branch(prompt, parent_bot_node):
            """Execute a single branch with the given prompt."""
            try:
                # Create a fresh bot copy for this branch
                branch_bot = Bot.load(temp_file)
                branch_bot.autosave = False
                # Preserve callbacks from parent bot
                branch_bot.callbacks = bot.callbacks

                # Find the tagged node in the loaded bot's conversation tree
                # This ensures we branch from the correct point, not the newest node
                def find_tagged_node(node):
                    """Recursively search for the node with the branch tag."""
                    # Check current node for any branch_self_anchor tags
                    for attr in dir(node):
                        if attr.startswith("_branch_self_anchor_"):
                            return node
                    # Search in parent chain
                    current = node
                    while current.parent:
                        current = current.parent
                        for attr in dir(current):
                            if attr.startswith("_branch_self_anchor_"):
                                return current
                    # Search in all descendants from root
                    root = node
                    while root.parent:
                        root = root.parent

                    def search_tree(n):
                        for attr in dir(n):
                            if attr.startswith("_branch_self_anchor_"):
                                return n
                        for reply in n.replies:
                            result = search_tree(reply)
                            if result:
                                return result
                        return None

                    return search_tree(root)

                tagged_node = find_tagged_node(branch_bot.conversation)
                if tagged_node:
                    # Position at the tagged node
                    branch_bot.conversation = tagged_node
                    # Remove the tag from this branch's copy
                    for attr in dir(tagged_node):
                        if attr.startswith("_branch_self_anchor_"):
                            delattr(tagged_node, attr)
                            break

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

                # Stitch completed conversation back onto bot conversation
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
                futures = [executor.submit(execute_branch, prompt, original_node) for prompt in prefixed_prompts]
                for future in as_completed(futures):
                    response, node = future.result()
                    responses.append(response)
                    branch_nodes.append(node)
        else:
            # Sequential execution
            for prompt in prefixed_prompts:
                response, node = execute_branch(prompt, original_node)
                responses.append(response)
                branch_nodes.append(node)

        # Remove the tag from the original node
        if hasattr(original_node, branch_tag):
            delattr(original_node, branch_tag)

        # Restore original bot settings
        bot.autosave = original_autosave

        # Clean up temp file
        try:
            os.remove(temp_file)
        except OSError:
            pass

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
            f"Successfully completed {success_count}/{len(message_list)} {exec_type} {work_type} branches. "
            f"Recombination result:\n\n{combined}"
        )

        return result_content

    except Exception as e:
        import traceback

        traceback.print_exc()
        return f"Error in branch_self: {str(e)}"


@toolify()
def add_tools(filepath: str) -> str:
    """Adds a new set of tools (python functions) to your toolkit
    All top-level, non-private functions in filepath will be uploaded
    to your toolkit. Use when you need to create a new tool or kit for
    yourself to use in the future. Tool format is strict: string in,
    string out, with error catching wrapping (typically) all code in
    the function.
    Parameters:
        filepath: location of python tool file
    Returns:
        str: success or error message
    """
    bot = _get_calling_bot()
    bot.add_tools(filepath)


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

    # Collect all bot nodes from root
    root = bot.conversation._find_root()
    bot_nodes = []

    def collect_bot_nodes(node):
        """Recursively collect all bot (assistant) nodes in order."""
        if hasattr(node, "role") and node.role == "assistant":
            bot_nodes.append(node)
        for reply in node.replies:
            collect_bot_nodes(reply)

    collect_bot_nodes(root)

    if not bot_nodes:
        return "No bot messages found in conversation"

    # Generate labels A, B, C, ... Z, AA, AB, etc.
    def generate_label(index):
        """Generate Excel-style column labels: A, B, ..., Z, AA, AB, ..."""
        label = ""
        index += 1  # Make it 1-indexed for the algorithm
        while index > 0:
            index -= 1
            label = chr(65 + (index % 26)) + label
            index //= 26
        return label

    # Build the output
    lines = []
    for i, node in enumerate(bot_nodes):
        label = generate_label(i)
        parts = []

        # Add tool calls if present
        if hasattr(node, "tool_calls") and node.tool_calls:
            tool_strs = []
            for tool_call in node.tool_calls:
                tool_name = tool_call.get("name", "unknown")
                tool_input = tool_call.get("input", {})

                # Truncate tool parameters
                if isinstance(tool_input, dict):
                    param_parts = []
                    for key, value in tool_input.items():
                        value_str = str(value)
                        if len(value_str) > 20:
                            value_str = value_str[:20] + "..."
                        param_parts.append(f"{key}={value_str}")
                    params_str = ", ".join(param_parts)
                else:
                    params_str = str(tool_input)
                    if len(params_str) > 20:
                        params_str = params_str[:20] + "..."

                tool_strs.append(f"<{tool_name} {params_str}>")

            parts.append(" ".join(tool_strs))

        # Add response content
        if hasattr(node, "content") and node.content:
            content = node.content.replace("\n", " ")
            if len(content) > 50:
                content = content[:50] + "..."
            parts.append(f'"{content}"')

        # Combine parts
        if parts:
            message_str = " | ".join(parts)
        else:
            message_str = "<empty message>"

        lines.append(f"[{label}] Bot: {message_str}")

    return "\n".join(lines)


@toolify()
def remove_context(labels: str) -> str:
    """Remove bot-user message pairs from the conversation history.

    Use when you need to delete specific messages from your conversation tree
    to reduce context or remove irrelevant information. This is a demo tool
    that removes message pairs by stitching the tree after deletion.

    Note: This tool has limitations with branched conversations and will
    attempt to handle the simplest case (linear conversation paths).

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

    # Parse the labels
    try:
        label_list = _process_string_array(labels)
        if not label_list:
            return "Error: No valid labels provided"
    except Exception as e:
        return f"Error parsing labels: {str(e)}"

    # Collect all bot nodes from root
    root = bot.conversation._find_root()
    bot_nodes = []

    def collect_bot_nodes(node):
        """Recursively collect all bot (assistant) nodes in order."""
        if hasattr(node, "role") and node.role == "assistant":
            bot_nodes.append(node)
        for reply in node.replies:
            collect_bot_nodes(reply)

    collect_bot_nodes(root)

    if not bot_nodes:
        return "Error: No bot messages found in conversation"

    # Generate labels and create mapping
    def generate_label(index):
        """Generate Excel-style column labels: A, B, ..., Z, AA, AB, ..."""
        label = ""
        index += 1  # Make it 1-indexed for the algorithm
        while index > 0:
            index -= 1
            label = chr(65 + (index % 26)) + label
            index //= 26
        return label

    label_to_node = {}
    for i, node in enumerate(bot_nodes):
        label = generate_label(i)
        label_to_node[label] = node

    # Find nodes to remove
    nodes_to_remove = []
    missing_labels = []
    for label in label_list:
        if label in label_to_node:
            nodes_to_remove.append(label_to_node[label])
        else:
            missing_labels.append(label)

    # Report missing labels but continue with valid ones
    if missing_labels and not nodes_to_remove:
        return f"Error: None of the provided labels were found: {missing_labels}"

    # Remove each bot node and its child user node (the pair)
    removed_count = 0
    errors = []

    for bot_node in nodes_to_remove:
        try:
            # Check if bot node has a parent
            if not bot_node.parent:
                errors.append("Cannot remove root node")
                continue

            parent = bot_node.parent

            # Check if bot node has exactly one child that is a user node
            if len(bot_node.replies) == 0:
                errors.append("Bot node has no child user node to remove")
                continue

            if len(bot_node.replies) > 1:
                errors.append("Bot node has multiple children - cannot determine which to remove")
                continue

            user_node = bot_node.replies[0]

            # Verify the child is actually a user node
            if not (hasattr(user_node, "role") and user_node.role == "user"):
                errors.append("Bot node's child is not a user node")
                continue

            # Remove the bot node from parent's replies and preserve order
            if bot_node in parent.replies:
                # Find the index where bot_node was located
                original_index = parent.replies.index(bot_node)
                parent.replies.remove(bot_node)

                # Insert user_node's children at the same position to preserve order
                insert_index = original_index
                for child in user_node.replies:
                    child.parent = parent
                    parent.replies.insert(insert_index, child)
                    insert_index += 1
            else:
                # If bot_node not in parent.replies, still add children and update parent
                for child in user_node.replies:
                    child.parent = parent
                    parent.replies.append(child)

            # If the current conversation pointer is at the bot node, user node,
            # or a descendant of the user node, move it to the parent
            current = bot.conversation
            while current:
                if current == bot_node or current == user_node:
                    bot.conversation = parent
                    break
                current = current.parent

            removed_count += 1

        except Exception as e:
            errors.append(f"Failed to remove node pair: {str(e)}")
            continue

    # Build result message
    result_parts = []
    if removed_count > 0:
        result_parts.append(f"Successfully removed {removed_count} message pair(s)")
    if missing_labels:
        result_parts.append(f"Missing labels: {missing_labels}")
    if errors:
        result_parts.append(f"Errors: {'; '.join(errors)}")

    if not result_parts:
        return "No messages were removed"

    return " | ".join(result_parts)


def _process_string_array(input_str: str) -> List[str]:
    """Parse a string representation of an array into a list of strings.
    Only works with properly formatted Python list literals.
    Args:
        input_str (str): String representation of a Python list literal
    Returns:
        List[str]: List of parsed strings
    Raises:
        ValueError: If the input is not a valid Python list literal
    """
    result = ast.literal_eval(input_str)
    if not isinstance(result, list) or not all((isinstance(x, str) for x in result)):
        raise ValueError("Input must evaluate to a list of strings")
    return result


def _verbose_callback(responses, nodes):
    from bots.dev.cli import clean_dict, pretty

    if responses and responses[-1]:
        pretty(responses[-1])
    requests = nodes[-1].requests
    results = nodes[-1].results
    pending_results = nodes[-1].pending_results
    if requests:
        request_str = "".join((clean_dict(r) for r in requests))
        pretty(f"Tool Requests\n\n{request_str}", "System")
    else:
        pretty("No requests")
    if results:
        result_str = "".join((clean_dict(r) for r in results))
        if result_str.strip():
            pretty(f"Tool Results\n\n{result_str}", "System")
    else:
        pretty("No results")
    if pending_results:
        result_str = "".join((clean_dict(r) for r in pending_results))
        if result_str.strip():
            pretty(f"Pending Results\n\n{result_str}", "System")
    else:
        pretty("No pending results")


def _remove_dummy_from_tree(node, dummy_content):
    if hasattr(node, "pending_tool_results"):
        node.pending_tool_results = [result for result in node.pending_tool_results if result.get("content") != dummy_content]

    if hasattr(node, "tool_results"):
        node.tool_results = [result for result in node.tool_results if result.get("content") != dummy_content]

    if hasattr(node, "replies"):
        for child in node.replies:
            _remove_dummy_from_tree(child, dummy_content)


@toolify()
def subagent(tasks: str, max_iterations: str = "20") -> str:
    """Create subagent bots to work on tasks autonomously with dynamic prompts.

    Each subagent works in a loop with the same dynamic prompt system as CLI auto mode:
    - Continues with neutral prompt ("ok") by default
    - Prompted to trim context when token count is high
    - Stops when it doesn't use tools
    - On first no-tool response, prompted to write a summary

    Args:
        tasks (str): List of tasks as a string array, like ['task 1', 'task 2', 'task 3']
                    Each task gets its own subagent
        max_iterations (str): Maximum number of iterations per subagent (default: "20")

    Returns:
        str: Combined results from all subagents
    """
    import os
    import uuid

    from bots.flows import functional_prompts as fp
    from bots.foundation.base import Bot

    bot = _get_calling_bot()
    if not bot:
        return "Error: Could not find calling bot"

    # Parse parameters
    try:
        max_iter = int(max_iterations)
    except ValueError:
        return f"Error: max_iterations must be a number, got '{max_iterations}'"

    # Process the tasks
    try:
        task_list = _process_string_array(tasks)
        if not task_list:
            return "Error: No valid tasks provided"
    except Exception as e:
        return f"Error parsing tasks: {str(e)}"

    try:
        # Store original conversation point and bot settings
        original_node = bot.conversation
        original_autosave = bot.autosave
        bot.autosave = False

        # Tag the current node so we can find it after load
        branch_tag = f"_subagent_anchor_{uuid.uuid4().hex[:8]}"
        setattr(original_node, branch_tag, True)

        # Create a modified conversation node with dummy tool results
        # This prevents 'tool_use without tool_result' errors in subagents
        if original_node.tool_calls:
            dummy_results = []
            for tool_call in original_node.tool_calls:
                if tool_call.get("name") == "subagent":
                    # Use bot's tool_handler to generate provider-appropriate format
                    dummy_result = bot.tool_handler.generate_response_schema(
                        tool_call, 
                        "Subagent working..."
                    )
                    dummy_results.append(dummy_result)

            if dummy_results:
                # Temporarily add dummy results for saving
                original_results = getattr(original_node, "tool_results", [])
                original_node._add_tool_results(dummy_results)

                # Save bot state with dummy results and tag
                temp_id = str(uuid.uuid4())[:8]
                worker_id = os.environ.get("PYTEST_XDIST_WORKER", "main")
                temp_file = f"subagent_{temp_id}_{worker_id}.bot"
                bot.save(temp_file)

                # Restore original results (remove dummy results from current bot)
                original_node.tool_results = original_results
            else:
                # No dummy results needed, save normally
                temp_id = str(uuid.uuid4())[:8]
                worker_id = os.environ.get("PYTEST_XDIST_WORKER", "main")
                temp_file = f"subagent_{temp_id}_{worker_id}.bot"
                bot.save(temp_file)
        else:
            # No tool calls, save normally
            temp_id = str(uuid.uuid4())[:8]
            worker_id = os.environ.get("PYTEST_XDIST_WORKER", "main")
            temp_file = f"subagent_{temp_id}_{worker_id}.bot"
            bot.save(temp_file)

        def execute_subagent(task, parent_bot_node):
            """Execute a single subagent with the given task."""
            try:
                # Create a fresh bot copy for this subagent
                subagent = Bot.load(temp_file)
                subagent.autosave = False
                subagent.name = f"subagent_{uuid.uuid4().hex[:6]}"
                # Preserve callbacks from parent bot
                subagent.callbacks = bot.callbacks

                # Find the tagged node in the loaded bot's conversation tree
                def find_tagged_node(node):
                    """Recursively search for the node with the subagent tag."""
                    # Check current node for any subagent_anchor tags
                    for attr in dir(node):
                        if attr.startswith("_subagent_anchor_"):
                            return node
                    # Search in parent chain
                    current = node
                    while current.parent:
                        current = current.parent
                        for attr in dir(current):
                            if attr.startswith("_subagent_anchor_"):
                                return current
                    # Search in all descendants from root
                    root = node
                    while root.parent:
                        root = root.parent

                    def search_tree(n):
                        for attr in dir(n):
                            if attr.startswith("_subagent_anchor_"):
                                return n
                        for reply in n.replies:
                            result = search_tree(reply)
                            if result:
                                return result
                        return None

                    return search_tree(root)

                tagged_node = find_tagged_node(subagent.conversation)
                if tagged_node:
                    # Position at the tagged node
                    subagent.conversation = tagged_node
                    # Remove the tag from this subagent's copy
                    for attr in dir(tagged_node):
                        if attr.startswith("_subagent_anchor_"):
                            delattr(tagged_node, attr)
                            break

                branching_node = subagent.conversation

                # Ensure clean tool handler state for subagent
                if hasattr(subagent, "tool_handler") and subagent.tool_handler:
                    subagent.tool_handler.clear()

                # Track metrics for context management
                last_input_tokens = [0]
                context_reduction_cooldown = [0]
                remove_context_threshold = 40000

                # Track if we've already asked for summary
                summary_requested = [False]

                # Create dynamic continue prompt using policy (same as CLI auto mode)
                def continue_prompt_func(bot: Bot, iteration: int) -> str:
                    # Check if bot used tools in last response
                    used_tools = bool(bot.tool_handler.requests)

                    # If no tools used and haven't requested summary yet, ask for one
                    if not used_tools and not summary_requested[0]:
                        summary_requested[0] = True
                        return "Please write a summary of your work in your text response."

                    # High token count with cooldown expired -> request context reduction
                    if last_input_tokens[0] > remove_context_threshold and context_reduction_cooldown[0] <= 0:
                        context_reduction_cooldown[0] = 3
                        return "trim useless context"

                    # Decrement cooldown
                    if context_reduction_cooldown[0] > 0:
                        context_reduction_cooldown[0] -= 1

                    return "ok"

                # Callback to update metrics
                iteration_count = [0]

                def metrics_callback(responses, nodes):
                    iteration_count[0] += 1

                    # Try to get token metrics (may not be available in all contexts)
                    try:
                        from bots.observability import metrics

                        last_metrics = metrics.get_and_clear_last_metrics()
                        last_input_tokens[0] = last_metrics.get("input_tokens", 0)
                    except Exception:
                        pass

                # Stop condition: no tools used AND summary has been requested, OR max iterations reached
                def stop_on_no_tools(bot: Bot) -> bool:
                    # Stop if max iterations reached
                    if iteration_count[0] >= max_iter:
                        return True
                    # Stop if no tools used AND summary has already been requested
                    return not bot.tool_handler.requests and summary_requested[0]

                # Run the subagent with dynamic prompts
                fp.prompt_while(
                    bot=subagent,
                    first_prompt=f"(subagent task): {task}",
                    continue_prompt=continue_prompt_func,
                    stop_condition=stop_on_no_tools,
                    callback=metrics_callback,
                )

                # Stitch completed conversation back onto bot conversation
                parent_bot_node.replies.extend(branching_node.replies)
                for node in branching_node.replies:
                    node.parent = parent_bot_node

                # Return the final response
                final_response = subagent.conversation.content
                return final_response, subagent.conversation

            except StopIteration as e:
                # Max iterations reached, return what we have
                return f"Subagent stopped: {str(e)}\n\nLast response:\n{subagent.conversation.content}", subagent.conversation
            except Exception as e:
                import traceback

                traceback.print_exc()
                return f"Error running subagent: {str(e)}", None

        # Execute subagents sequentially
        responses = []
        subagent_nodes = []

        for task in task_list:
            response, node = execute_subagent(task, original_node)
            responses.append(response)
            subagent_nodes.append(node)

        # Remove the tag from the original node
        if hasattr(original_node, branch_tag):
            delattr(original_node, branch_tag)

        # Restore original bot settings
        bot.autosave = original_autosave

        # Clean up temp file
        try:
            os.remove(temp_file)
        except OSError:
            pass

        # Count successful subagents
        success_count = sum(1 for r in responses if r and not r.startswith("Error"))

        # Format results
        result_parts = [f"Successfully completed {success_count}/{len(task_list)} subagent tasks.\n"]
        for i, (task, response) in enumerate(zip(task_list, responses), 1):
            result_parts.append(f"\n--- Subagent {i}: {task[:50]}{'...' if len(task) > 50 else ''} ---")
            result_parts.append(response)

        return "\n".join(result_parts)

    except Exception as e:
        import traceback

        traceback.print_exc()
        return f"Error in subagent: {str(e)}"
