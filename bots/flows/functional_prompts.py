"""Functional patterns for structured bot interactions and complex reasoning.

This module provides a collection of higher-level functions for orchestrating
interactions in common patterns like chains, branches, and trees. These patterns
enable sophisticated reasoning approaches while maintaining clear structure and
reproducibility.

Key Features:
- Sequential Processing:
    - chain(): Execute prompts in sequence
    - chain_while(): Chain with iteration until condition met
    - prompt_while(): Single prompt with iteration

- Parallel Exploration:
    - branch(): Explore multiple paths independently
    - branch_while(): Branch with iteration
    - par_branch(): Parallel version of branch()
    - par_branch_while(): Parallel version of branch_while()

- Advanced Reasoning:
    - tree_of_thought(): Branch, explore, then synthesize
    - prompt_for(): Dynamic prompts from data
    - par_dispatch(): Compare multiple bots

Common Parameters:
- bot (Bot): The bot instance to use
- prompts (List[Prompt]): List of prompts to process
- stop_condition (Condition): Function determining when to stop iteration

Common Return Values:
- Response: String containing bot's response
- ResponseNode: ConversationNode containing response and context

Example:
    >>> responses, nodes = chain(bot, [
    ...     "First, analyze the problem...",
    ...     "Now, propose solutions...",
    ...     "Finally, implement the best solution..."
    ... ])
"""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, List, Optional, Tuple, Union

from bots.foundation.base import Bot, ConversationNode

# Type Aliases
Prompt = str  # A string containing a prompt to be sent to the bot
Response = str  # A string containing a bot's response
PromptNode = ConversationNode  # A conversation node containing a prompt
ResponseNode = ConversationNode  # A conversation node containing a response
Condition = Callable[[Bot], bool]  # Function that evaluates bot state
DynamicPrompt = Callable[[Any], Prompt]  # Function that generates prompts

RecombinatorFunction = Callable[
    [List[Response], List[ResponseNode]], Tuple[Response, ResponseNode]
]  # A function that combines multiple responses into a single response

FunctionalPrompt = Callable[
    [Bot, Any], Union[Tuple[Response, ResponseNode], Tuple[List[Response], List[ResponseNode]]]
]  # A function that acts on a Bot and returns a response or set of responses in the form of a tuple.


class conditions:
    """Predefined condition functions for controlling bot iteration.

    This class provides a collection of static methods that can be used as
    stop conditions in functions like prompt_while() and chain_while(). Each
    condition evaluates some aspect of the bot's state to determine whether
    iteration should continue.

    Attributes:
        No instance attributes - all methods are static

    Common Usage:
        >>> # Continue until bot stops using tools
        >>> prompt_while(bot, prompt, stop_condition=conditions.tool_not_used)
        >>>
        >>> # Continue until bot says "DONE"
        >>> chain_while(bot, prompts, stop_condition=conditions.said_DONE)

    Note:
        Each condition function takes a Bot instance and returns a boolean.
        True typically indicates iteration should stop.
    """

    @staticmethod
    def said_READY(bot: Bot) -> bool:
        """Check if the bot's response contains the word 'READY'.

        Use when you need to continue prompting until the bot indicates readiness.

        Args:
            bot (Bot): The bot to check

        Returns:
            bool: True if the response contains 'READY', False otherwise
        """
        return "READY" in bot.conversation.content

    @staticmethod
    def five_iterations(bot: Bot):
        """Create a condition that stops after five iterations.

        Use when you want to prevent infinite loops by setting an iteration limit.
        Note: This requires external counter management.

        Args:
            max_count (int): Maximum number of iterations allowed

        Returns:
            Callable[[Bot], bool]: A condition function with iteration counting
        """
        iteration_count = {"count": 0}

        def condition(bot: Bot) -> bool:
            iteration_count["count"] += 1
            return iteration_count["count"] >= 5

        return condition

    @staticmethod
    def no_new_tools_used(bot: Bot) -> bool:
        """Check if the bot used the same tools as in the previous response.

        Use when you want to stop when the bot stops exploring new tool options.

        Args:
            bot (Bot): The bot to check

        Returns:
            bool: True if no new tools were used compared to previous iteration
        """
        if not hasattr(bot, "_previous_tools"):
            # First iteration - store current tools
            bot._previous_tools = set()
            if bot.tool_handler.requests:
                for request in bot.tool_handler.requests:
                    tool_name, _ = bot.tool_handler.tool_name_and_input(request)
                    bot._previous_tools.add(tool_name)
            return False

        # Get current tools
        current_tools = set()
        if bot.tool_handler.requests:
            for request in bot.tool_handler.requests:
                tool_name, _ = bot.tool_handler.tool_name_and_input(request)
                current_tools.add(tool_name)

        # Check if any new tools were used
        new_tools = current_tools - bot._previous_tools
        bot._previous_tools = current_tools

        return len(new_tools) == 0 and len(current_tools) > 0

    @staticmethod
    def error_in_response(bot: Bot) -> bool:
        """Check if the bot's response contains error indicators.

        Use when you want to stop iteration if the bot encounters errors.

        Args:
            bot (Bot): The bot to check

        Returns:
            bool: True if the response contains error indicators
        """
        content = bot.conversation.content.lower()
        error_indicators = ["error", "failed", "exception", "traceback", "syntax"]
        return any(indicator in content for indicator in error_indicators)

    def tool_used(bot: Bot) -> bool:
        """Check if the bot has used any tools in its last response.

        Use when you need to continue prompting until the bot uses a tool.

        Args:
            bot (Bot): The bot to check

        Returns:
            bool: True if the bot has used any tools, False otherwise
        """
        return bool(bot.tool_handler.requests)

    @staticmethod
    def tool_not_used(bot: Bot) -> bool:
        """Check if the bot has not used any tools in its last response.

        Use when you need to continue prompting until the bot stops using tools.

        Args:
            bot (Bot): The bot to check

        Returns:
            bool: True if the bot has not used any tools, False otherwise
        """
        return not bool(bot.tool_handler.requests)

    @staticmethod
    def said_DONE(bot: Bot) -> bool:
        """Check if the bot's response contains the word 'DONE'.

        Use when you need to continue prompting until the bot indicates completion.

        Args:
            bot (Bot): The bot to check

        Returns:
            bool: True if the response contains 'DONE', False otherwise
        """
        return "DONE" in bot.conversation.content


def single_prompt(bot: Bot, prompt: Prompt) -> Tuple[Response, ResponseNode]:
    """Execute a single prompt and return both response and conversation state.

    Use when you need:
    - The simplest possible bot interaction
    - To capture both response and conversation state
    - A building block for custom interaction patterns
    - To understand the fundamental bot interaction model

    This function serves as:
    1. A demonstration of the basic bot interaction pattern
    2. A template for more complex functional patterns
    3. A utility for simple, one-shot interactions
    4. A way to understand conversation node handling

    Args:
        bot (Bot): The bot to interact with. The bot's current conversation
            state is preserved and updated with this interaction
        prompt (Prompt): The prompt to send to the bot. Should be a clear,
            self-contained instruction or question

    Returns:
        Tuple[Response, ResponseNode]: A tuple containing:
            - response (str): The bot's response text
            - node (ConversationNode): Conversation node containing:
                - The response
                - The prompt that generated it
                - Links to parent/child nodes
                - Associated metadata

    Examples:
        >>> # Simple question and answer
        >>> response, node = basic(bot,
        ...     "What is the time complexity of quicksort?"
        ... )
        >>> print(response)
        >>>
        >>> # Tool usage
        >>> response, node = basic(bot,
        ...     "Review the code in main.py"
        ... )
        >>> print(node.tool_calls)  # See what tools were used
        >>>
        >>> # Access conversation context
        >>> response, node = basic(bot, "Analyze this.")
        >>> print(node.parent.content)  # See previous context

    Implementation Notes:
        - Maintains conversation tree structure
        - Updates bot's current conversation state
        - Preserves tool usage information
        - Serves as foundation for other patterns
    """
    response = bot.respond(prompt)
    node = bot.conversation
    return (response, node)


def chain(
    bot: Bot, prompt_list: List[Prompt], callback: Optional[Callable[[List[Response], List[ResponseNode]], None]] = None
) -> Tuple[List[Response], List[ResponseNode]]:
    """Execute a sequence of prompts that build on each other.

    Use when you need to:
    - Guide a bot through a structured sequence of steps
    - Build up complex reasoning through progressive stages
    - Maintain context between related prompts
    - Create a linear flow of thought or analysis

    This is one of the most fundamental patterns, providing a way to break down
    complex tasks into ordered steps where each step builds on the context and
    understanding developed in previous steps.

    Args:
        bot (Bot): The bot to interact with. The bot maintains conversation
            context throughout the chain, allowing each step to reference
            and build upon previous responses
        prompt_list (List[Prompt]): Ordered list of prompts to process sequentially.
            For best results:
            - Make prompts build progressively
            - Reference previous steps when needed
            - Keep a clear logical flow
            - Use explicit transitions between steps
        callback (Optional[Callable[[List[Response], List[ResponseNode]], None]]):
            A function (with arguments list[respose], list[node]) which is called
            after each response from the bot.

    Returns:
    Tuple[List[Response], List[ResponseNode]]: A tuple containing a list of response strings
        and a list of corresponding ConversationNodes.
    """
    responses = []
    nodes = []
    for prompt in prompt_list:
        response = bot.respond(prompt)
        responses.append(response)
        nodes.append(bot.conversation)
        if callback:
            try:
                callback(responses, nodes)
            except Exception as e:
                pass  # Don't let callback errors break the main function
    return responses, nodes


def branch(
    bot: Bot, prompt_list: List[Prompt], callback: Optional[Callable[[List[Response], List[ResponseNode]], None]] = None
) -> Tuple[List[Response], List[ResponseNode]]:
    """Create multiple independent conversation paths from the current state.

    Use when you need to:
    - Explore multiple perspectives simultaneously
    - Analyze different aspects of a problem independently
    - Compare different approaches without cross-influence
    - Generate diverse solutions or viewpoints

    This is a fundamental pattern for parallel thinking that allows exploration
    of multiple lines of thought without letting them influence each other.
    Each branch starts from the same context but develops independently.

    Args:
        bot (Bot): The bot to interact with. The bot's current conversation
            state is used as the starting point for all branches, but each
            branch gets its own independent context
        prompts (List[Prompt]): List of prompts, each creating a separate
            conversation branch. For effective branching:
            - Make prompts independent of each other
            - Focus each prompt on a distinct aspect
            - Be explicit about the perspective or approach
            - Maintain consistent depth across branches
        callback (Optional[Callable[[List[Response], List[ResponseNode]], None]]):
            A function (with arguments list[respose], list[node]) which is called
            after each response from the bot.

    Returns:
        Tuple[List[Response], List[ResponseNode]]: A tuple containing:
            - responses (List[Optional[str]]): List of responses, one per
              branch. Failed branches contain None
            - nodes (List[Optional[ConversationNode]]): List of conversation
              nodes containing responses and their independent contexts.
              Failed branches contain None

    Examples:
        >>> # Multi-perspective analysis
        >>> responses, nodes = branch(bot, [
        ...     "Analyze this code from a security perspective...",
        ...     "Analyze this code from a performance perspective...",
        ...     "Analyze this code from a maintainability perspective...",
        ...     "Analyze this code from a scalability perspective..."
        ... ])
        >>>
        >>> # Solution exploration
        >>> responses, nodes = branch(bot, [
        ...     "Solve this using a recursive approach...",
        ...     "Solve this using an iterative approach...",
        ...     "Solve this using a dynamic programming approach...",
        ...     "Solve this using a divide-and-conquer approach..."
        ... ])
        >>>
        >>> # Stakeholder perspectives
        >>> responses, nodes = branch(bot, [
        ...     "Evaluate this feature from a user's perspective...",
        ...     "Evaluate this feature from a developer's perspective...",
        ...     "Evaluate this feature from a business perspective...",
        ...     "Evaluate this feature from a maintenance perspective..."
        ... ])

    Implementation Notes:
        - Creates independent context for each branch
        - Handles branch failures gracefully
        - Maintains tree structure for conversation history
        - Conversation is left at final prompt's response.
    """
    original_conversation = bot.conversation
    responses = []
    nodes = []
    for prompt in prompt_list:
        bot.conversation = original_conversation
        try:
            response = bot.respond(prompt)
            node = bot.conversation
            if callback:
                try:
                    callback([response], [node])
                except Exception as e:
                    pass  # Don't let callback errors break the main function
        except Exception as e:
            response = None
            node = None
        finally:
            responses.append(response)
            nodes.append(node)
    return responses, nodes


def recombine(
    bot: Bot, responses: List[Response], nodes: List[ResponseNode], recombinator_function: RecombinatorFunction, **kwargs
) -> Tuple[Response, ResponseNode]:
    """Synthesize multiple conversation branches into a unified conclusion.

    Use when you need to:
    - Combine insights from parallel explorations
    - Synthesize multiple perspectives into one view
    - Create a summary from multiple analyses
    - Resolve potentially conflicting viewpoints

    This function is a key component in tree-based reasoning patterns,
    typically used after branch() or as part of tree_of_thought() to
    combine parallel thinking paths into a coherent conclusion.

    Args:
        bot (Bot): The bot instance. Currently maintained for future
            extensions that might involve bot interaction during
            recombination
        responses (List[Response]): List of response strings from parallel
            branches. Each response typically represents:
            - A different perspective on the problem
            - Analysis of a specific aspect
            - Results from a particular approach
        nodes (List[ResponseNode]): List of conversation nodes containing
            the responses and their context. These nodes maintain the
            full conversation history of each branch
        recombinator_function (RecombinatorFunction): Custom function that
            implements the synthesis logic. Must have signature:
            (List[Response], List[ResponseNode]) -> Tuple[Response, ResponseNode]

            The function should:
            - Process all input responses
            - Consider their relationships
            - Resolve any conflicts
            - Produce a coherent synthesis

    Returns:
        Tuple[Response, ResponseNode]: A tuple containing:
            - response (str): The synthesized response combining insights
              from all input branches
            - node (ConversationNode): A new conversation node containing
              the combined response and linking to all source branches

    Examples:
        >>> # Simple concatenation with formatting
        >>> def basic_combine(responses, nodes):
        ...     combined = "\\n".join(f"- {r}" for r in responses)
        ...     return f"Combined Insights:\\n{combined}", nodes[0]
        ...
        >>> final_response, final_node = recombine(
        ...     bot, branch_responses, branch_nodes, basic_combine
        ... )
        >>>
        >>> # Structured synthesis with weighting
        >>> def weighted_synthesis(responses, nodes):
        ...     # Weight responses by confidence markers
        ...     weighted = []
        ...     for r in responses:
        ...         confidence = r.count("definitely") + r.count("clearly")
        ...         weighted.append((confidence, r))
        ...
        ...     # Sort by confidence and format
        ...     sorted_insights = [r for _, r in sorted(weighted, reverse=True)]
        ...     synthesis = "Synthesis (by confidence):\\n" + "\\n".join(
        ...         f"{i+1}. {r}" for i, r in enumerate(sorted_insights)
        ...     )
        ...     return synthesis, nodes[0]
        ...
        >>> final_response, final_node = recombine(
        ...     bot, branch_responses, branch_nodes, weighted_synthesis
        ... )

    Implementation Notes:
        - Maintains conversation tree structure
        - Links final node to all source branches
        - Preserves full conversation history
        - Updates bot's current conversation state
    """
    start_point = bot.conversation
    response, node = recombinator_function(responses, nodes, **kwargs)
    node.parent = start_point
    start_point.replies[-1] = node
    bot.conversation = node
    return response, node


def tree_of_thought(
    bot: Bot,
    prompts: List[Prompt],
    recombinator_function: RecombinatorFunction,
    callback: Optional[Callable[[Response, ResponseNode], None]] = None,
) -> Tuple[Response, ResponseNode]:
    """Implement tree-of-thought reasoning for complex problem-solving.

    Use when you need the bot to:
    - Break down complex problems into multiple perspectives
    - Explore different aspects of a problem in parallel
    - Synthesize multiple lines of thinking into a coherent solution
    - Make decisions that require considering multiple factors

    This function implements the tree-of-thought reasoning pattern in three phases:
    1. Branch: Create parallel conversation paths for different aspects
    2. Explore: Process each branch independently
    3. Synthesize: Combine insights from all branches into a final response

    Args:
        bot (Bot): The bot to interact with
        prompts (List[Prompt]): List of prompts that define different thinking
            paths. Each prompt should focus on a distinct aspect or approach
            to the problem. For best results, make prompts:
            - Independent of each other
            - Focused on specific aspects
            - Clear about their perspective
        recombinator_function (RecombinatorFunction): Function that synthesizes
            multiple responses into a final conclusion. Must have signature:
            (List[Response], List[ResponseNode]) -> Tuple[Response, ResponseNode]
            The function should:
            - Consider all responses
            - Identify key insights
            - Resolve conflicts
            - Create a coherent synthesis
       callback (Optional[Callable[[Response, ResponseNode], None]]):
           A function called after each branch response with the individual
            after each response from the bot.

    Returns:
        Tuple[Response, ResponseNode]: A tuple containing:
            - response (str): The final synthesized response combining
              insights from all branches
            - node (ConversationNode): Conversation node containing the
              final response, with links to all branch nodes

    Examples:
        >>> # Technical decision making
        >>> def combine_tech_analysis(responses, nodes):
        ...     insights = "\\n".join(f"- {r}" for r in responses)
        ...     return f"Technical Analysis:\\n{insights}", nodes[0]
        ...
        >>> response, node = tree_of_thought(
        ...     bot,
        ...     [
        ...         "Analyze performance implications...",
        ...         "Consider security aspects...",
        ...         "Evaluate maintenance impact...",
        ...         "Assess scalability concerns..."
        ...     ],
        ...     combine_tech_analysis
        ... )
        >>>
        >>> # Product feature evaluation
        >>> def synthesize_feature(responses, nodes):
        ...     aspects = dict(zip(
        ...         ["Technical", "Business", "User"],
        ...         responses
        ...     ))
        ...     return (
        ...         f"Feature Analysis:\\n" +
        ...         "\\n".join(f"{k}: {v}" for k,v in aspects.items()),
        ...         nodes[0]
        ...     )
        ...
        >>> response, node = tree_of_thought(
        ...     bot,
        ...     [
        ...         "Evaluate technical feasibility...",
        ...         "Analyze business value...",
        ...         "Assess user impact..."
        ...     ],
        ...     synthesize_feature
        ... )

    Implementation Notes:
        - Uses branch() internally for parallel exploration
        - Maintains conversation history in a tree structure
        - Final node links to all exploration branches
        - All branch contexts are preserved for reference
    """
    responses, nodes = branch(bot, prompts, callback=callback)
    final_response = recombine(bot, responses, nodes, recombinator_function)
    return final_response


def prompt_while(
    bot: Bot,
    first_prompt: Prompt,
    continue_prompt: Prompt = "ok",
    stop_condition: Condition = conditions.tool_not_used,
    callback: Optional[Callable[[List[Response], List[ResponseNode]], None]] = None,
) -> Tuple[List[Response], List[ResponseNode]]:
    """Repeatedly engage a bot in a task until completion criteria are met.

    Use when you need to:
    - Have a bot work iteratively on a task
    - Continue processing until specific criteria are met
    - Maintain context across multiple iterations
    - Handle tasks with unknown completion time

    This is a fundamental iteration pattern that enables:
    - Progressive refinement of solutions
    - Exhaustive processing of complex tasks
    - Self-guided task completion
    - Dynamic interaction flows

    Args:
        bot (Bot): The bot to interact with. Maintains conversation context
            across all iterations, allowing progressive improvement and
            refinement
        first_prompt (Prompt): The initial task prompt. Should:
            - Clearly define the task
            - Set expectations for completion
            - Include any relevant constraints
            - Specify how to indicate completion
        continue_prompt (Prompt, optional): Prompt sent for each iteration
            after the first. Defaults to 'ok'. Consider customizing to:
            - Guide the iteration process
            - Maintain task focus
            - Encourage progress
            - Request specific improvements
        stop_condition (Condition, optional): Function that determines when
            to stop iterating. Takes a Bot parameter and returns bool.
            Common patterns:
            - conditions.tool_not_used (default): Stop when bot stops using tools
            - conditions.said_DONE: Stop when bot indicates completion
            - Custom conditions for specific criteria
        callback (Optional[Callable[[List[Response], List[ResponseNode]], None]]):
            A function (with arguments list[respose], list[node]) which is called
            after each response from the bot.

    Returns:
        Tuple[List[Response], List[ResponseNode]]: A tuple containing:
            - responses (List[str]): All bot responses in order:
                - First response to initial prompt
                - All subsequent iteration responses
                - Final response meeting stop condition
            - nodes (List[ConversationNode]): Conversation nodes containing
              responses and their cumulative context

    Examples:
        >>> # Code debugging with tool usage
        >>> responses, nodes = prompt_while(
        ...     bot,
        ...     "Debug this code. Fix all errors you find.",
        ...     continue_prompt="Continue debugging. Any more issues?",
        ...     stop_condition=conditions.tool_not_used
        ... )
        >>>
        >>> # Document improvement with explicit completion
        >>> responses, nodes = prompt_while(
        ...     bot,
        ...     "Improve this text. Say DONE when perfect.",
        ...     continue_prompt="What else can be improved?",
        ...     stop_condition=conditions.said_DONE
        ... )
        >>>
        >>> # Custom completion criteria
        >>> def quality_threshold(bot: Bot) -> bool:
        ...     # Stop when response contains confidence marker
        ...     return "99% confident" in bot.conversation.content
        ...
        >>> responses, nodes = prompt_while(
        ...     bot,
        ...     "Optimize this function until confident.",
        ...     continue_prompt="Continue optimization.",
        ...     stop_condition=quality_threshold
        ... )

    Implementation Notes:
        - Maintains continuous conversation context
        - Preserves all iteration responses
        - Allows custom iteration control
        - Supports progressive refinement
        - Enables self-guided completion
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
        if callback:
            try:
                callback(responses, nodes)
            except Exception as e:
                pass  # Don't let callback errors break the main function
    return responses, nodes


def prompt_for(
    bot: Bot,
    items: List[Any],
    dynamic_prompt: DynamicPrompt,
    should_branch: bool = False,
    callback: Optional[Callable[[List[Response], List[ResponseNode]], None]] = None,
) -> Tuple[List[Response], List[ResponseNode]]:
    """Generate and process prompts dynamically from a list of items.

    Use when you need to process a collection of items where each item requires
    its own customized prompt. This function enables data-driven conversation
    flows by combining dynamic prompt generation with either sequential or
    parallel processing strategies.

    Args:
        bot (Bot): The bot to interact with
        items (List[Any]): List of items to process. Each item will be passed
            to dynamic_prompt to generate a prompt
        dynamic_prompt (DynamicPrompt): Function that generates a prompt string
            for each item. Must have signature: (item: Any) -> str
        should_branch (bool, optional): Processing strategy flag:
            - If True: Creates parallel conversation branches for each item,
              preserving independent context for each response
            - If False (default): Processes items sequentially in the same
              conversation (i.e. a chain), maintaining cumulative context
        callback (Optional[Callable[[List[Response], List[ResponseNode]], None]]):
            A function (with arguments list[respose], list[node]) which is called
            after each response from the bot.

    Returns:
        Tuple[List[Response], List[ResponseNode]]: A tuple containing:
            - responses: List[str] - Bot's responses, one per input item
            - nodes: List[ConversationNode] - Conversation nodes containing
              the responses and their context

    Example:
        >>> # Define a prompt generator
        >>> def review_prompt(file_path: str) -> str:
        ...     return f"Review {file_path} for security issues."
        ...
        >>> # Process multiple files in parallel branches
        >>> responses, nodes = prompt_for(
        ...     bot,
        ...     ["auth.py", "api.py", "data.py"],
        ...     review_prompt,
        ...     should_branch=True
        ... )
        >>>
        >>> # Process sequentially, building on previous context
        >>> responses, nodes = prompt_for(
        ...     bot,
        ...     ["Step 1", "Step 2", "Step 3"],
        ...     lambda step: f"Complete {step}...",
        ...     should_branch=False
        ... )

    Note:
        When should_branch is True, this function uses branch() internally,
        allowing parallel exploration of items. When False, it uses chain(),
        which maintains conversation context between items.
    """
    prompts = [dynamic_prompt(item) for item in items]
    if should_branch:
        return branch(bot, prompts, callback)
    else:
        return chain(bot, prompts, callback)


def chain_while(
    bot: Bot,
    prompt_list: List[Prompt],
    stop_condition: Condition = conditions.tool_not_used,
    continue_prompt: str = "ok",
    callback: Optional[Callable[[List[Response], List["ResponseNode"]], None]] = None,
) -> Tuple[List[Response], List["ResponseNode"]]:
    """Execute a sequence of steps where each step can iterate until complete.

    Use when you need to:
    - Guide a bot through ordered steps
    - Allow each step to take multiple iterations
    - Ensure completion criteria for each step
    - Maintain context between steps and iterations

    This function combines two fundamental patterns:
    1. chain(): For sequential processing of steps
    2. prompt_while(): For iteration within each step

    The result is a powerful pattern for complex tasks where each stage
    needs to reach completion before moving to the next.

    Args:
        bot (Bot): The bot to interact with. Maintains conversation context
            across all steps and iterations
        prompt_list (List[Prompt]): Ordered list of step prompts. Each prompt
            should:
            - Define a clear task or objective
            - Include completion criteria
            - Build on previous steps appropriately
            - Be self-contained for iteration
        stop_condition (Condition, optional): Function that determines when
            each step is complete. Takes a Bot parameter and returns bool.
            Common options:
            - conditions.tool_not_used (default): Stop when bot stops using tools
            - conditions.said_DONE: Stop when bot indicates completion
            - Custom conditions for specific criteria
        continue_prompt (str, optional): Prompt to send for each iteration
            after the first when a step hasn't met its stop condition.
            Defaults to 'ok'. Consider customizing for clearer interaction:
            - "Continue with this step..."
            - "Keep going until complete..."
            - "Any more improvements needed?"
        callback (Optional[Callable[[List[Response], List[ResponseNode]], None]]):
            A function (with arguments list[respose], list[node]) which is called
            after each response from the bot.


    Returns:
        Tuple[List[Response], List[ResponseNode]]: A tuple containing:
            - responses (List[str]): All bot responses, including:
                - Initial response for each step
                - All iteration responses
                - Final response for each step
            - nodes (List[ConversationNode]): Conversation nodes containing
              responses and their cumulative context

    Examples:
        >>> # Code improvement chain
        >>> responses, nodes = chain_while(
        ...     bot,
        ...     [
        ...         "Analyze the code and list all issues...",
        ...         "Fix each identified issue...",
        ...         "Add tests for the changes...",
        ...         "Document the improvements..."
        ...     ],
        ...     stop_condition=conditions.said_DONE,
        ...     continue_prompt="Continue until this step is complete..."
        ... )
        >>>
        >>> # Document review chain
        >>> responses, nodes = chain_while(
        ...     bot,
        ...     [
        ...         "Review document structure and format...",
        ...         "Check content for accuracy and clarity...",
        ...         "Improve language and style...",
        ...         "Add missing sections and details...",
        ...         "Final proofreading..."
        ...     ],
        ...     stop_condition=conditions.tool_not_used,
        ...     continue_prompt="Continue reviewing..."
        ... )

    Implementation Notes:
        - Maintains continuous context across steps
        - Each step can iterate independently
        - Tool handler is cleared after completion
        - All responses and iterations are preserved
        - Context includes full iteration history
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
        if callback:
            try:
                callback(responses, nodes)
            except Exception as e:
                pass  # Don't let callback errors break the main function
    return responses, nodes


def branch_while(
    bot: Bot,
    prompt_list: List[Prompt],
    stop_condition: Condition = conditions.tool_not_used,
    continue_prompt: str = "ok",
    callback: Optional[Callable[[List[Response], List[ResponseNode]], None]] = None,
) -> Tuple[List[Response], List[ResponseNode]]:
    """Create parallel conversation branches with independent iteration control.

    Use when you need to explore multiple iterative processes independently,
    where each process may require a different number of steps to complete.
    This function combines the parallel exploration capability of branch()
    with the iterative control of prompt_while(), allowing multiple
    concurrent processes to run until they individually reach completion.

    Args:
        bot (Bot): The bot to interact with
        prompt_list (List[Prompt]): Initial prompts that start each branch.
            Each prompt begins an independent conversation path that can
            iterate multiple times
        stop_condition (Condition, optional): Function that determines when
            each branch should stop iterating. Takes a Bot parameter and
            returns bool. Defaults to conditions.tool_not_used, which stops
            when the bot stops using tools
        continue_prompt (str, optional): Prompt to send for each iteration
            after the first when a branch hasn't met its stop condition.
            Defaults to 'ok'
        callback (Optional[Callable[[List[Response], List[ResponseNode]], None]]):
            A function (with arguments list[respose], list[node]) which is called
            after each response from the bot.

    Returns:
        Tuple[List[Response], List[ResponseNode]]: A tuple containing:
            - responses: List[str] - Final responses from each branch,
              representing the last response before the stop condition was met
            - nodes: List[ConversationNode] - Conversation nodes containing
              the final responses and their full iteration history
            Note: Failed branches return (None, None) at their positions

    Examples:
        >>> # Optimize multiple functions until they're "DONE"
        >>> responses, nodes = branch_while(
        ...     bot,
        ...     [
        ...         "Optimize sort() until O(n log n) average case...",
        ...         "Improve search() until O(log n) worst case...",
        ...         "Reduce memory usage in cache() to O(n)..."
        ...     ],
        ...     stop_condition=conditions.said_DONE,
        ...     continue_prompt="Continue optimization"
        ... )
        >>>
        >>> # Process multiple files until no more tools are used
        >>> responses, nodes = branch_while(
        ...     bot,
        ...     [
        ...         "Review and fix issues in auth.py...",
        ...         "Review and fix issues in api.py...",
        ...         "Review and fix issues in data.py..."
        ...     ],
        ...     stop_condition=conditions.tool_not_used,
        ...     continue_prompt="Continue reviewing and fixing"
        ... )

    Note:
        Each branch maintains its own conversation context and can iterate
        a different number of times. This is useful when some tasks may
        require more steps to complete than others.
    """
    original_conversation = bot.conversation
    responses = []
    nodes = []
    for initial_prompt in prompt_list:
        bot.conversation = original_conversation  # Reset to original state for each branch
        try:
            response = bot.respond(initial_prompt)
            while not stop_condition(bot):
                response = bot.respond(continue_prompt)
                if callback:
                    try:
                        callback([response], [bot.conversation])
                    except Exception as e:
                        pass  # Don't let callback errors break the main function
            node = bot.conversation
        except Exception as e:
            response = None
            node = None
        finally:
            responses.append(response)
            nodes.append(node)
    return responses, nodes


def par_branch(
    bot: Bot, prompts: List[Prompt], callback: Optional[Callable[[List[Response], List[ResponseNode]], None]] = None
) -> Tuple[List[Response], List[ResponseNode]]:
    """Create and process multiple conversation branches in parallel.

    Use when you need to explore multiple lines of thinking simultaneously and
    want to leverage multiple CPU cores for faster processing. This is the
    parallel version of branch(), providing the same functionality but with
    improved performance for multiple prompts.

    Args:
        bot (Bot): The bot to interact with
        prompts (List[Prompt]): List of prompts to process in parallel
        callback (Optional[Callable[[List[Response], List[ResponseNode]], None]]):
            A function (with arguments list[respose], list[node]) which is called
            after each response from the bot.

    Returns:
        Tuple[List[Response], List[ResponseNode]]: A tuple containing:
            - List of responses, one per prompt
            - List of conversation nodes containing those responses
            Note: Failed branches return (None, None) at their positions

    Example:
        responses, nodes = par_branch(
            bot,
            [
                "Analyze code structure...",
                "Review documentation...",
                "Check test coverage...",
                "Audit dependencies..."
            ]
        )

    Note:
        This function temporarily disables bot autosave and creates a temporary
        file to facilitate parallel processing. The file is cleaned up after
        completion.
    """

    original_autosave = bot.autosave
    original_conversation = bot.conversation
    bot.autosave = False
    temp_file = "temp_bot.bot"
    bot.save(temp_file)
    responses = [None] * len(prompts)
    nodes = [None] * len(prompts)

    def process_prompt(index: int, prompt: str) -> Tuple[int, Response, ResponseNode]:
        try:
            branch_bot = Bot.load(temp_file)
            branch_bot.autosave = False
            response = branch_bot.respond(prompt)
            new_node = branch_bot.conversation
            new_node.parent.parent = original_conversation
            original_conversation.replies.append(new_node.parent)
            if callback:
                try:
                    callback([response], [new_node])
                except Exception as e:
                    pass  # Don't let callback errors break the main function
            return index, response, new_node.parent
        except Exception as e:
            return index, None, None

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_prompt, i, prompt) for i, prompt in enumerate(prompts)]
        for future in as_completed(futures):
            idx, response, node = future.result()
            responses[idx] = response
            nodes[idx] = node

    bot.autosave = original_autosave
    try:
        os.remove(temp_file)
    except OSError:
        pass
    return responses, nodes


def par_branch_while(
    bot: Bot,
    prompt_list: List[Prompt],
    stop_condition: Condition = conditions.tool_not_used,
    continue_prompt: str = "ok",
    callback: Optional[Callable[[List[Response], List[ResponseNode]], None]] = None,
) -> Tuple[List[Response], List[ResponseNode]]:
    """Execute multiple iterative conversation branches in parallel threads.

    Use when you need to explore multiple iterative processes simultaneously
    This is the parallel processing version of branch_while(), using
    ThreadPoolExecutor to run multiple conversation branches concurrently.

    Performance Benefits:
    - Processes multiple branches simultaneously using thread pool
    - Reduces total execution time for multiple long-running tasks
    - Especially effective when branches have similar iteration counts

    Args:
        bot (Bot): The bot to interact with. A copy is made for each branch
            to ensure thread safety
        prompt_list (List[Prompt]): Initial prompts that start each branch.
            Each prompt begins an independent conversation path that runs
            in its own thread
        stop_condition (Condition, optional): Function that determines when
            each branch should stop iterating. Takes a Bot parameter and
            returns bool. Must be thread-safe. Defaults to
            conditions.tool_not_used
        continue_prompt (str, optional): Prompt to send for each iteration
            after the first when a branch hasn't met its stop condition.
            Defaults to 'ok'
        callback (Optional[Callable[[List[Response], List[ResponseNode]], None]]):
            A function (with arguments list[respose], list[node]) which is called
            after each response from the bot.

    Returns:
        Tuple[List[Response], List[ResponseNode]]: A tuple containing:
            - responses: List[str] - Final responses from each branch,
              representing the last response before the stop condition was met
            - nodes: List[ConversationNode] - Conversation nodes containing
              the final responses and their full iteration history
            Note: Failed branches return (None, None) at their positions

    Examples:
        >>> # Parallel optimization of multiple components
        >>> responses, nodes = par_branch_while(
        ...     bot,
        ...     [
        ...         "Optimize database queries until response time < 100ms...",
        ...         "Reduce API latency until < 50ms...",
        ...         "Improve cache hit rate until > 95%..."
        ...     ],
        ...     stop_condition=conditions.said_DONE,
        ...     continue_prompt="Continue optimization"
        ... )
        >>>
        >>> # Parallel code review and fix
        >>> responses, nodes = par_branch_while(
        ...     bot,
        ...     [
        ...         "Review and fix security issues in auth.py...",
        ...         "Review and fix performance in api.py...",
        ...         "Review and fix error handling in data.py..."
        ...     ],
        ...     stop_condition=conditions.tool_not_used,
        ...     continue_prompt="Continue fixes"
        ... )

    Implementation Notes:
        - Uses temporary file to store bot state for thread safety
        - Disables autosave during parallel processing
        - Each branch gets its own bot instance to prevent interference
        - Conversation nodes are properly re-linked after parallel execution
        - Temporary resources are cleaned up after completion
    """

    original_autosave = bot.autosave
    original_conversation = bot.conversation
    bot.autosave = False
    temp_file = "temp_bot.bot"
    bot.save(temp_file)
    responses = [None] * len(prompt_list)
    nodes = [None] * len(prompt_list)

    def process_branch(index: int, initial_prompt: str) -> Tuple[int, Response, ResponseNode]:
        try:
            branch_bot = Bot.load(temp_file)
            branch_bot.autosave = False
            first_response = branch_bot.respond(initial_prompt)
            first_response_node = branch_bot.conversation
            response = first_response
            if callback:
                try:
                    callback([response], [branch_bot.conversation])
                except Exception as e:
                    pass  # Don't let callback errors break the main function

            while not stop_condition(branch_bot):
                response = branch_bot.respond(continue_prompt)
                if callback:
                    try:
                        callback([response], [branch_bot.conversation])
                    except Exception as e:
                        pass  # Don't let callback errors break the main function
            # Return the final node after all iterations, not the first node
            final_node = branch_bot.conversation
            # Link the *first* node back to the original conversation
            first_response_node.parent.parent = original_conversation
            # And link the original conversation to the initial prompt node
            original_conversation.replies.append(first_response_node.parent)
            return index, response, final_node.parent
        except Exception as e:
            return index, None, None

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_branch, i, prompt) for i, prompt in enumerate(prompt_list)]
        for future in as_completed(futures):
            idx, response, node = future.result()
            responses[idx] = response
            nodes[idx] = node

    bot.autosave = original_autosave
    try:
        os.remove(temp_file)
    except OSError:
        pass
    return responses, nodes


def par_dispatch(
    bot_list: List[Bot], functional_prompt: Callable[[Bot, Any], Tuple[Response, ResponseNode]], **kwargs: Any
) -> List[Tuple[Optional[Response], Optional[ResponseNode]]]:
    """Execute a functional prompt pattern across multiple bots in parallel.

    Use when you need to:
    - Compare how different LLM providers handle the same task
    - Test multiple bot configurations simultaneously
    - Run the same complex operation across a fleet of bots
    - Benchmark performance across different bot implementations

    This function enables parallel processing of any functional prompt pattern
    (chain, branch, tree_of_thought, etc.) across multiple bots using a thread
    pool for concurrent execution.

    Args:
        bot_list (List[Bot]): List of bots to process in parallel. Each bot
            can be a different type (AnthropicBot, OpenAIBot, etc.) or the
            same type with different configurations
        functional_prompt (Callable[[Bot, ...], Tuple[Response, ResponseNode]]):
            Any function from this module that takes a bot as its first
            argument. Common choices include:
            - chain: For sequential processing
            - branch: For parallel exploration
            - tree_of_thought: For complex reasoning
         **kwargs (Any): Additional arguments to pass to the functional prompt.
            These must match the signature of the chosen functional_prompt

    Returns:
        List[Tuple[Optional[Response], Optional[ResponseNode]]]: A list with
        the same length as bot_list, where each element is either:
            - A tuple (response, node) from successful execution
            - A tuple (None, None) if that bot's execution failed
        The ordering matches the input bot_list.

    Examples:
        >>> # Compare LLM providers on code review
        >>> results = par_dispatch(
        ...     [anthropic_bot, openai_bot, claude_bot],
        ...     chain,
        ...     prompts=[
        ...         "Review code structure...",
        ...         "Identify security issues...",
        ...         "Suggest improvements..."
        ...     ]
        ... )
        >>>
        >>> # Compare different temperature settings
        >>> results = par_dispatch(
        ...     [
        ...         AnthropicBot(temperature=0.1),
        ...         AnthropicBot(temperature=0.5),
        ...         AnthropicBot(temperature=0.9)
        ...     ],
        ...     tree_of_thought,
        ...     prompts=["Solve this complex problem..."],
        ...     recombinator_function=my_recombinator
        ... )
        >>>
        >>> # Process and compare results
        >>> for bot, (response, node) in zip(bot_list, results):
        ...     print(f"{bot.name} ({bot.temperature}): {response}")

    Implementation Notes:
        - Uses ThreadPoolExecutor for parallel processing
        - Each bot executes independently in its own thread
        - Failed executions are caught and return (None, None)
        - Order of results matches order of input bots
        - No state is shared between bot executions
    """
    results = [None] * len(bot_list)

    def process_bot(index: int, bot: Bot) -> Tuple[int, Tuple[Optional[Response], Optional[ResponseNode]]]:
        try:
            result = functional_prompt(bot, **kwargs)
            return index, result
        except Exception as e:
            return index, (None, None)

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_bot, i, bot) for i, bot in enumerate(bot_list)]
        for future in as_completed(futures):
            idx, result = future.result()
            results[idx] = result

    return results


def broadcast_to_leaves(
    bot: Bot,
    prompt: Prompt,
    skip: List[str],
    continue_prompt: Optional[Prompt] = None,
    stop_condition: Optional[Condition] = None,
    callback: Optional[Callable[[List[Response], List[ResponseNode]], None]] = None,
) -> Tuple[List[Response], List[ResponseNode]]:
    """Send a prompt to all leaf nodes in parallel, with optional iteration."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    original_autosave = bot.autosave
    original_conversation = bot.conversation
    bot.autosave = False
    temp_file = "temp_broadcast_bot.bot"
    bot.save(temp_file)

    # Find all leaf nodes starting from current position
    def find_leaves(node: ConversationNode) -> List[ConversationNode]:
        """Recursively find all leaf nodes from the given node."""
        if not node.replies:
            return [node]
        leaves = []
        for reply in node.replies:
            leaves.extend(find_leaves(reply))
        return leaves

    all_leaves = find_leaves(bot.conversation)

    # Filter out skipped leaves based on labels
    target_leaves = []
    for leaf in all_leaves:
        should_skip = False
        if hasattr(leaf, "labels"):
            for label in leaf.labels:
                if label in skip:
                    should_skip = True
                    break
        if not should_skip:
            target_leaves.append(leaf)

    responses = [None] * len(target_leaves)
    nodes = [None] * len(target_leaves)

    def process_leaf(index: int, leaf: ConversationNode):
        """Process a single leaf node with optional iteration in parallel."""
        try:
            leaf_bot = Bot.load(temp_file)
            leaf_bot.autosave = False
            leaf_bot.conversation = leaf
            response = leaf_bot.respond(prompt)
            if continue_prompt is not None and stop_condition is not None:
                while not stop_condition(leaf_bot):
                    response = leaf_bot.respond(continue_prompt)
                    if callback:
                        try:
                            callback([response], [leaf_bot.conversation])
                        except Exception as e:
                            pass
            elif callback:
                try:
                    callback([response], [leaf_bot.conversation])
                except Exception as e:
                    pass
            final_node = leaf_bot.conversation
            final_node.parent.parent = original_conversation
            original_conversation.replies.append(final_node.parent)
            return index, response, final_node.parent
        except Exception as e:
            return index, None, None

    # Process all leaves in parallel
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_leaf, i, leaf) for i, leaf in enumerate(target_leaves)]
        for future in as_completed(futures):
            idx, response, node = future.result()
            responses[idx] = response
            nodes[idx] = node

    # Restore bot state
    bot.autosave = original_autosave
    bot.conversation = original_conversation
    try:
        os.remove(temp_file)
    except OSError:
        pass
    return responses, nodes


def broadcast_fp(
    bot: Bot, functional_prompt: FunctionalPrompt, skip: List[str] = None, **kwargs: Any
) -> Tuple[List[Response], List[ResponseNode]]:
    """Execute a functional prompt on all leaf nodes in parallel.

    Use when you need to:
    - Apply the same functional prompt pattern to all conversation endpoints
    - Process multiple conversation branches with the same complex operation
    - Gather results from all leaves using sophisticated prompting patterns
    - Scale functional prompt patterns across conversation trees

    This function finds all leaf nodes from the current conversation position
    and executes the specified functional prompt on each leaf independently
    in parallel threads.

    Args:
        bot (Bot): The bot to interact with
        functional_prompt (FunctionalPrompt): Any functional prompt function
            from this module (chain, branch, tree_of_thought, etc.)
        skip (List[str], optional): List of labels to skip. Leaves with any
            of these labels will not be processed. Defaults to empty list.
        **kwargs: Additional arguments to pass to the functional prompt.
            These must match the signature of the chosen functional_prompt

    Returns:
        Tuple[List[Response], List[ResponseNode]]: A tuple containing:
            - responses: List of responses from each leaf (None for failed/skipped)
            - nodes: List of conversation nodes from each leaf (None for failed/skipped)

    Examples:
        >>> # Chain prompts on all leaves
        >>> responses, nodes = broadcast_fp(
        ...     bot,
        ...     chain,
        ...     prompts=["Analyze this...", "Summarize findings..."]
        ... )
        >>>
        >>> # Tree of thought on all leaves
        >>> responses, nodes = broadcast_fp(
        ...     bot,
        ...     tree_of_thought,
        ...     prompts=["Consider approach A...", "Consider approach B..."],
        ...     recombinator_function=my_recombinator
        ... )
        >>>
        >>> # Skip certain labeled leaves
        >>> responses, nodes = broadcast_fp(
        ...     bot,
        ...     single_prompt,
        ...     skip=["draft", "incomplete"],
        ...     prompt="Finalize this work..."
        ... )
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    if skip is None:
        skip = []

    original_autosave = bot.autosave
    original_conversation = bot.conversation
    bot.autosave = False
    temp_file = "temp_broadcast_fp_bot.bot"
    bot.save(temp_file)

    # Find all leaf nodes starting from current position
    def find_leaves(node: ConversationNode) -> List[ConversationNode]:
        """Recursively find all leaf nodes from the given node."""
        if not node.replies:
            return [node]
        leaves = []
        for reply in node.replies:
            leaves.extend(find_leaves(reply))
        return leaves

    all_leaves = find_leaves(bot.conversation)

    # Filter out skipped leaves based on labels
    target_leaves = []
    for leaf in all_leaves:
        should_skip = False
        if hasattr(leaf, "labels"):
            for label in leaf.labels:
                if label in skip:
                    should_skip = True
                    break
        if not should_skip:
            target_leaves.append(leaf)

    responses = [None] * len(target_leaves)
    nodes = [None] * len(target_leaves)

    def process_leaf(index: int, leaf: ConversationNode):
        """Process a single leaf node with the functional prompt."""
        try:
            leaf_bot = Bot.load(temp_file)
            leaf_bot.autosave = False
            leaf_bot.conversation = leaf

            # Execute the functional prompt on this leaf
            result = functional_prompt(leaf_bot, **kwargs)

            # Handle different return types from functional prompts
            if isinstance(result, tuple) and len(result) == 2:
                if isinstance(result[0], list):
                    # Multiple responses (like from chain, branch)
                    final_response = result[0][-1] if result[0] else None
                    final_node = result[1][-1] if result[1] else None
                else:
                    # Single response (like from single_prompt, tree_of_thought)
                    final_response = result[0]
                    final_node = result[1]
            else:
                final_response = None
                final_node = None

            if final_node:
                final_node.parent.parent = original_conversation
                original_conversation.replies.append(final_node.parent)

            return index, final_response, final_node.parent if final_node else None
        except Exception as e:
            return index, None, None

    # Process all leaves in parallel
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_leaf, i, leaf) for i, leaf in enumerate(target_leaves)]
        for future in as_completed(futures):
            idx, response, node = future.result()
            responses[idx] = response
            nodes[idx] = node

    # Restore bot state
    bot.autosave = original_autosave
    bot.conversation = original_conversation
    try:
        os.remove(temp_file)
    except OSError:
        pass

    return responses, nodes
