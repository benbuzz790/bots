from typing import Optional, Dict, Any, List
import inspect
from bots.foundation.base import Bot, ConversationNode, ToolHandler
import json
from bots.flows import functional_prompts as fp
from typing import Optional
from typing import List
import ast


def _get_calling_bot() ->Optional[Bot]:
    """Helper function to get a reference to the calling bot.

    Returns:
        Optional[Bot]: Reference to the calling bot or None if not found
    """
    frame = inspect.currentframe()
    while frame:
        if (frame.f_code.co_name == '_cvsn_respond' and 'self' in frame.f_locals):
            potential_bot = frame.f_locals['self']
            if isinstance(potential_bot, Bot):
                return potential_bot
        frame = frame.f_back
    return None


def _get_own_info() ->str:
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
        return 'Error: Could not find calling bot'
    info = {'name': bot.name, 'role': bot.role, 'role_description': bot.
        role_description, 'model_engine': bot.model_engine.value,
        'temperature': bot.temperature, 'max_tokens': bot.max_tokens,
        'tool_count': len(bot.tool_handler.tools) if bot.tool_handler else 0}
    return json.dumps(info)


def _modify_own_settings(temperature: str=None, max_tokens: str=None) ->str:
    """Modify your settings.

    Use when you need to adjust your configuration parameters.

    Parameters:
        temperature (str, optional): New temperature value as string (0.0 to 1.0)
        max_tokens (str, optional): New maximum tokens value as string (must be > 0)

    Returns:
        str: Description of changes made or error message
    """
    bot = _get_calling_bot()
    if not bot:
        return 'Error: Could not find calling bot'
    try:
        if temperature is not None:
            temp_float = float(temperature)
            if not 0.0 <= temp_float <= 1.0:
                return 'Error: Temperature must be between 0.0 and 1.0'
            bot.temperature = temp_float
        if max_tokens is not None:
            tokens_int = int(max_tokens)
            if tokens_int <= 0:
                return 'Error: Max tokens must be a positive integer'
            bot.max_tokens = tokens_int
        return (
            f'Settings updated successfully. Current settings: temperature={bot.temperature}, max_tokens={bot.max_tokens}'
            )
    except ValueError:
        return (
            'Error: Invalid number format. Temperature must be a float and max_tokens must be an integer'
            )
    except Exception as e:
        return f'Error: {str(e)}'


def branch_self(self_prompts: str, allow_work: str='False') ->str:
    """Branches your conversation using a list of self-prompts. The prompts
    will be sent as user messages in response to your message that calls this
    tool. Also tags the messages with (self-prompt) to distinguish from legitimate
    user messages.

    Use when you need to:
    - explore multiple conversation paths.
    - break down a large list of tasks (>~6)

    Branches will be traversed sequentially.

    Each message will start a new conversation branch from the current message.

    Parameters:
        self_prompts (str): Array formatted as a string, i.e. ['1', '2', '3']
        allow_work: 'True' or 'False' (default). If True, allows each branch to work until it
            does not respond with any tool calls (i.e. each branch will be a chain).

    Returns:
        str: success message or error string.
    """

    bot = _get_calling_bot()


    # Insert a dummy result to prevent repeated tool calls
    if not bot.tool_handler.requests:
        return 'Error: No branch_self tool request found'
    
    request = bot.tool_handler.requests[-1]
    dummy_result = bot.tool_handler.generate_response_schema(
        request = request, 
        tool_output_kwargs = json.dumps({'status': 'branching_in_progress'})
    )
    bot.tool_handler.add_result(dummy_result)
    bot.conversation.add_tool_results([dummy_result])

    if not bot:
        return 'Error: Could not find calling bot'
    try:
        allow_work = allow_work.lower() == 'true'

        message_list = _process_string_array(self_prompts)

        if not message_list:
            return 'Error: No valid messages provided'
        
        original_node = bot.conversation
        if not original_node:
            return 'Error: No current conversation node found'
        
        for i, item in enumerate(message_list):
            message_list[i] = f'(self-prompt): {item}'
        
        try:
            if not allow_work:
                responses, nodes = fp.branch(bot, message_list)
            else:
                responses, nodes = fp.branch_while(bot, message_list)
        except Exception as e:
            return 'Branch operation failed:' + str(e)
        
        # Clean up
        bot.conversation = original_node
        bot.conversation.tool_results = [r for r in bot.conversation.tool_results if r != dummy_result]
        for reply in bot.conversation.replies:
            reply.tool_results = [r for r in reply.tool_results if r != dummy_result]
        bot.tool_handler.results = [r for r in bot.tool_handler.results if r != dummy_result]

        # return
        if not any(response is None for response in responses):
            return f'Successfully created {len(responses)} conversation branches'
        else:
            error_messages = []
            for i, response in enumerate(responses):
                if response is None:
                    error_messages.append(f"Tool Error: branch {i+1} failed")
            return "\n".join(error_messages)

    except Exception as e:
        return f'Error: {str(e)}'


def _add_tools(filepath: str) ->str:
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


def _process_string_array(input_str: str) ->List[str]:
    """Parse a string representation of an array into a list of strings.
    Only works with properly formatted Python list literals.
    
    Args:
        input_str (str): String representation of a Python list literal
        
    Returns:
        List[str]: List of parsed strings
        
    Raises:
        ValueError: If the input is not a valid Python list literal
    """
    try:
        result = ast.literal_eval(input_str)
        if not isinstance(result, list) or not all(isinstance(x, str) for x in
            result):
            raise ValueError('Input must evaluate to a list of strings')
        return result
    except (SyntaxError, ValueError) as e:
        raise ValueError(f'Invalid input format: {e}')
