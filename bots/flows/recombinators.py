from typing import List, Optional, Tuple

from bots.foundation.base import Bot, ConversationNode

"""
Recombinator functions for combining multiple responses from functional prompts.
This module provides various strategies for combining multiple responses from
parallel conversation branches into a single coherent response.
"""
# Type aliases for clarity
Response = str
ResponseNode = ConversationNode


class recombinators:
    """Collection of recombinator functions for combining multiple responses.
    Recombinators take multiple responses from parallel conversation branches
    and combine them into a single coherent response. They support different
    strategies from simple concatenation to LLM-based judging and merging.
    """

    @staticmethod
    def concatenate(responses: List[Response], nodes: List[ResponseNode], **kwargs) -> Tuple[Response, ResponseNode]:
        """Simple concatenation of all responses with formatting.
        Args:
            responses: List of response strings to combine
            nodes: List of conversation nodes (first one used for return)
            **kwargs: Additional parameters (ignored)
        Returns:
            Tuple of combined response string and conversation node
        """
        if not responses:
            return ("", nodes[0] if nodes else None)
        # Filter out None responses
        valid_responses = [r for r in responses if r is not None]
        if not valid_responses:
            return ("No valid responses to combine", nodes[0] if nodes else None)
        # Create formatted combination
        combined = "Combined Analysis:\n\n"
        for i, response in enumerate(valid_responses, 1):
            combined += f"Response {i}:\n{response}\n\n"
        return (combined.strip(), nodes[0] if nodes else None)

    @staticmethod
    def llm_judge(
        responses: List[Response],
        nodes: List[ResponseNode],
        judge_bot: Optional[Bot] = None,
        instruction: str = (
            "Select the best response from the options below. "
            "Return only the selected response without additional commentary."
        ),
        **kwargs,
    ) -> Tuple[Response, ResponseNode]:
        """Use an LLM to judge and select the best response from options.
        Args:
            responses: List of response strings to judge
            nodes: List of conversation nodes
            judge_bot: Bot to use as judge (creates new AnthropicBot if None)
            instruction: Instruction for the judge bot
            **kwargs: Additional parameters
        Returns:
            Tuple of selected best response and corresponding node
        """
        if not responses:
            return ("", nodes[0] if nodes else None)
        # Filter out None responses
        valid_responses = [(r, n) for r, n in zip(responses, nodes) if r is not None]
        if not valid_responses:
            return ("No valid responses to judge", nodes[0] if nodes else None)
        if len(valid_responses) == 1:
            return valid_responses[0]
        # Create judge bot if not provided
        if judge_bot is None:
            from bots.foundation.anthropic_bots import AnthropicBot

            judge_bot = AnthropicBot()
        # Format options for judging
        options_text = "\n\n".join([f"Option {i+1}:\n{response}" for i, (response, _) in enumerate(valid_responses)])
        judge_prompt = f"{instruction}\n\nOptions:\n{options_text}"
        try:
            judgment = judge_bot.respond(judge_prompt)
            # Try to find which option was selected by looking for "Option X"
            import re

            option_match = re.search(r"Option (\d+)", judgment)
            if option_match:
                option_num = int(option_match.group(1)) - 1
                if 0 <= option_num < len(valid_responses):
                    return valid_responses[option_num]
            # If no clear option selected, try to match content
            for response, node in valid_responses:
                if response.strip() in judgment or judgment in response.strip():
                    return (response, node)
            # Fallback: return the judgment itself with first node
            return (judgment, valid_responses[0][1])
        except Exception as e:
            # Fallback to first response if judging fails
            error_msg = f"Judge error: {str(e)}\n" f"Fallback to first response:\n{valid_responses[0][0]}"
            return (error_msg, valid_responses[0][1])

    @staticmethod
    def llm_vote(
        responses: List[Response],
        nodes: List[ResponseNode],
        judge_bots: Optional[List[Bot]] = None,
        num_judges: int = 3,
        instruction: str = (
            "Select the best response from the options below. " "Return only the number of your choice (1, 2, 3, etc.)."
        ),
        **kwargs,
    ) -> Tuple[Response, ResponseNode]:
        """Use multiple LLM judges to vote on the best response.
        Args:
            responses: List of response strings to judge
            nodes: List of conversation nodes
            judge_bots: List of bots to use as judges (creates new ones if None)
            num_judges: Number of judges to use if creating new bots
            instruction: Instruction for judge bots
            **kwargs: Additional parameters
        Returns:
            Tuple of winning response and corresponding node
        """
        if not responses:
            return ("", nodes[0] if nodes else None)
        # Filter out None responses
        valid_responses = [(r, n) for r, n in zip(responses, nodes) if r is not None]
        if not valid_responses:
            return ("No valid responses to vote on", nodes[0] if nodes else None)
        if len(valid_responses) == 1:
            return valid_responses[0]
        # Create judge bots if not provided
        if judge_bots is None:
            from bots.foundation.anthropic_bots import AnthropicBot

            judge_bots = [AnthropicBot() for _ in range(num_judges)]
        # Format options for voting
        options_text = "\n\n".join([f"Option {i+1}:\n{response}" for i, (response, _) in enumerate(valid_responses)])
        vote_prompt = f"{instruction}\n\nOptions:\n{options_text}"
        # Collect votes
        votes = [0] * len(valid_responses)
        for judge in judge_bots:
            try:
                judgment = judge.respond(vote_prompt)
                # Extract vote number
                import re

                vote_match = re.search(r"\b(\d+)\b", judgment)
                if vote_match:
                    vote_num = int(vote_match.group(1)) - 1
                    if 0 <= vote_num < len(valid_responses):
                        votes[vote_num] += 1
            except Exception:
                continue  # Skip failed votes
        # Find winner
        if sum(votes) == 0:
            # No valid votes, return first response
            return valid_responses[0]
        winner_index = votes.index(max(votes))
        return valid_responses[winner_index]

    @staticmethod
    def llm_merge(
        responses: List[Response],
        nodes: List[ResponseNode],
        merger_bot: Optional[Bot] = None,
        instruction: str = (
            "Combine the following responses into a single, coherent, "
            "non-redundant response that captures the best insights from each:"
        ),
        **kwargs,
    ) -> Tuple[Response, ResponseNode]:
        """Use an LLM to merge multiple responses into a coherent whole.
        Args:
            responses: List of response strings to merge
            nodes: List of conversation nodes
            merger_bot: Bot to use for merging (creates new AnthropicBot if None)
            instruction: Instruction for the merger bot
            **kwargs: Additional parameters
        Returns:
            Tuple of merged response and first conversation node
        """
        if not responses:
            return ("", nodes[0] if nodes else None)
        # Filter out None responses
        valid_responses = [r for r in responses if r is not None]
        if not valid_responses:
            return ("No valid responses to merge", nodes[0] if nodes else None)
        if len(valid_responses) == 1:
            return (valid_responses[0], nodes[0] if nodes else None)
        # Create merger bot if not provided
        if merger_bot is None:
            from bots.foundation.anthropic_bots import AnthropicBot

            merger_bot = AnthropicBot()
        # Format responses for merging
        responses_text = "\n\n---\n\n".join([f"Response {i+1}:\n{response}" for i, response in enumerate(valid_responses)])
        merge_prompt = f"{instruction}\n\nResponses to merge:\n\n{responses_text}"
        try:
            merged_response = merger_bot.respond(merge_prompt)
            return (merged_response, nodes[0] if nodes else None)
        except Exception as e:
            # Fallback to concatenation if merging fails
            fallback = f"Merge error: {str(e)}\n\n" f"Fallback concatenation:\n\n" + "\n\n".join(valid_responses)
            return (fallback, nodes[0] if nodes else None)
