from typing import Optional, Dict, Any, List
import inspect
from bots.foundation.base import Bot, ConversationNode, ToolHandler
import json
from bots.flows import functional_prompts as fp
from typing import Optional
import time

# Let's isolate my spaghetti code
def _get_calling_bot() ->Optional[Bot]:
    """Helper function to get a reference to the calling bot.

    Returns:
        Optional[Bot]: Reference to the calling bot or None if not found
    """
    frame = inspect.currentframe()
    while frame:
        if (frame.f_code.co_name == 'handle_response' and 'self' in frame.
            f_locals and isinstance(frame.f_locals['self'], ToolHandler)):
            for frame_up in inspect.stack()[1:]:
                if 'self' in frame_up.frame.f_locals and isinstance(frame_up
                    .frame.f_locals['self'], Bot):
                    return frame_up.frame.f_locals['self']
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

''' # string literal for preservation through bot edits.
# Bug assessment:
# Tool calls are processed in base.py before the text response,
# therefore, any tool like this which messes with the conversation
# structure will NOT contain the bot's response until AFTER execution
# is complete.

# Questions:
# 1. Does tool processing need to happen first?
# 2. Can tool processing happen in mailbox.process_response? Probably
# 3. Is there a way around this here through fancy conversation management? NO
'''

def branch_self(self_prompts: str, allow_work: str = 'False') ->str:
    """Branches your conversation using a list of self-prompts. The prompts 
    will be sent as use messages in response to your message that calls this
    tool. Tags the messages with (self-prompt) to distinguish from legitimate
    user messages. Avoid losing your place -- if you see the tag, know that 
    you're on a branch and consider carefully whether you should branch further.

    Use when you need to:
    - explore multiple conversation paths in parallel.
    - execute a parallelizable list of large tasks
    - 'spin off' tangent tasks
    
    Each message will start a new conversation branch from the current message.

    Parameters:
        self-prompts (str): Array formatted.
        allow_work: 'True' or 'False' (default). If True, allows each branch to work until it
            does not respond with any tool calls (i.e. each branch will be a chain).

    Returns:
        str: success message or error string.
    """
    bot = _get_calling_bot()
    if not bot:
        return 'Error: Could not find calling bot'
    try:
        allow_work = bool(allow_work)
        message_list = [msg.strip() for msg in self_prompts.split(',') if msg.strip()]
        if not message_list:
            return 'Error: No valid messages provided'
        original_node = bot.conversation
        if not original_node:
            return 'Error: No current conversation node found'

        for i, item in enumerate(message_list):
            message_list[i] = f"(self-prompt): {item}"
            print(message_list[i])

        try:
            if not allow_work:
                responses, nodes = fp.branch(bot, message_list)
            else:
                responses, nodes = fp.branch_while(bot, message_list)
        except Exception as e:
            return 'Branch operation failed:' + str(e)

        bot.conversation = original_node

        return f'Successfully created {len(responses)} conversation branches'
    except Exception as e:
        return f'Error: {str(e)}'

def add_tools(filepath: str) ->str:
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
    # Add validation
    bot.add_tools(filepath)