from typing import List, Callable, Any, Tuple, Union
from src.base import Bot
from src.base import ConversationNode

"""Custom typing for clarity (hopefully)"""
Prompt = str
Response = str
PromptNode = ConversationNode
ResponseNode = ConversationNode
StopCondition = Callable[[Response], bool]
DynamicPrompt = Callable[[Any], Prompt]
RecombinatorFunction = Callable[[List[Response], List[ResponseNode]], Tuple
    [Response, ResponseNode]]

def chain(bot: Bot, 
          prompts: List[Prompt]
         ) ->Tuple[List[Response], List[ResponseNode]]:
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
        response = bot.respond(prompt, auto=True)
        responses.append(response)
        nodes.append(bot.conversation)
    return responses, nodes


def branch(bot: Bot, 
           prompts: List[Prompt]
          ) -> Tuple[List[Response], List[ResponseNode]]:
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
        response = bot.respond(prompt, auto=True)
        responses.append(response)
        nodes.append(bot.conversation)
    bot.conversation = original_conversation
    return responses, nodes


def recombine(bot: Bot, 
              responses: List[Response], 
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
                    recombinator_function:RecombinatorFunction
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


def prompt_while(bot: Bot, prompt: Prompt, stop_condition: StopCondition
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
    while True:
        response = bot.respond(prompt, auto=True)
        responses.append(response)
        nodes.append(bot.conversation)
        if stop_condition(response):
            break
    return responses, nodes


def prompt_for(bot: Bot, items: List[Any], dynamic_prompt: DynamicPrompt,
    branch: bool=False) ->Tuple[List[Response], List[ResponseNode]]:
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
            response = bot.respond(prompt, auto=True)
            responses.append(response)
            nodes.append(bot.conversation)
        return responses, nodes


def sequential_process( bot: Bot, 
                        task: Prompt,
                        list_length: int, 
                        ) ->Tuple[Response, ResponseNode]:
    """
    Generates a list of subtasks based on the task, elaborates on each subtask, and then executes each elaboration.
    Similar to chain of thought, but more token efficient in theory.

    Args:
    bot (Bot): The bot to use to create the instructions list and execute instructions.
    task (Prompt): The initial prompt requesting a task to be completed.
    list_length (int): The expected length of the list.

    Returns:
    Tuple[List[Response], List[ResponseNode]]: A tuple containing the final response and node of the final execution prompt
    """

    list_prompt = f"""Hello LLM assistant! You're being used in an automated 
        system to complete a multi-step task. Please start by making a list of 
        steps to required to complete the task. The list should be {list_length}
        steps long. Do not start working yet, just break down the task. 
        The task is as follows:\n\n{task}"""

    bot.respond(list_prompt)

    elaboration_prompts = [f"""For top level item {i + 1} in the list you just 
        provided, give brief details and requirements in the form of instructions. 
        Please reply with only the instructions as though you are telling someone 
        to do the task and say nothing else. Mention specific tools (among those 
        available to you) in the instructions.""" for i in range(list_length)
    ]

    branch_node = bot.conversation
    elaborations, _ = branch(bot, elaboration_prompts)

    execution_prompts = [ f"""Please do the following subtask per these 
        detailed instructions. A few notes: 1. the previous tasks have been completed
        in a different conversation branch. 2. the next tasks will be completed in
        another branch, so please do not move forward past these instructions: 
        \n\n{elab}""" for elab in elaborations
    ]

    for eprompt in execution_prompts:
        bot.conversation = branch_node
        bot.respond(eprompt)
        p = "Continue to work autonomously until you complete the subtask. When you're done, say 'DONE'"
        stop_condition = lambda x: "DONE" in x
        r, rnode = prompt_while(bot, p, stop_condition)

    return r, rnode


def retry_until(bot: Bot, 
                dynamic_prompt: Union[Prompt, Callable[[], Prompt]],
                condition: Callable[[Response], bool], 
                max_attempts: int=8
                ) ->Tuple[Response, ResponseNode]:
    """
    Repeatedly branches and retries a prompt until a condition is met or max attempts are reached.

    Args:
    bot (Bot): The bot to use for the responses.
    prompt (Union[Prompt, Callable[[], Prompt]]): Either a static prompt string or a function that returns a prompt.
    condition (Callable[[Response], bool]): A function that takes a Response and returns True if the condition is met.
    max_attempts (int): The maximum number of attempts before giving up. Defaults to 8.

    Returns:
    Tuple[Response, ResponseNode]: A tuple containing the successful response string and its corresponding ConversationNode.
    If max attempts are reached without meeting the condition, returns the last attempt.
    """
    original_conversation = bot.conversation
    for _ in range(max_attempts):
        bot.conversation = original_conversation
        current_prompt = dynamic_prompt()
        response = bot.respond(current_prompt, auto=True)
        if condition(response):
            return response, bot.conversation
    return response, bot.conversation
