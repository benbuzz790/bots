from typing import List, Callable, Any, Tuple
from bots.foundation.base import Bot
from bots.foundation.base import ConversationNode
from concurrent.futures import ThreadPoolExecutor, as_completed
import os


"""Custom typing for clarity (hopefully)"""
Prompt = str
Response = str
PromptNode = ConversationNode
ResponseNode = ConversationNode
Condition = Callable[[Bot], bool]
DynamicPrompt = Callable[[Any], Prompt]
RecombinatorFunction = Callable[[List[Response], List[ResponseNode]], Tuple[Response, ResponseNode]]
"""Add callbacks?"""


class conditions:
    """
    A list of frequently used and helpful conditions for convenience
    """

    def tool_used(bot: Bot):
        return bool(bot.tool_handler.requests)

    def tool_not_used(bot: Bot):
        return not bool(bot.tool_handler.requests)

    def tool_not_used_debug(bot: Bot):
        print(f'{bot.name}: {bot.conversation.content}')
        return not bool(bot.tool_handler.requests)

    def said_DONE(bot: Bot):
        return 'DONE' in bot.conversation.content

    def said_DONE_debug(bot: Bot):
        print(f'{bot.name}: {bot.conversation.content}')
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


def recombine(bot: Bot, responses: List[Response], nodes: List[ResponseNode
    ], recombinator_function: RecombinatorFunction) ->Tuple[Response,
    ResponseNode]:
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
    start_point = bot.conversation
    response, node = recombinator_function(responses, nodes)
    node.parent = start_point
    start_point.replies[-1] = node
    bot.conversation = node
    return response, node


def tree_of_thought(bot: Bot, prompts: List[Prompt], recombinator_function:
    RecombinatorFunction) ->Tuple[Response, ResponseNode]:
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


def prompt_while(bot: Bot, first_prompt: Prompt, continue_prompt: Prompt=
    'ok', stop_condition: Condition=conditions.tool_not_used) ->Tuple[List[
    Response], List[ResponseNode]]:
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


def prompt_for(bot: Bot, items: List[Any], dynamic_prompt: DynamicPrompt,
    should_branch: bool=False) ->Tuple[List[Response], List[ResponseNode]]:
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


def chain_while(bot: Bot, prompt_list: List[Prompt], stop_condition:
    Condition=conditions.tool_not_used, continue_prompt: str='ok') ->Tuple[
    List[Response], List[ResponseNode]]:
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


def branch_while(bot: Bot, prompt_list: List[Prompt], stop_condition:
    Condition=conditions.tool_not_used, continue_prompt: str='ok') ->Tuple[
    List[Response], List[ResponseNode]]:
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


def par_branch(bot: Bot, prompts: List[Prompt]) ->Tuple[List[Response],
    List[ResponseNode]]:
    """
    Creates multiple conversation branches from the current node in parallel.
    Each branch starts from the current conversation state and processes independently.

    Args:
    bot (Bot): The bot to use for the responses.
    prompts (List[Prompt]): A list of prompts to send to the bot.

    Returns:
    Tuple[List[Response], List[ResponseNode]]: A tuple containing a list of response
    strings and a list of corresponding ConversationNodes. If an error occurs in any
    branch, 'None' is sent for both the response and node for that branch.
    """
    original_autosave = bot.autosave
    original_conversation = bot.conversation
    bot.autosave = False
    temp_file = 'temp_bot.bot'
    bot.save(temp_file)
    responses = [None] * len(prompts)
    nodes = [None] * len(prompts)

    def process_prompt(index: int, prompt: str) ->Tuple[int, Response,
        ResponseNode]:
        try:
            branch_bot = Bot.load(temp_file)
            branch_bot.autosave = False
            response = branch_bot.respond(prompt)
            new_node = branch_bot.conversation
            new_node.parent = original_conversation
            original_conversation.replies.append(new_node)
            return index, response, new_node
        except:
            return index, None, None
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_prompt, i, prompt) for i, prompt in
            enumerate(prompts)]
        for future in as_completed(futures):
            idx, response, node = future.result()
            responses[idx] = response
            nodes[idx] = node
    bot.autosave = original_autosave
    try:
        os.remove(temp_file)
    except:
        pass
    return responses, nodes


def par_branch_while(bot: Bot, prompt_list: List[Prompt], stop_condition:
    Condition=conditions.tool_not_used, continue_prompt: str='ok') ->Tuple[
    List[Response], List[ResponseNode]]:
    """
    Creates parallel branches for a list of prompts, continuing each branch until its
    stop condition is met. Each branch starts from the current conversation state and
    develops independently. Branches are processed in parallel.

    Args:
    bot (Bot): The bot to use for the responses.
    prompt_list (List[Prompt]): List of prompts to create branches with
    stop_condition (Condition): Function that takes a Bot and returns True when ready
                              to move to next prompt
    continue_prompt (str): Prompt to send when stop_condition is False

    Returns:
    Tuple[List[Response], List[ResponseNode]]: Lists of final responses and their
    corresponding nodes from each branch. If an error occurs on a branch, the response
    and node returned are 'None'.
    """
    original_autosave = bot.autosave
    original_conversation = bot.conversation
    bot.autosave = False
    temp_file = 'temp_bot.bot'
    bot.save(temp_file)
    responses = [None] * len(prompt_list)
    nodes = [None] * len(prompt_list)

    def process_branch(index: int, initial_prompt: str) ->Tuple[int,
        Response, ResponseNode]:
        try:
            branch_bot = Bot.load(temp_file)
            branch_bot.autosave = False
            first_response = branch_bot.respond(initial_prompt)
            first_node = branch_bot.conversation
            response = first_response
            while not stop_condition(branch_bot):
                response = branch_bot.respond(continue_prompt)
            first_node.parent = original_conversation
            original_conversation.replies.append(first_node)
            return index, response, first_node
        except Exception as e:
            return index, None, None
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_branch, i, prompt) for i, prompt in
            enumerate(prompt_list)]
        for future in as_completed(futures):
            idx, response, node = future.result()
            responses[idx] = response
            nodes[idx] = node
    bot.autosave = original_autosave
    try:
        os.remove(temp_file)
    except:
        pass
    return responses, nodes


def par_dispatch(bot_list: List[Bot], functional_prompt: Callable, **kwargs
    ) ->List[Tuple[Response, ResponseNode]]:
    """
    Dispatches each bot in bot_list through functional_prompt(bot, **kwargs) in parallel.

    Args:
        bot_list (List[Bot]): List of bots to process in parallel
        functional_prompt (Callable): A function that takes a bot and kwargs as arguments
        **kwargs: Additional arguments to pass to the functional_prompt

    Returns:
        List[ 
            Tuple[
                    Optional[List[Response] Respsonse], 
                    Optional[List[ResponseNode] RespsonseNode]
                ]
            ]
        
        I.e. [(responses, nodes), (responses, nodes), (responses, nodes), ...]
                
        List of results from each bot's functional prompt execution, in the same form 
        as that functional prompt (list or node). If an error occurs for any bot, that
        position will contain (None, None).
    """
    results = [None] * len(bot_list)

    def process_bot(index: int, bot: Bot) ->Tuple[int, Tuple[Response,ResponseNode]]:
        try:
            result = functional_prompt(bot, **kwargs)
            return index, result
        except Exception as e:
            return index, (None, None)
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_bot, i, bot) for i, bot in
            enumerate(bot_list)]
        for future in as_completed(futures):
            idx, result = future.result()
            results[idx] = result
    return results
