from typing import List, Callable, Any
from src.base import Bot
from src.base import ConversationNode

# Not sure if auto_tool should be true, false, or optional yet

"""Custom typing for clarity (hopefully)"""
Prompt = str
Response = str
PromptNode = ConversationNode
ResponseNode = ConversationNode
StopCondition = Callable[[Response], bool]
DynamicPrompt = Callable[[Any], Prompt]
RecombinatorFunction = Callable[[List[ResponseNode]], (Response, ResponseNode)]

def chain(bot: Bot, prompts: List[Prompt]) ->List[ResponseNode]:
    """
    Implements a chain of thought by sending a series of prompts to the bot.

    Args:
    bot (Bot): The bot to use for the responses.
    prompts (List[Prompt]): A list of prompts to send to the bot in order.

    Returns:
    List[ResponseNode]: A list of tuples, each containing a response string and its corresponding ConversationNode.
    """
    responses = []
    for prompt in prompts:
        response = bot.respond(prompt, tool_auto=True)
        responses.append((response, bot.conversation))
    return responses

def branch(bot: Bot, prompts: List[Prompt]) ->List[ResponseNode]:
    """
    Creates multiple conversation branches from the current node.

    Args:
    bot (Bot): The bot to use for the responses.
    prompts (List[Prompt]): A list of prompts to send to the bot.

    Returns:
    List[ResponseNode]: A list of tuples, each containing a response string and its corresponding ConversationNode.
    """
    original_conversation = bot.conversation
    branches = []
    for prompt in prompts:
        bot.conversation = original_conversation
        response = bot.respond(prompt, tool_auto=True)
        branches.append((response, bot.conversation))
    bot.conversation = original_conversation
    return branches


def recombine(bot: Bot, response_nodes: List[ResponseNode],
    recombinator_function: RecombinatorFunction) ->ResponseNode:
    """
    Recombines multiple conversation branches using a provided function.

    Args:
    bot (Bot): The bot to use for the responses. (Kept for potential future use)
    response_nodes (List[ResponseNode]): A list of tuples, each containing a response string and its corresponding ConversationNode.
    recombinator_function (RecombinatorFunction): A function that takes a list of ResponseNodes and returns a single ResponseNode.

    Returns:
    ResponseNode: A tuple containing the recombined response string and its corresponding ConversationNode.
    """
    recombined_response, recombined_node = recombinator_function(response_nodes
        )
    bot.conversation = recombined_node
    return recombined_response, recombined_node


def tree_of_thought(bot: Bot, prompts: List[Prompt], recombinator_function:
    RecombinatorFunction) ->ResponseNode:
    """
    Implements a tree of thought approach by branching into multiple conversation paths and then recombining the results.

    Args:
    bot (Bot): The bot to use for the responses.
    prompts (List[Prompt]): A list of prompts to create branches with.
    recombinator_function (RecombinatorFunction): A function that takes a list of ResponseNodes and returns a single ResponseNode.

    Returns:
    ResponseNode: A tuple containing the final recombined response string and its corresponding ConversationNode.
    """
    branches = branch(bot, prompts)
    final_response = recombine(bot, branches, recombinator_function)
    return final_response


def prompt_while(bot: Bot, prompt: Prompt, stop_condition: StopCondition
    ) ->List[ResponseNode]:
    """
    Repeatedly prompts the bot until a stop condition is met.

    Args:
    bot (Bot): The bot to use for the responses.
    prompt (Prompt): The prompt to repeatedly send to the bot.
    stop_condition (StopCondition): A function that takes a ResponseNode and returns True if the loop should stop.

    Returns:
    List[ResponseNode]: A list of tuples, each containing a response string and its corresponding ConversationNode.
    """
    responses = []
    while True:
        response = bot.respond(prompt, tool_auto=True)
        response_node = response, bot.conversation
        responses.append(response_node)
        if stop_condition(response_node):
            break
    return responses


def prompt_for(bot: Bot, items: List[Any], dynamic_prompt: DynamicPrompt,
    branch: bool=False) ->List[ResponseNode]:
    """
    Generates prompts for a list of items and gets responses from the bot.

    Args:
    bot (Bot): The bot to use for the responses.
    items (List[Any]): A list of items to generate prompts for.
    dynamic_prompt (DynamicPrompt): A function that takes an item and returns a prompt.
    branch (bool): If True, creates separate conversation branches for each item. 
                   If False (default), processes items sequentially in the same conversation.
    
    Returns:
    List[ResponseNode]: A list of tuples, each containing a response string and its corresponding ConversationNode.
    """
    prompts = [dynamic_prompt(item) for item in items]
    if branch:
        return branch(bot, prompts)
    else:
        responses = []
        for prompt in prompts:
            response = bot.respond(prompt, tool_auto=True)
            responses.append((response, bot.conversation))
        return responses

def sequential_process(bot: Bot, initial_prompt: Prompt, list_length: int
    ) ->List[ResponseNode]:
    """
    Implements a sequential process that generates a list, elaborates on each item, and then executes each elaboration.

    Args:
    bot (Bot): The bot to use for the responses.
    initial_prompt (Prompt): The initial prompt requesting a list of a specific length with numbered items.
    list_length (int): The expected length of the list.

    Returns:
    List[ResponseNode]: A list of tuples, each containing a response string and its corresponding ConversationNode.
    """
    bot.respond(initial_prompt)
    branch_point = bot.conversation
    index = range(list_length)
    elaboration_prompts = []
    for i in index:
        elaboration_prompts.append(f'For top level item {i} in the list you just provided,
        give brief details and requirements in the form of an instruction.')
    elaborations = branch(bot, [elaboration_prompts])
    execution_prompts = [f"Thanks, let's handle this step by step. Do just the following: {elab[0]}" for elab in elaborations]
    bot.conversation = branch_point
    final_responses = chain(bot, execution_prompts)
    return final_responses
