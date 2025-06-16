# Functional Prompts Primer

## Introduction

Functional prompts are a powerful paradigm for orchestrating complex AI bot interactions through structured patterns. Instead of simple back-and-forth conversations, functional prompts enable sophisticated reasoning approaches like parallel exploration, iterative refinement, and tree-based thinking.

This primer will guide you through the core concepts, patterns, and practical applications of functional prompts.

## Core Concepts

### What are Functional Prompts?

Functional prompts are higher-level functions that orchestrate bot interactions in common patterns. They transform simple prompt-response cycles into structured flows that can:

- Process multiple prompts sequentially or in parallel
- Iterate until specific conditions are met
- Control complex conversation trees

### Key Benefits

1. **Structured Prompting**: Break complex problems into manageable, ordered steps
2. **Parallel Exploration**: Explore multiple approaches without cross-contamination
3. **Iterative Refinement**: Continue working until completion criteria are met
4. **Context Preservation**: Maintain conversation history and relationships
5. **Reproducible Patterns**: Reuse proven prompt structures

## Fundamental Patterns

### 1. Sequential Processing

#### `chain(bot, prompts)`
Executes prompts in sequence, where each step builds on previous context.

**Use when you need to:**
- Guide through structured steps
- Build complex reasoning progressively
- Maintain context between related prompts

**Example:**
```python
responses, nodes = chain(bot, [
    "Find and read cli.py",
    "Find and read functional_prompts.py",
    "Create a primer on functional prompting. Save to functional_prompt_primer.md"
])
```

#### `prompt_while(bot, first_prompt, continue_prompt, stop_condition)`
Repeats a prompt until a condition is met.

**Use when you need to:**
- Work iteratively on a task
- Continue until specific criteria are met
- Handle tasks with unknown completion time

**Example:**
```python
responses, nodes = prompt_while(
    bot,
    "Debug the file you just read. Fix all errors you find.",
    continue_prompt="Continue debugging. Any more issues?",
    stop_condition=conditions.tool_not_used
)
```

### 2. Parallel Exploration

#### `branch(bot, prompts)`
Creates independent conversation paths from the current state.

**Use when you need to:**
- Work on multiple related files or tasks
- Reset context to a certain point in the conversation, creating a single new branch to work from.
- Generate diverse solutions without cross-influence

**Example:**
```python
responses, nodes = branch(bot, [
    "Analyze from a security perspective...",
    "Analyze from a performance perspective...",
    "Analyze from a maintainability perspective..."
])
```

#### `par_branch(bot, prompts)`
Parallel version of branch().

**Use when you need:**
- Faster processing of multiple prompts

### 3. Advanced Reasoning

#### `tree_of_thought(bot, prompts, recombinator_function)`
Implements tree-of-thought reasoning: branch, explore, then synthesize.

**Use when you need to:**
- Break down complex problems into multiple perspectives, then merge those perspectives
- Synthesize insights from parallel explorations
- Make decisions requiring multiple factors

**Example:**
```python
def combine_analysis(responses, nodes):
    # Simple concatenation
    insights = "\n".join(f"- {r}" for r in responses)
    return f"Combined Analysis:\n{insights}", nodes[0]

response, node = tree_of_thought(
    bot,
    [
        "Evaluate technical feasibility...",
        "Analyze business impact...",
        "Assess user experience..."
    ],
    combine_analysis
)
```

## Iteration Control

### Stop Conditions

Functional prompts use condition functions to control iteration:

- `conditions.tool_not_used` - Stop when bot stops using tools
- `conditions.tool_used` - Stop when bot uses tools
- `conditions.said_DONE` - Stop when response contains "DONE"

**Custom conditions:**
```python
def quality_threshold(bot):
    return "i am done" in bot.conversation.content.lower()

responses, nodes = prompt_while(
    bot = bot,
    initial_prompt = "MESSAGE: do some work"
    continue_promtp = "say 'I am done' if MESSAGE is completely addressed.",
    stop_condition=quality_threshold
)
```

## Advanced Patterns

### Dynamic Prompts

#### `prompt_for(bot, items, dynamic_prompt, should_branch)`
Generates prompts dynamically from data.

**Example:**
```python
def review_prompt(filename):
    return f"Review {filename} for security issues."

responses, nodes = prompt_for(
    bot,
    ["auth.py", "api.py", "data.py"],
    review_prompt,
    should_branch=True  # Process files in parallel
)
```

### Multi-Bot dispatch

#### `par_dispatch(bot_list, functional_prompt, **kwargs)`
Execute any functional prompt across multiple bots in parallel.

**Use when you need to:**
- Run a flow on each of a number of 'primed' bots.
- Compare different LLM providers
- Test multiple configurations

**Example:**
```python

bot = AnthropicBot()

bot_list = bot*5 # Creates 5 copies of the blank bot

# Prime bots with context
for bot, filepath in zip(bot_list, files):
    _ = bot.respond(f"Your filepath is {filepath}. After the next message, please review and debug")

# Dispatch them in parallel
results = par_dispatch(
    bot_list,
    chain_while,
    prompts=[
        "Find and read your file",
        "Create a thorough test file considering all edge cases",
        "Run the test file and debug"
    ]
)
```

### Conversation Tree Operations

#### `broadcast_to_leaves(bot, prompt, skip, continue_prompt, stop_condition)`
Send prompts to all leaf nodes (conversation endpoints) in parallel.

**Use when you need to:**
- Continue multiple conversation branches
- Apply operations to all endpoints
- E.g. After making a set of files, broadcast an instruction to write tests.

## Practical Applications

### 1. Code Review Workflow

```python
# Multi-perspective code analysis
responses, nodes = branch(bot, [
    "Review for security vulnerabilities...",
    "Check for performance issues...",
    "Evaluate code maintainability...",
    "Assess test coverage..."
])

# Synthesize findings using a bot
def combine_reviews(bot, responses, nodes):
    summary = f"Code Review:\n" + "\n".join(f"• {r}" for r in responses)
    response = bot.respond(f"Please review the code review below and create a summary with categorized issues, suggested next actions, and priorities.\n\n{summary}")
    return response, bot.conversation

combiner_bot = bots.load('combiner.bot')

final_review, _ = recombine(bot, responses, nodes, lambda responses, nodes: combine_reviews(combiner_bot, responses, nodes))
```

### 2. Iterative Problem Solving

```python
# Work on problem until completion
responses, nodes = chain_while(
    bot,
    [
        "STEP 1: Understand the problem requirements...",
        "STEP 2: Design a solution approach...",
        "STEP 3: Implement the solution...",
        "STEP 4: Test and validate..."
    ],
    stop_condition=conditions.said_DONE,
    continue_prompt="say command 'DONE' if the latest STEP is complete (but not before)"
)
```

### 3. Research and Analysis

```python
# Parallel research on different aspects
research_topics = [
    "Current market trends",
    "Competitor analysis", 
    "Technology landscape",
    "Regulatory considerations"
]

def research_prompt(topic):
    return f"Research and summarize: {topic}"

bot = AnthropicBot(allow_web_search=True)

responses, nodes = prompt_for(
    bot,
    research_topics,
    research_prompt,
    should_branch=True
)
```

## Best Practices

### 1. Prompt Design

- **Be specific**: Clear, focused prompts yield better results
- Generally - follow prompting best practices.

### 2. Condition Selection

- **tool_not_used**: Good general purpose condition for agentic tasks
- **Custom conditions**: Tailor to specific completion criteria

### 3. Continue Prompt
- **'ok'** is the best general purpose continue prompt. It does not anchor toward action (like 'continue' does) or stopping (like 'stop if <condition>' does).

### 4. Performance Considerations

- Parallel functional prompts (`par_branch`, `par_branch_while`) may cause you to hit rate limits.

## Integration with CLI

The functional prompts integrate seamlessly with the CLI system:

```bash
# Interactive functional prompt wizard
>>> /fp

# Broadcast functional prompts to all leaves
>>> /broadcast_fp
```

The CLI provides:
- Interactive parameter collection
- Real-time tool result display
- Conversation tree navigation
- Error recovery with backups

## Common Patterns and Recipes
### 1. Single Agentic Task (Most Common)
```python
# The most common functional prompt pattern - let the bot work autonomously
responses, nodes = prompt_while(
   bot,
   "Please analyze the codebase and create comprehensive documentation.",
   continue_prompt="ok",
   stop_condition=conditions.tool_not_used
)
```

This is the bread-and-butter pattern for all agentic tasks. The bot will:
- Start working on the initial task
- Continue iterating with "ok" prompts until it stops using tools
- (Current SOTA LLMs will) Give a summary without using a tool when complete.
- Handle complex multi-step processes autonomously

### 2. List and Execute Pattern
```python
# First, get a list of tasks
task_response = bot.respond("Break down this project into 5-7 specific, parallelizable, actionable tasks. List them clearly with numbers and periods: 1. task, 2. task, 3. task, etc.")

# Extract task numbers (assuming tasks are numbered 1-N)
import re
task_matches = re.findall(r'(\d+)\.', task_response)
task_numbers = [int(match) for match in task_matches]

# Create prompts for each task
task_prompts = [
   f"Do task {n} from this list:\n\n{task_response}"
   for n in task_numbers
]

# Execute all tasks in parallel
responses, nodes = par_branch_while(
   bot,
   task_prompts,
   stop_condition=conditions.tool_not_used,
   continue_prompt="ok"
)
```

This pattern is excellent for:
- Breaking down complex tasks into parallel work
- Ensuring all subtasks reference the same master list
- Maximizing parallelization while maintaining context

### 3. List and Execute (Simplified)
```python
# Alternative approach using prompt_for with dynamic prompts
def task_prompt(task_number):
   return f"Do task {task_number} from the list we discussed earlier."

# Get the task list first
task_list_response = bot.respond("Create a numbered list of 5 tasks for this project.")

# Execute tasks in parallel
responses, nodes = prompt_for(
   bot = bot,
   items = range(1, 6),  # Tasks 1-5
   dynamic_prompt = task_prompt,
   should_branch=True
)
```


### Iterative Refinement
```python
# Keep improving until quality threshold is met
def quality_check(bot):
    bot = bots.load('quality.bot')
    content = bot.conversation.content.lower()
    return any(phrase in content for phrase in ["excellent", "perfect", "optimal"])

responses, nodes = prompt_while(
    bot,
    "Write a comprehensive project proposal. Aim for excellence.",
    continue_prompt="Review and improve the proposal further.",
    stop_condition=quality_check
)
```

## Conclusion

Functional prompts transform AI interactions from simple conversations into structured reasoning systems. By mastering these patterns, you can:

- Solve complex problems systematically
- Explore multiple perspectives efficiently
- Build robust, reproducible workflows
- Scale task management to projects and beyond

Start with simple patterns like `chain` and `branch`, then progress to advanced techniques like `tree_of_thought` and `par_dispatch` as your needs grow.

The key is matching the right pattern to your specific requirements and building up complexity gradually.
