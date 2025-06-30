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
    import json #hack for now
    bot = _get_calling_bot()
    original_conversation_node = bot.conversation
    allow_work = allow_work.lower() == "true"
    parallel = parallel.lower() == "true"
    recombine = recombine.lower()
    valid_recombine_options = ["none", "concatenate", "llm_judge", "llm_vote", "llm_merge"]
    if recombine not in valid_recombine_options:
        return f"Error: Invalid recombine option. Valid: {valid_recombine_options}"
    message_list = _process_string_array(self_prompts)
    if not message_list:
        return "Error: No valid messages provided"
    for i, item in enumerate(message_list):
        message_list[i] = f"(self-prompt): {item}"
    try:
        if parallel:
            if allow_work:
                responses, nodes = fp.par_branch_while(bot, message_list, callback=verbose_callback)
            else:
                responses, nodes = fp.par_branch(bot, message_list, callback=verbose_callback)
        elif allow_work:
            responses, nodes = fp.branch_while(bot, message_list, callback=verbose_callback)
        else:
            responses, nodes = fp.branch(bot, message_list, callback=verbose_callback)
        bot.conversation = original_conversation_node
    except Exception as e:
        bot.conversation = original_conversation_node
        return f"Error during branching: {str(e)}"
    if any((response is None for response in responses)):
        error_messages = [f"Branch {i+1} failed" for i, r in enumerate(responses) if r is None]
        return "Errors: " + "; ".join(error_messages)
    if recombine == "none":
        exec_type = "parallel" if parallel else "sequential"
        work_type = "iterative" if allow_work else "single-response"
        return f"Successfully created {len(responses)} {exec_type} {work_type} branches"
    else:
        try:
            if recombine == "concatenate":
                combined_response, _ = recombinators.recombinators.concatenate(responses, nodes)
            elif recombine == "llm_judge":
                combined_response, _ = recombinators.recombinators.llm_judge(responses, nodes)
            elif recombine == "llm_vote":
                combined_response, _ = recombinators.recombinators.llm_vote(responses, nodes)
            elif recombine == "llm_merge":
                combined_response, _ = recombinators.recombinators.llm_merge(responses, nodes)
            return combined_response
        except Exception as e:
            return f"Error during {recombine} recombination: {str(e)}"

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