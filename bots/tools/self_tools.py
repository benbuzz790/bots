import ast
import inspect
import json
from typing import List, Optional
from bots.dev.decorators import handle_errors
from bots.flows import functional_prompts as fp
from bots.flows import recombinators
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
    info = {"name": bot.name, "role": bot.role, "role_description": bot.role_description, "model_engine": bot.model_engine.value, "temperature": bot.temperature, "max_tokens": bot.max_tokens, "tool_count": len(bot.tool_handler.tools) if bot.tool_handler else 0}
    return json.dumps(info)

@handle_errors
def _modify_own_settings(temperature: str=None, max_tokens: str=None) -> str:
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

@handle_errors
def branch_self(self_prompts: str, allow_work: str="False", parallel: str="False", recombine: str="none") -> str:
    """Create multiple conversation branches to explore different approaches or tackle separate tasks.
    Each branch gets its own copy of the conversation up to this point, then follows
    the prompt you give it. The branches run one after another if parallel is "False" (default).
    Args:
        self_prompts (str): List of prompts as a string array, like ['task 1', 'task 2', 'task 3']
                           Each prompt becomes a separate conversation branch
        allow_work (str): 'True' to let each branch use tools and continue working until done
                         'False' (default) for single-response branches
        parallel (str): 'True' to let branches work in parallel, 'False' for sequential (default).
        recombine (str): One of ('concatenate', 'llm_merge', 'llm_vote', 'llm_judge'). If specified
                         combines the final messages from each branch using that method.
    Returns:
        str: Success message with branch count, or error details if something went wrong
    Writing effective branch prompts:
        Each prompt should be a complete, self-contained instruction that includes:
        REQUIRED:
        - Task instruction: What specific action to take
        - Definition of done: How to know when the task is complete, typically in
        terms of a specific side effect or set of side effects on files or achieved
        through use of your available tools.
        OPTIONAL:
        - Tool suggestions: Which tools of yours might be helpful.
        - Context to gather: What information to look up or files to examine first
        - Output format: Specific system side effect, with specific qualities
        - Success criteria: What makes a good vs. poor result
        Good prompt examples:
        - "Search for recent AI safety research papers, then create a summary report
           highlighting key findings and methodologies. Done when I have a 2-page
           summary with at least 5 recent citations."
        - "Analyze our Q3 sales data from Google Drive, identify top 3 performance
           trends, and create visualizations. Use artifacts for charts. Done when
           I have clear charts showing trends with actionable insights."
    Example usage:
        branch_self("['Analyze the data for trends', 'Create visualizations', 'Write summary report']")
    """
    import json
    import os
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from bots.foundation.base import Bot

    bot = _get_calling_bot()
    if not bot:
        return "Error: Could not find calling bot"

    original_conversation_node = bot.conversation

    # Parse parameters
    allow_work = allow_work.lower() == "true"
    parallel = parallel.lower() == "true"
    recombine = recombine.lower()

    valid_recombine_options = ["none", "concatenate", "llm_judge", "llm_vote", "llm_merge"]
    if recombine not in valid_recombine_options:
        return f"Error: Invalid recombine option. Valid: {valid_recombine_options}"

    # Process the prompts
    message_list = _process_string_array(self_prompts)
    if not message_list:
        return "Error: No valid messages provided"

    # Add self-prompt prefix
    for i, item in enumerate(message_list):
        message_list[i] = f"(self-prompt): {item}"

    try:
        # Save the current bot state to create copies
        original_autosave = bot.autosave
        bot.autosave = False

        # CRITICAL: Add dummy tool result BEFORE saving to prevent recursive calls
        # The assistant node has an unresolved branch_self tool call
        # We need to add a user node with a dummy result so branch bots don't try to call it again
        save_conversation_node = original_conversation_node
        dummy_user_node = None

        if original_conversation_node.tool_calls:
            # Find the branch_self tool call
            tool_call = None
            for tc in original_conversation_node.tool_calls:
                if tc.get('name') == 'branch_self':
                    tool_call = tc
                    break

            if tool_call:
                # Create user node with dummy tool result
                dummy_result = {
                    'tool_use_id': tool_call['id'],
                    'content': 'Branching in progress...'
                }
                dummy_user_node = original_conversation_node._add_reply(
                    role="user",
                    content="Executing branches...",  # Non-empty content required by API
                    tool_results=[dummy_result],
                    sync_tools=False  # Don't sync tool results
                )
                save_conversation_node = dummy_user_node
                bot.conversation = dummy_user_node

        # Save bot state
        temp_file = "temp_branch_self_bot.bot"
        bot.save(temp_file)

        # Restore bot's conversation pointer to original position
        bot.conversation = original_conversation_node

        def execute_branch(index, prompt):
            """Execute a single branch with the given prompt."""
            try:
                # Create a fresh bot copy for this branch
                branch_bot = Bot.load(temp_file)
                branch_bot.autosave = False

                if allow_work:
                    # Use iterative approach for work
                    from bots.flows import functional_prompts as fp
                    response = branch_bot.respond(prompt)
                    while not fp.conditions.tool_not_used(branch_bot):
                        response = branch_bot.respond("ok")
                else:
                    # Single response
                    response = branch_bot.respond(prompt)

                return index, response, branch_bot
            except Exception as e:
                import traceback
                traceback.print_exc()
                return index, None, None

        # Execute branches
        responses = [None] * len(message_list)
        branch_bots = [None] * len(message_list)

        if parallel:
            # Parallel execution
            with ThreadPoolExecutor() as executor:
                futures = [executor.submit(execute_branch, i, prompt)
                          for i, prompt in enumerate(message_list)]

                for future in as_completed(futures):
                    index, response, result_bot = future.result()
                    responses[index] = response
                    branch_bots[index] = result_bot
        else:
            # Sequential execution
            for i, prompt in enumerate(message_list):
                index, response, result_bot = execute_branch(i, prompt)
                responses[index] = response
                branch_bots[index] = result_bot

        # Restore original bot settings
        bot.autosave = original_autosave

        # Clean up temp file
        try:
            os.remove(temp_file)
        except OSError:
            pass

        # Check if all branches succeeded
        failed_count = sum(1 for r in responses if r is None)
        if failed_count == len(responses):
            return "Error: All branches failed to execute"
        elif failed_count > 0:
            print(f"Warning: {failed_count} branches failed")

        # Merge the branch trees back into the original conversation
        final_container = merge_branch_trees(original_conversation_node, branch_bots, message_list, responses, dummy_user_node)

        # CRITICAL: Update bot's conversation pointer to the final container node
        # This prevents duplicate tool results when the next message is added
        if final_container:
            bot.conversation = final_container
        elif dummy_user_node and dummy_user_node.replies:
            # Find the container node
            for reply in dummy_user_node.replies:
                if reply.role == "assistant" and "branches:" in reply.content:
                    bot.conversation = reply
                    break

        # Handle recombination if requested
        if recombine != "none" and responses:
            # Filter out None responses
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

                # Add the combined result as a new assistant message
                bot.conversation = bot.conversation._add_reply(
                    role="assistant",
                    content=f"[Combined result using {recombine}]:\n{combined}",
                    sync_tools=False
                )

        # Return success message
        exec_type = "parallel" if parallel else "sequential"
        work_type = "iterative" if allow_work else "single-response"
        success_count = len(responses) - failed_count
        return f"Successfully created {success_count} {exec_type} {work_type} branches"

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error in branch_self: {str(e)}"

@handle_errors
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


def verbose_callback(responses, nodes):
    from bots.dev.cli import pretty, clean_dict
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
def merge_branch_trees(branch_point, branch_bots, branch_prompts, responses, dummy_user_node=None):
    """Merge the conversation trees from branch bots back into the original conversation tree.

    Args:
        branch_point: The conversation node where branching occurred (original bot's current position)
        branch_bots: List of bot instances that executed the branches
        branch_prompts: List of prompts that were sent to each branch
        responses: List of responses from each branch
        dummy_user_node: The user node with dummy tool result (if created)
    """
    print(f"DEBUG merge_branch_trees: Starting merge")
    # The branch_point is the assistant node with the unresolved branch_self tool call
    # Check if we already have a user node with the tool result (from dummy result)

    # Look for existing user node with tool result
    user_node = dummy_user_node
    container_node = None

    if not user_node and branch_point.replies:
        for reply in branch_point.replies:
            if reply.role == "user" and reply.tool_results:
                # This is our dummy result node
                user_node = reply
                break

    if user_node:
        print(f"DEBUG merge_branch_trees: Found user node with {len(user_node.tool_results)} tool results")
        # Update the dummy tool result with the final result
        if user_node.tool_results and branch_point.tool_calls:
            tool_call_id = branch_point.tool_calls[0]['id']
            for i, result in enumerate(user_node.tool_results):
                if result.get('tool_use_id') == tool_call_id and result.get('content') == 'Branching in progress...':
                    # Update the dummy result with the final result
                    exec_type = "parallel" if len(responses) > 1 else "sequential"
                    work_type = "iterative" if any("ok" in str(b.conversation) for b in branch_bots if b) else "single-response"
                    result_content = f"Successfully created {len(responses)} {exec_type} {work_type} branches"
                    user_node.tool_results[i]['content'] = result_content
                    print(f"DEBUG merge_branch_trees: Updated tool result content")
                    break

        # Check if we already have a container node
        if user_node.replies:
            for user_reply in user_node.replies:
                if user_reply.role == "assistant" and "Processing branches" in user_reply.content:
                    container_node = user_reply
                    break

    if not user_node:
        # No existing user node, we need to create one
        # This shouldn't happen if branch_self added the dummy result correctly
        tool_call_id = None
        if branch_point.tool_calls:
            for tool_call in branch_point.tool_calls:
                if tool_call.get('name') == 'branch_self':
                    tool_call_id = tool_call['id']
                    break

        if tool_call_id:
            # Create the final tool result
            exec_type = "parallel" if len(responses) > 1 else "sequential"
            work_type = "iterative" if any("ok" in str(b.conversation) for b in branch_bots if b) else "single-response"
            result_content = f"Successfully created {len(responses)} {exec_type} {work_type} branches"

            tool_result = {
                'tool_use_id': tool_call_id,
                'content': result_content
            }

            # Add user node with tool result
            user_node = branch_point._add_reply(
                role="user",
                content="Branch execution completed.",  # Non-empty content required by API
                tool_results=[tool_result],
                sync_tools=False  # Don't sync to avoid duplicates
            )
        else:
            # No branch_self tool call, just use branch_point
            user_node = branch_point

    # If we don't have a container node yet, create one
    if not container_node:
        # Update the container content to reflect the final state
        container_node = user_node._add_reply(
            role="assistant",
            content=f"Executed {len(responses)} branches:",
            sync_tools=False  # Don't sync to avoid duplicates
        )
    else:
        # Update the existing container node's content
        container_node.content = f"Executed {len(responses)} branches:"

    print(f"DEBUG merge_branch_trees: After creating container, user node has {len(user_node.tool_results)} tool results")

    # The branches should have already added their responses to the container node
    # We just need to make sure they're properly structured
    # If branches were added elsewhere, we need to move them

    # Check if branches were added to the container
    existing_branch_count = 0
    for reply in container_node.replies:
        if reply.role == "user" and "(self-prompt):" in reply.content:
            existing_branch_count += 1

    # Only add branches if they weren't already added
    if existing_branch_count < len(responses):
        for i, (branch_bot, prompt, response) in enumerate(zip(branch_bots, branch_prompts, responses)):
            if branch_bot is None or response is None:
                continue  # Skip failed branches

            # Check if this branch was already added
            branch_exists = False
            for reply in container_node.replies:
                if reply.role == "user" and reply.content == prompt:
                    branch_exists = True
                    break

            if not branch_exists:
                # Add the branch prompt as a user node
                branch_user = container_node._add_reply(
                    role="user", 
                    content=prompt,
                    sync_tools=False  # Don't sync to avoid duplicates
                )

                # Add the branch response as an assistant node
                branch_assistant = branch_user._add_reply(
                    role="assistant",
                    content=response,
                    sync_tools=False  # Don't sync to avoid duplicates
                )

                # If the branch did more work (has replies), copy those too
                branch_conversation = branch_bot.conversation
                if branch_conversation.replies:
                    merge_sub_branches(branch_assistant, branch_conversation.replies)

    print(f"DEBUG merge_branch_trees: Final user node has {len(user_node.tool_results)} tool results")
    return container_node


def merge_sub_branches(target_node, source_replies):
    """Recursively merge sub-branches from source replies into target node.

    Args:
        target_node: The node in the original tree to attach replies to
        source_replies: List of reply nodes from the branch bot to merge
    """
    for source_reply in source_replies:
        # Copy the reply node
        merged_reply = target_node._add_reply(
            role=source_reply.role,
            content=source_reply.content,
            tool_calls=source_reply.tool_calls.copy() if source_reply.tool_calls else [],
            tool_results=source_reply.tool_results.copy() if source_reply.tool_results else [],
            pending_results=source_reply.pending_results.copy() if source_reply.pending_results else [],
            sync_tools=False  # Don't sync to avoid duplicates
        )

        # Recursively merge any further replies
        if source_reply.replies:
            merge_sub_branches(merged_reply, source_reply.replies)