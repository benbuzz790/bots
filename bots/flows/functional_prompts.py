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
RecombinatorFunction = Callable[[List[Response], 
                                 List[ResponseNode] ], 
                                 Tuple[Response, ResponseNode]]

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
        response = bot.respond(prompt)
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
        response = bot.respond(prompt)
        responses.append(response)
        nodes.append(bot.conversation)
        bot.conversation = original_conversation
    return responses, nodes

def basic(bot: Bot, prompt: Prompt) -> Tuple[Response, ResponseNode]:
    response = bot.respond(prompt)
    node = bot.conversation
    return response, node

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
                 continue_prompt: Prompt, 
                 stop_condition: Condition
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
    response = bot.respond(first_prompt)
    responses.append(response)
    nodes.append(bot.conversation)
    while not stop_condition(bot):
        response = bot.respond(continue_prompt)
        responses.append(response)
        nodes.append(bot.conversation)
    return responses, nodes


def prompt_for( bot: Bot, 
                items: List[Any], 
                dynamic_prompt: DynamicPrompt,
                should_branch: bool=False
                ) -> Tuple[List[Response], List[ResponseNode]]:
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
                stop_condition: Condition,
                continue_prompt: str
                ) -> None:
    """
    Sends a series of messages. Moves to next message when stop_condition(bot) is met.
    Sends continue_prompt if condition is not met.
    Clears tool handler.
    """
    for p in prompt_list:
        response = bot.respond(p)
        while not stop_condition(bot):
            response = bot.respond(continue_prompt)
    bot.tool_handler.clear()

def retry_until(bot: Bot, 
                dynamic_prompt: DynamicPrompt,
                stop_condition: Condition, 
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
        if stop_condition(bot):
            return response, bot.conversation
    return response, bot.conversation


class conditions:
    def tool_used(bot:Bot):
        if bot.conversation.tool_calls:
            return True
        else:
            return False
    
    def tool_not_used(bot:Bot):
        return not conditions.tool_used(bot)

    def said_DONE(bot:Bot):
        return "DONE" in bot.conversation.content

