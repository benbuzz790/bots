from typing import List, Callable, Any, Tuple, Union
from bots.foundation.base import Bot
from bots.foundation.base import ConversationNode


"""Custom typing for clarity (hopefully)"""
Prompt = str
Response = str
PromptNode = ConversationNode
ResponseNode = ConversationNode
Condition = Callable[[Bot], bool]
DynamicPrompt = Callable[[Any], Prompt]
RecombinatorFunction = Callable[[List[Response], List[ResponseNode]], Tuple[Response, ResponseNode]]


class conditions:
    """
    A list of frequently used and helpful conditions for convenience
    """
    def tool_used(bot: Bot):
        return bool(bot.tool_handler.requests)

    def tool_not_used(bot: Bot):
        return not bool(bot.tool_handler.requests)

    def said_DONE(bot: Bot):
        return 'DONE' in bot.conversation.content



def basic(bot: Bot, prompt: Prompt) ->Tuple[Response, ResponseNode]:
    """
    Included as a demonstration. Sends prompt to bot and returns the result.
    """
    response = bot.respond(prompt)
    node = bot.conversation
    return response, node


def chain(bot: Bot, prompts: List[Prompt]) ->Tuple[List[Response], List[
    ResponseNode]]:
    """
    Implements a chain of thought by sending a series of prompts to the bot.

    Args:
    bot (Bot): The bot to use for the responses.
    prompts (List[Prompt]): A list of prompts to send to the bot in order.

    Returns:
    Tuple[List[Response], List[ResponseNode]]: A tuple containing a list of response strings and a list of corresponding ConversationNodes.
    """
    responses = []
    nodes = []
    for prompt in prompts:
        response = bot.respond(prompt)
        responses.append(response)
        nodes.append(bot.conversation)
    return responses, nodes


def branch(bot: Bot, prompts: List[Prompt]) ->Tuple[List[Response], List[
    ResponseNode]]:
    """
    Creates multiple conversation branches from the current node.
    Each branch starts from the current conversation state.

    Args:
    bot (Bot): The bot to use for the responses.
    prompts (List[Prompt]): A list of prompts to send to the bot.

    Returns:
    Tuple[List[Response], List[ResponseNode]]: A tuple containing a 
    list of response strings and a list of corresponding 
    ConversationNodes. If an error occurs, 'None' is sent for both the 
    response and node.
    """
    original_conversation = bot.conversation
    responses = []
    nodes = []
    for prompt in prompts:
        bot.conversation = original_conversation
        try:
            response = bot.respond(prompt)
            node = bot.conversation
        except:
            response = None
            node = None
        finally:
            responses.append(response)
            nodes.append(node)            
    return responses, nodes


def recombine(bot: Bot, responses: List[Response], 
              nodes: List[ResponseNode], 
              recombinator_function: RecombinatorFunction
              ) ->Tuple[Response, ResponseNode]:
    """
    Recombines multiple conversation branches using a provided function.

    Args:
    bot (Bot): The bot to use for the responses. (Kept for potential future use)
    responses (List[Response]): A list of response strings.
    nodes (List[ResponseNode]): A list of corresponding ConversationNodes.
    recombinator_function (RecombinatorFunction): A function that takes a list of Responses and a list of ResponseNodes and returns a single Response and ResponseNode.

    Returns:
    Tuple[Response, ResponseNode]: A tuple containing the recombined response string and its corresponding ConversationNode.
    """
    response, node = recombinator_function(responses, nodes)
    bot.conversation = node
    return response, node


def tree_of_thought(bot: Bot, 
                    prompts: List[Prompt], 
                    recombinator_function: RecombinatorFunction
                    ) ->Tuple[Response, ResponseNode]:
    """
    Implements a tree of thought approach by branching into multiple 
    conversation paths and then recombining the results.

    Args:
    bot (Bot): The bot to use for the responses.
    prompts (List[Prompt]): A list of prompts to create branches with.
    recombinator_function (RecombinatorFunction): A function that takes 
        a list of Responses and a list of ResponseNodes and returns a 
        single Response and ResponseNode.

    Returns:
    Tuple[Response, ResponseNode]: A tuple containing the final recombined 
        response string and its corresponding ConversationNode.
    """
    responses, nodes = branch(bot, prompts)
    final_response = recombine(bot, responses, nodes, recombinator_function)
    return final_response


def prompt_while(bot: Bot, 
                 first_prompt: Prompt, 
                 continue_prompt: Prompt = 'ok',
                 stop_condition: Condition = conditions.tool_not_used,
                ) ->Tuple[List[Response], List[ResponseNode]]:
    """
    Repeatedly prompts the bot until a stop condition is met.

    Args:
    bot (Bot): The bot to use for the responses.
    prompt (Prompt): The prompt to repeatedly send to the bot.
    stop_condition (StopCondition): A function that takes a Response and returns True if the loop should stop.

    Returns:
    Tuple[List[Response], List[ResponseNode]]: A tuple containing a list of response strings and a list of corresponding ConversationNodes.
    """
    responses = []
    nodes = []
    response = bot.respond(first_prompt)
    responses.append(response)
    nodes.append(bot.conversation)
    while not stop_condition(bot):
        response = bot.respond(continue_prompt)
        responses.append(response)
        nodes.append(bot.conversation)
    return responses, nodes


def prompt_for(bot: Bot, items: List[Any], 
               dynamic_prompt: DynamicPrompt,
               should_branch: bool=False
              ) ->Tuple[List[Response], List[ResponseNode]]:
    """
    Generates prompts for a list of items and gets responses from the bot.

    Args:
    bot (Bot): The bot to use for the responses.
    items (List[Any]): A list of items to generate prompts for.
    dynamic_prompt (DynamicPrompt): A function that takes an item and returns a prompt.
    branch (bool): If True, creates separate conversation branches for each item. 
                   If False (default), processes items sequentially in the same conversation.
    
    Returns:
    Tuple[List[Response], List[ResponseNode]]: A tuple containing a list of response strings and a list of corresponding ConversationNodes.
    """
    prompts = [dynamic_prompt(item) for item in items]
    if should_branch:
        return branch(bot, prompts)
    else:
        return chain(bot, prompts)


def chain_while(bot: Bot, 
                prompt_list: List[Prompt], 
                stop_condition:Condition = conditions.tool_not_used, 
                continue_prompt: str = 'ok'
                ) ->Tuple[List[Response], List[ResponseNode]]:
    """
    Sends a series of messages. Moves to next message when stop_condition(bot) is met.
    Sends continue_prompt if condition is not met.
    Clears tool handler.
    
    Args:
    bot (Bot): The bot to use for the responses.
    prompt_list (List[Prompt]): List of prompts to send in sequence
    stop_condition (Condition): Function that takes a Bot and returns True when ready to move to next prompt
    continue_prompt (str): Prompt to send when stop_condition is False
    
    Returns:
    Tuple[List[Response], List[ResponseNode]]: Lists of responses and their corresponding nodes
    """
    responses = []
    nodes = []
    for p in prompt_list:
        response = bot.respond(p)
        responses.append(response)
        nodes.append(bot.conversation)
        while not stop_condition(bot):
            response = bot.respond(continue_prompt)
            responses.append(response)
            nodes.append(bot.conversation)
    bot.tool_handler.clear()
    return responses, nodes

def branch_while(bot: Bot, 
                 prompt_list: List[Prompt], 
                 stop_condition: Condition = conditions.tool_not_used, 
                 continue_prompt: str = 'ok'
                 ) ->Tuple[List[Response], List[ResponseNode]]:
    """
    Creates parallel branches for a list of prompts, continuing each branch until its stop condition is met.
    Each branch starts from the current conversation state and develops independently.

    Args:
    bot (Bot): The bot to use for the responses.
    prompt_list (List[Prompt]): List of prompts to create branches with
    stop_condition (Condition): Function that takes a Bot and returns True when ready to move to next prompt
    continue_prompt (str): Prompt to send when stop_condition is False

    Returns:
    Tuple[List[Response], List[ResponseNode]]: Lists of final responses and their corresponding nodes from each branch. If an error occurs on a branch, the response and node returned are 'None'.
    """
    original_conversation = bot.conversation
    responses = []
    nodes = []
    for initial_prompt in prompt_list:
        try:
            bot.conversation = original_conversation
            response = bot.respond(initial_prompt)
            while not stop_condition(bot):
                response = bot.respond(continue_prompt)
            node = bot.conversation
        except Exception as e:
            response = None
            node = None
        finally:
            responses.append(response)
            nodes.append(node)
    return responses, nodes
