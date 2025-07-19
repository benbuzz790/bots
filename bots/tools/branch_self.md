# Branch Self Tool - Design and Implementation

## Overview

The `branch_self` tool enables an AI assistant to create multiple parallel conversation branches to explore different approaches, tackle separate tasks, or generate multiple solutions simultaneously. Each branch receives its own copy of the conversation history and executes independently before results are merged back into the main conversation. Recursive branching is intended.

## Core Design Principles

### 1. Conversation Tree Integrity

The tool maintains a proper conversation tree structure where:
- Each branch becomes a direct child of the original assistant node that made the `branch_self` call
- All branch user nodes share the same `tool_use_id` (as they all respond to the same branching request)
- The conversation follows the expected pattern: `Assistant (tool_use) → User (tool_result) → Assistant (response) → etc`

### 2. API Compliance

The implementation ensures compliance with the Anthropic API requirements:
- Each `tool_use` has exactly one corresponding `tool_result` in the immediate following user message
- Tool results only appear in user messages, never assistant messages
- No duplicate `tool_use_id` values appear in ancestor-descendant relationships

### 3. Minimal Conversation Pollution

Branch execution details are kept internal to the tool. The main conversation only sees:
- The original branching request
- A summary of branch execution results (in a tool result)

However
- The individual branch conversations become part of the tree structure
- This allows later modification or continuation

- This means the user only sees the results of the branches, but is able to communicate with the branches if needed later. A CLI allows the user to traverse the tree at their discretion.

## Implementation Architecture

### Conversation Structure

```
Before execution is complete - dummy result put in place to satisfy API requirement for paired tool requests and results. (Note, all 'response to taskX' responses below may be conversation chains. Only the first response is shown for brevity)

Assistant (tool_use: branch_self, id=X)
    └── User (tool_result: id=X, content="Branching In Progress...") + "(self-prompt): task 1"
    │   └── Assistant: "response to task1"
    ├── User (tool_result: id=X, content="Branching In Progress...") + "(self-prompt): task2"
    │   └── Assistant: "response to task2"
    └── User (tool_result: id=X, content="Branching In Progress...") + "(self-prompt): task3"
    	└── Assistant: "response to task3"

After execution is complete, but before another message is sent - pending result with summary is added to original node (as is the case with every tool result)

Assistant (tool_use: branch_self, id=X) + (pending_result: tool_result: id=X, content="Successfully created... and summary...")
    └── User (tool_result: id=X, content="Branching In Progress...") + "(self-prompt): task 1"
    │   └── Assistant: "response to task1"
    ├── User (tool_result: id=X, content="Branching In Progress...") + "(self-prompt): task2"
    │   └── Assistant: "response to task2"
    └── User (tool_result: id=X, content="Branching In Progress...") + "(self-prompt): task3"
    	 └── Assistant: "response to task3"

After the next user message is sent - Tool results sync across nodes, overwriting because ID is the same

Assistant (tool_use: branch_self, id=X)
    └── User (tool_result: id=X, content="Successfully created... and summary...") + "(self-prompt): task 1"
    │   └── Assistant: "response to task1"
    ├── User (tool_result: id=X, content="Successfully created... and summary...") + "(self-prompt): task2"
    │   └── Assistant: "response to task2"
    └── User (tool_result: id=X, content="Successfully created... and summary...") + "(self-prompt): task3"
    |	 └── Assistant: "response to task3"
    └── User (tool_result: id=X, content="Successfully created... and summary...") + "<next user msg>"

```

### Key Components

1. **Branch Execution**: Each branch runs in isolation with its own bot instance
2. **Tree Merging**: Results are merged back into a flat structure (not nested)
3. **Tool Result Management**: All branches share the same tool result content but exist as separate conversation paths
4. **Recombination**: When requested, results are combined and included in the tool result

### Tool Result Flow

1. **Initial State**: Assistant makes `branch_self` tool call
2. **Branch Creation**: Each branch gets created as a direct child with the same `tool_use_id`
3. **Result Updates**: All branch tool results are updated with the final execution summary
4. **Conversation Continues**: Normal conversation flow resumes from any branch point

## Design Rationale

### Why 'Flat' Structure?

A flat structure (branches as direct children) rather than nested structure prevents:
- Duplicate `tool_use_id` values in ancestor-descendant chains
- Complex message serialization issues
- API violations regarding tool result placement

### Why Shared Tool Use ID?

All branches respond to the same original `branch_self` request, so they logically share the same `tool_use_id`. This maintains the semantic relationship while allowing multiple conversation paths.

### Why No Assistant Messages for Results?

Adding assistant messages for branch summaries for recombination results creates nodes that can receive pending tool results, leading to API violations. Instead, all summary information is included in the tool result content.

### Why Direct Child Placement?

Placing branches as direct children of the original assistant node:
- Maintains proper tool call → tool result relationships
- Prevents message structure violations
- Keeps the conversation tree semantically correct
- Allows for proper tool result synchronization

### Why use a dummy result instead of hiding the tool request from the child branches?

Hiding the tool request has the effect of making the LLM believe branching *has not yet occurred* and therefore it tries to start branching again. This results in infinite recursive branching.

## Usage Patterns

### Basic Branching
```python
branch_self("['Analyze data', 'Create visualization', 'Write summary']")
```

### Iterative Work
```python
branch_self("['Task 1', 'Task 2']", allow_work="True")
```

### With Recombination
```python
branch_self("['Approach A', 'Approach B']", recombine="llm_judge")
```

## Error Handling

The tool handles various failure modes:
- Individual branch failures (continues with successful branches)
- File system issues (temporary bot file management)
- API errors (proper error propagation)
- Malformed inputs (validation and error messages)