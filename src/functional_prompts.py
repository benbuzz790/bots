from typing import List, Callable, Any, Tuple
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
RecombinatorFunction = Callable[[List[Response], List[ResponseNode]], Tuple[Response, ResponseNode]]

def chain(bot: Bot, prompts: List[Prompt]) -> Tuple[List[Response], List[ResponseNode]]:
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
        response = bot.respond(prompt, tool_auto=True)
        responses.append(response)
        nodes.append(bot.conversation)
    return responses, nodes

def branch(bot: Bot, prompts: List[Prompt]) -> Tuple[List[Response], List[ResponseNode]]:
    """
    Creates multiple conversation branches from the current node.

    Args:
    bot (Bot): The bot to use for the responses.
    prompts (List[Prompt]): A list of prompts to send to the bot.

    Returns:
    Tuple[List[Response], List[ResponseNode]]: A tuple containing a list of response strings and a list of corresponding ConversationNodes.
    """
    original_conversation = bot.conversation
    responses = []
    nodes = []
    for prompt in prompts:
        bot.conversation = original_conversation
        response = bot.respond(prompt, tool_auto=True)
        responses.append(response)
        nodes.append(bot.conversation)
    bot.conversation = original_conversation
    return responses, nodes

def recombine(bot: Bot, responses: List[Response], nodes: List[ResponseNode],
    recombinator_function: RecombinatorFunction) -> Tuple[Response, ResponseNode]:
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
    recombined_response, recombined_node = recombinator_function(responses, nodes)
    bot.conversation = recombined_node
    return recombined_response, recombined_node

def tree_of_thought(bot: Bot, prompts: List[Prompt], recombinator_function:
    RecombinatorFunction) -> Tuple[Response, ResponseNode]:
    """
    Implements a tree of thought approach by branching into multiple conversation paths and then recombining the results.

    Args:
    bot (Bot): The bot to use for the responses.
    prompts (List[Prompt]): A list of prompts to create branches with.
    recombinator_function (RecombinatorFunction): A function that takes a list of Responses and a list of ResponseNodes and returns a single Response and ResponseNode.

    Returns:
    Tuple[Response, ResponseNode]: A tuple containing the final recombined response string and its corresponding ConversationNode.
    """
    responses, nodes = branch(bot, prompts)
    final_response = recombine(bot, responses, nodes, recombinator_function)
    return final_response

def prompt_while(bot: Bot, prompt: Prompt, stop_condition: StopCondition
    ) -> Tuple[List[Response], List[ResponseNode]]:
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
    while True:
        response = bot.respond(prompt, tool_auto=True)
        responses.append(response)
        nodes.append(bot.conversation)
        if stop_condition(response):
            break
    return responses, nodes

def prompt_for(bot: Bot, items: List[Any], dynamic_prompt: DynamicPrompt,
    branch: bool=False) -> Tuple[List[Response], List[ResponseNode]]:
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
    if branch:
        return branch(bot, prompts)
    else:
        responses = []
        nodes = []
        for prompt in prompts:
            response = bot.respond(prompt, tool_auto=True)
            responses.append(response)
            nodes.append(bot.conversation)
        return responses, nodes

def sequential_process(instruct_bot: Bot, initial_prompt: Prompt, 
                       list_length: int, executor_bot: Bot = None,
                       ) -> Tuple[List[Response], List[ResponseNode]]:
    """
    Implements a sequential process that generates a list, elaborates on each item, and then executes each elaboration.

    Args:
    instruct_bot (Bot): The bot to use to create the instructions list.
    executor_bot (Bot): The bot to use to execute the instructions.
    initial_prompt (Prompt): The initial prompt requesting a list of a specific length with numbered items.
    list_length (int): The expected length of the list.

    Returns:
    Tuple[List[Response], List[ResponseNode]]: A tuple containing a list of response strings and a list of corresponding ConversationNodes.
    """
    instruct_bot.respond(initial_prompt)
    branch_point = instruct_bot.conversation
    index = range(list_length)
    elaboration_prompts = []
    for i in index:
        elaboration_prompts.append(f'For top level item {i+1} in the list you just provided,\
        give brief details and requirements in the form of an instruction.')
    elaborations, _ = branch(instruct_bot, elaboration_prompts)
    if executor_bot is None:
        instruct_bot.conversation = branch_point
        executor_bot = instruct_bot
    execution_prompts = [f"Please do the following task: \n\n {elab}" for elab in elaborations]
    final_responses, final_nodes = chain(executor_bot, execution_prompts)
    return final_responses, final_nodes