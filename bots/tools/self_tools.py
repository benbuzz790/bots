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
                    dummy_result = {"tool_use_id": tool_call["id"], "content": "Branching in progress..."}
                    dummy_results.append(dummy_result)

            if dummy_results:
                # Temporarily add dummy results for saving
                original_results = getattr(original_node, "tool_results", [])
                original_node._add_tool_results(dummy_results)

                # Save bot state with dummy results and tag
                temp_id = str(uuid.uuid4())[:8]
                temp_file = f"branch_self_{temp_id}.bot"
                bot.save(temp_file)

                # Restore original results (remove dummy results from current bot)
                original_node.tool_results = original_results
            else:
                # No dummy results needed, save normally
                temp_id = str(uuid.uuid4())[:8]
                temp_file = f"branch_self_{temp_id}.bot"
                bot.save(temp_file)
        else:
            # No tool calls, save normally
            temp_id = str(uuid.uuid4())[:8]
            temp_file = f"branch_self_{temp_id}.bot"
            bot.save(temp_file)

        def execute_branch(prompt, parent_bot_node):
            """Execute a single branch with the given prompt."""
            try:
                # Create a fresh bot copy for this branch
                branch_bot = Bot.load(temp_file)
                branch_bot.autosave = False

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
def remove_context(message_ids: str) -> str:
    """Remove bot-user message pairs from the conversation history.

    Use when you need to delete specific messages from your conversation tree
    to reduce context or remove irrelevant information. This is a demo tool
    that removes message pairs by stitching the tree after deletion.

    Note: This tool has limitations with branched conversations and will
    attempt to handle the simplest case (linear conversation paths).

    Parameters:
        message_ids (str): String representation of a list of message IDs to remove.
            Format: "['id1', 'id2', 'id3']"
            Each ID should correspond to a message in the conversation tree.

    Returns:
        str: Success message with count of removed pairs, or error message

    Example:
        remove_context("['msg_001', 'msg_002']")
    """
    bot = _get_calling_bot()
    if not bot:
        return "Error: Could not find calling bot"

    # Parse the message IDs
    try:
        id_list = _process_string_array(message_ids)
        if not id_list:
            return "Error: No valid message IDs provided"
    except Exception as e:
        return f"Error parsing message IDs: {str(e)}"

    # Find all nodes in the conversation tree and build an ID map
    def collect_nodes_with_ids(node, node_map):
        """Recursively collect all nodes that have an 'id' attribute."""
        if hasattr(node, 'id') and node.id:
            node_map[node.id] = node
        for reply in node.replies:
            collect_nodes_with_ids(reply, node_map)

    # Start from root
    root = bot.conversation._find_root()
    node_map = {}
    collect_nodes_with_ids(root, node_map)

    # Find nodes to remove
    nodes_to_remove = []
    for msg_id in id_list:
        if msg_id in node_map:
            nodes_to_remove.append(node_map[msg_id])
        else:
            return f"Error: Message ID '{msg_id}' not found in conversation tree"

    # Remove each node and stitch the tree
    removed_count = 0
    for node in nodes_to_remove:
        try:
            # Check if node has a parent
            if not node.parent:
                return f"Error: Cannot remove root node (ID: {node.id if hasattr(node, 'id') else 'unknown'})"

            parent = node.parent

            # Remove this node from parent's replies
            if node in parent.replies:
                parent.replies.remove(node)

            # Stitch: attach this node's children to its parent
            for child in node.replies:
                child.parent = parent
                parent.replies.append(child)

            # If the current conversation pointer is at this node or a descendant,
            # move it to the parent
            current = bot.conversation
            while current:
                if current == node:
                    bot.conversation = parent
                    break
                current = current.parent

            removed_count += 1

        except Exception as e:
            return f"Error removing node: {str(e)}"

    return f"Successfully removed {removed_count} message(s) from conversation tree"


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