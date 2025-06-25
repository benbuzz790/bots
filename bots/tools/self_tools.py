import ast
import inspect
import json
from typing import List, Optional

from bots.dev.decorators import handle_errors
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


@handle_errors
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
    # Import _get_calling_bot locally to avoid decorator global namespace issues
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
    return f"Settings updated successfully. Current settings: " f"temperature={bot.temperature}, max_tokens={bot.max_tokens}"


@handle_errors
def branch_self(self_prompts: str, allow_work: str = "False") -> str:
    """Create multiple conversation branches to explore different approaches or tackle separate tasks.
    Think of this like opening multiple browser tabs - each branch starts from this point
    and explores a different direction. Perfect for when you need to:
    - Try different solutions to the same problem
    - Handle multiple related tasks separately
    - Break down a complex request into smaller parts (when you have more than ~6 tasks)
    - Compare different approaches side-by-side
    Each branch gets its own copy of the conversation up to this point, then follows
    the prompt you give it. The branches run one after another, not at the same time.
    Args:
        self_prompts (str): List of prompts as a string array, like ['task 1', 'task 2', 'task 3']
                           Each prompt becomes a separate conversation branch
        allow_work (str): 'True' to let each branch use tools and continue working until done
                         'False' (default) for single-response branches
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
    # Import _get_calling_bot locally to avoid decorator global namespace issues
    import ast  # Also import ast locally
    import json  # Also import json locally
    from typing import List  # Import List type
    from bots.flows import functional_prompts as fp  # Import functional_prompts locally
    def _process_string_array_local(input_str: str) -> List[str]:
        """Parse a string representation of an array into a list of strings."""
        result = ast.literal_eval(input_str)
        if not isinstance(result, list) or not all(isinstance(x, str) for x in result):
            raise ValueError("Input must evaluate to a list of strings")
        return result
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
    # Insert a dummy result to prevent repeated tool calls
    if not bot.tool_handler.requests:
        return "Error: No branch_self tool request found"
    request = bot.tool_handler.requests[-1]
    dummy_result = bot.tool_handler.generate_response_schema(
        request=request,
        tool_output_kwargs=json.dumps({"status": "branching_in_progress"}),
    )
    bot.tool_handler.add_result(dummy_result)
    bot.conversation._add_tool_results([dummy_result])
    if not bot:
        return "Error: Could not find calling bot"
    allow_work = allow_work.lower() == "true"
    message_list = _process_string_array_local(self_prompts)
    if not message_list:
        return "Error: No valid messages provided"
    original_node = bot.conversation
    if not original_node:
        return "Error: No current conversation node found"
    for i, item in enumerate(message_list):
        message_list[i] = f"(self-prompt): {item}"
    # Store original respond method and create debug wrapper
    original_respond = bot.respond
    branch_counter = 0
    def debug_respond(self, prompt):
        nonlocal branch_counter
        print(f"\n=== BRANCH {branch_counter} DEBUG ===")
        print(f"PROMPT: {prompt}")
        print("=" * 50)
        # Call original respond method
        response = original_respond(prompt)
        print(f"RESPONSE: {response}")
        print(f"=== END BRANCH {branch_counter} DEBUG ===\n")
        branch_counter += 1
        return response
    # Temporarily override the respond method
    bot.respond = debug_respond.__get__(bot, type(bot))
    try:
        if not allow_work:
            responses, nodes = fp.branch(bot, message_list)
        else:
            responses, nodes = fp.branch_while(bot, message_list)
    finally:
        # Always restore the original respond method
        bot.respond = original_respond
    # Clean up
    bot.conversation = original_node
    bot.conversation.tool_results = [r for r in bot.conversation.tool_results if r != dummy_result]
    for reply in bot.conversation.replies:
        reply.tool_results = [r for r in reply.tool_results if r != dummy_result]
    bot.tool_handler.results = [r for r in bot.tool_handler.results if r != dummy_result]
    # return
    if not any(response is None for response in responses):
        return f"Successfully created {len(responses)} conversation branches"
    else:
        error_messages = []
        for i, response in enumerate(responses):
            if response is None:
                error_messages.append(f"Tool Error: branch {i+1} failed")
        return "\n".join(error_messages)
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


@handle_errors
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
    if not isinstance(result, list) or not all(isinstance(x, str) for x in result):
        raise ValueError("Input must evaluate to a list of strings")
    return result

