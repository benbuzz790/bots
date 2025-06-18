"""Example demonstrating functional prompt patterns using chain() and branch().
Use when you need to understand how to:
    - Create sequential vs parallel conversation flows
    - Compare different conversation strategies with the same prompts
    - Handle multiple conversation branches effectively
This example illustrates two key functional prompt patterns:
1. chain() - Sequential conversation where each prompt builds on previous
   responses
   Returns: Tuple[List[str], List[ConversationNode]] - responses and nodes
2. branch() - Parallel conversation paths exploring different dialogue
   directions
   Returns: Tuple[List[str], List[ConversationNode]] - responses and nodes
Example usage:
    python functional_prompt_example.py
The example uses a playful conversation to demonstrate how the same prompts can
produce different conversation patterns when used with chain vs branch
approaches.
Key differences demonstrated:
- chain(): Each response builds on all previous context
- branch(): Each response starts fresh from the initial context
Returns:
    Prints the conversation patterns for both chain and branch approaches,
    showing how the same prompts produce different conversation flows.
"""

from typing import List

import bots
import bots.flows.functional_prompts as fp
from bots.foundation.base import ConversationNode  # For type hints

# Initialize bots for different conversation patterns (each maintains its own
# conversation tree)
chain_bot: bots.AnthropicBot = bots.AnthropicBot(name="chain-bot")
branch_bot: bots.AnthropicBot = bots.AnthropicBot(name="branch-bot")
# Define conversation prompts that progress from casual to specific topics.
# Each prompt builds on assumed previous responses to demonstrate context
# handling.
prompt_set: List[str] = [
    "Let's count to 6, you start",
    "2",
    "4",
    "6",
]
# Demonstrate sequential conversation pattern (each response sees all previous
# context)
responses: List[str]
nodes: List[ConversationNode]
responses, nodes = fp.chain(chain_bot, prompt_set)
print("Chain conversation pattern:")
print(chain_bot)
# Demonstrate parallel conversation branches (each response starts from root
# context)
responses: List[str]
nodes: List[ConversationNode]
responses, nodes = fp.branch(branch_bot, prompt_set)
print("\nBranch conversation pattern:")
print(branch_bot)
