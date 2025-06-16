"""Flows Module - Higher-level interaction patterns for bot behaviors.

This module provides structured patterns and operations for complex bot interactions:

- Core operations (chain, branch, tree_of_thought) for sequential and parallel processing
- Flow composition utilities for building complex behaviors

The flows module consists of one main components:
- functional_prompts: Core operations and building blocks

Example:
    >>> import bots.flows.functional_prompts as fp
    >>> responses, nodes = fp.chain(bot, [
    ...     "First prompt",
    ...     "Second prompt",
    ...     "Third prompt"
    ... ])

    >>> responses, nodes = fp.branch(bot, [
    ...     "Approach A",
    ...     "Approach B",
    ...     "Approach C"
    ... ])
"""

from . import functional_prompts

__all__ = ['functional_prompts']
