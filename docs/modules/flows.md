# Flows Module

**Module**: `bots/flows/`
**Version**: 3.0.0

## Overview

Functional prompts and recombination strategies

## Architecture

```
flows/
├── __init__.py
├── functional_prompts.py
├── recombinators.py
```

## Key Components

### conditions

Predefined condition functions for controlling bot iteration.

### recombinators

Collection of recombinator functions for combining multiple responses.


## Usage Examples

```python
from bots.flows import *

# Usage examples coming soon
```

## API Reference

### Classes and Functions

| Name | Type | Description |
|------|------|-------------|
| `conditions` | Class | Predefined condition functions for controlling bot iteration |
| `dynamic_prompts` | Class | Factory functions for creating dynamic prompts based on bot  |
| `single_prompt` | Function | Execute a single prompt and return both response and convers |
| `chain` | Function | Execute a sequence of prompts that build on each other. |
| `branch` | Function | Create multiple independent conversation paths from the curr |
| `recombine` | Function | Synthesize multiple conversation branches into a unified con |
| `tree_of_thought` | Function | Implement tree-of-thought reasoning for complex problem-solv |
| `prompt_while` | Function | Repeatedly engage a bot in a task until completion criteria  |
| `prompt_for` | Function | Generate and process prompts dynamically from a list of item |
| `chain_while` | Function | Execute a sequence of steps where each step can iterate unti |
| `branch_while` | Function | Create parallel conversation branches with independent itera |
| `par_branch` | Function | Create and process multiple conversation branches in paralle |
| `par_branch_while` | Function | Execute multiple iterative conversation branches in parallel |
| `par_dispatch` | Function | Execute a functional prompt pattern across multiple bots in  |
| `broadcast_to_leaves` | Function | Send a prompt to all leaf nodes in parallel, with optional i |
| `broadcast_fp` | Function | Execute a functional prompt on all leaf nodes in parallel. |
| `said_READY` | Function | Check if the bot's response contains the word 'READY'. |
| `five_iterations` | Function | Create a condition that stops after five iterations. |
| `no_new_tools_used` | Function | Check if the bot used the same tools as in the previous resp |
| `error_in_response` | Function | Check if the bot's response contains error indicators. |
| `tool_used` | Function | Check if the bot has used any tools in its last response. |
| `tool_not_used` | Function | Check if the bot has not used any tools in its last response |
| `said_DONE` | Function | Check if the bot's response contains the word 'DONE'. |
| `static` | Function | Create a dynamic prompt that always returns the same string. |
| `policy` | Function | Create a dynamic prompt that selects prompts based on rules. |
| `process_prompt` | Function | No description |
| `process_branch` | Function | No description |
| `process_bot` | Function | No description |
| `find_leaves` | Function | Recursively find all leaf nodes from the given node. |
| `process_leaf` | Function | Process a single leaf node with optional iteration in parall |
| `find_leaves` | Function | Recursively find all leaf nodes from the given node. |
| `process_leaf` | Function | Process a single leaf node with the functional prompt. |
| `condition` | Function | No description |
| `static_prompt_func` | Function | No description |
| `dynamic_prompt_func` | Function | No description |
| `recombinators` | Class | Collection of recombinator functions for combining multiple  |
| `concatenate` | Function | Simple concatenation of all responses with formatting. |
| `llm_judge` | Function | Use an LLM to judge and select the best response from option |
| `llm_vote` | Function | Use multiple LLM judges to vote on the best response. |
| `llm_merge` | Function | Use an LLM to merge multiple responses into a coherent whole |
