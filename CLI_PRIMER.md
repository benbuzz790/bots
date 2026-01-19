# Bots CLI Primer: Complete Guide to the Command Line Interface

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Basic Concepts](#basic-concepts)
4. [Navigation Commands](#navigation-commands)
5. [State Management](#state-management)
6. [Functional Prompts](#functional-prompts)
7. [Advanced Features](#advanced-features)
8. [Workflow Examples](#workflow-examples)

---

## Introduction

The Bots CLI is an advanced interactive terminal interface for working with AI agents. Unlike simple chat interfaces, the CLI treats conversations as navigable tree structures, allowing you to explore multiple solution paths, backtrack to earlier points, and orchestrate complex multi-step workflows.
**Key Philosophy:** Conversations aren't linear—they're explorations. The CLI gives you the tools to navigate, branch, and recombine these explorations efficiently.

---

## Getting Started

### Launching the CLI

**Start with a new bot:**

```bash
python -m bots.dev.cli
```

**Start with an existing bot:**

```bash
python -m bots.dev.cli path/to/mybot.bot
```

### Your First Session

When you launch the CLI, you'll see a prompt where you can:

- Type regular messages to chat with the bot
- Use commands (starting with `/`) to control the CLI
- Press Ctrl+C to interrupt long-running operations
- Type `/exit` to quit

**Example first interaction:**

```
You: Hello! Can you help me understand this codebase?
Bot: Of course! I'd be happy to help. What would you like to know about the codebase?
You: /save my_helper.bot
System: Bot saved to my_helper.bot
```

---

## Basic Concepts

### The Conversation Tree

Every conversation in the CLI is a **tree structure**, not a linear chat:

```
Root
 ├─ "What's in this directory?"
 │   ├─ "Read main.py"
 │   │   └─ "Refactor this function"
 │   └─ "Read test.py"
 │       └─ "Add more tests"
 └─ "Check the README"
     └─ "Update documentation"
```

**Why trees?**

- **Exploration:** Try multiple approaches without losing your work
- **Comparison:** Keep different solution attempts side-by-side
- **Efficiency:** Reuse common context without repeating prompts

### Current Position

You're always at a specific **node** in the conversation tree. The CLI shows you:

- The current conversation history (from root to your position)
- Available navigation options
- Tool usage and results (if verbose mode is on)

---

## Navigation Commands

### Basic Movement

#### `/up` - Go Back One Turn

Moves up the tree to the previous message. Like "undo" for conversations, (but not their side effects on the system!)

**Use when:**

- You want to try a different prompt
- The bot's text response wasn't what you needed
- You want to branch from an earlier point
- You send a 'task description' prompt followed by a 'configuration' prompt, and want to run the same task with a different configuration

**Example:**

```
You: Refactor this code
Bot: [makes changes you don't like]
You: /up
System: Moved up to previous node
You: Actually, just add comments instead
```

#### `/down` - Move Forward

Moves down the tree to a reply. If there are multiple replies (branches), you'll be asked to choose.

**Use when:**

- Returning to a branch after going `/up`
- Exploring different branches you created earlier

**Example:**

```
You: /down
System: Multiple replies available:
  0: "Refactor this code"
  1: "Add comments instead"
Which reply? 1
```

#### `/left` and `/right` - Sibling Navigation

Move between branches at the same level (siblings in the tree).
**Use when:**

- Comparing different approaches side-by-side
- Quickly switching between parallel explorations
**Example:**

```
You: /left
System: Moved to left sibling: "Security analysis"
You: /right
System: Moved to right sibling: "Performance analysis"
```

### Advanced Navigation

#### `/root` - Jump to Start

Returns to the very beginning of the conversation tree.

**Use when:**

- Starting a completely new line of inquiry
- Resetting to a clean slate while keeping history

#### `/label` - Bookmark Important Points

Create named bookmarks at important conversation points.

**Usage:**

```
/label                    # Show all existing labels
/label checkpoint1        # Create label "checkpoint1" at current node
/label goto checkpoint1   # Jump to labeled node
```

**Use when:**

- Marking successful solutions
- Creating checkpoints before risky operations
- Organizing complex multi-branch workflows

**Example workflow:**

```
You: Read the codebase
Bot: [reads files]
You: /label codebase_understood
You: Try refactoring approach A
Bot: [attempts refactor]
You: /up
You: /label
System: Available labels: codebase_understood
You: /label goto codebase_understood
System: Jumped to labeled node
You: Try refactoring approach B instead
```

#### `/leaf` - View All Endpoints

Shows all "leaf" nodes (endpoints) in the conversation tree below your current position.

**Usage:**

```
/leaf              # List all leaves with previews
/leaf 3            # Jump to leaf #3
```

**Use when:**

- Reviewing all the different paths you've explored
- Finding a specific branch you worked on earlier
- Understanding the full scope of your exploration

**Example:**

```
You: /leaf
System: Found 4 leaves:
  0: "...refactored main.py successfully"
  1: "...added comprehensive tests"
  2: "...updated documentation"
  3: "...fixed security vulnerability"
Which leaf? 2
```

---

## State Management

### Saving and Loading

#### `/save` - Save Bot State

Saves the entire bot including:

- Complete conversation tree
- All tools and their source code
- Bot configuration and parameters

**Usage:**

```
/save                    # Prompts for filename
/save mybot.bot         # Saves to specific file
```

**Use when:**

- End of a productive session
- Before trying something risky
- Creating shareable bot configurations

#### `/load` - Load Bot State

Loads a previously saved bot, restoring everything.

**Usage:**

```
/load                    # Prompts for filename
/load mybot.bot         # Loads specific file
```

**Important:** Loading moves you to the most recent message in the loaded bot's conversation tree.

### Prompt Management

#### `/s` - Save Prompts

Save frequently-used prompts for quick reuse.

**Usage:**

```
/s                              # Saves your last message
/s Analyze this code for bugs   # Saves specific text
```

#### `/p` - Load Prompts

Search and load saved prompts. The prompt is pre-filled in your input, ready to edit or send.

**Usage:**

```
/p                    # Shows all saved prompts
/p analyze            # Searches for prompts containing "analyze"
```

**Use when:**

- You have standard workflows or templates
- Repeatedly asking similar questions
- Sharing common prompts with team members

---

## Functional Prompts

Functional prompts are powerful workflow patterns that send multiple prompts in structured ways. Access them via `/fp` or `/broadcast_fp`.

### `/fp` - Execute Functional Prompts

Launches an interactive wizard to choose and configure a functional prompt.

**Available Functional Prompts:**

#### 1. **single_prompt** - Simple one-shot prompt

Just sends a single prompt. Useful as a building block for other FPs.

#### 2. **chain** - Sequential prompts

Sends prompts one after another in sequence.

**Example use case:**

```
Prompts: ["Read main.py", "Read test.py", "Identify missing test coverage"]
```

#### 3. **branch** - Parallel exploration

Creates separate conversation branches for each prompt.

**Example use case:**

```
Prompts: ["Security analysis", "Performance analysis", "Code quality analysis"]
```

Each analysis happens independently, preserving all results.

#### 4. **par_branch** - Parallel branching with recombination

Like branch, but combines results at the end.

**Example use case:**

```
Prompts: ["Analyze file A", "Analyze file B", "Analyze file C"]
Recombine: "concatenate" or "llm_merge"
```

#### 5. **prompt_while** - Conditional iteration

Keeps prompting until a condition is met.
**Example use case:**

```
Prompt: "Run tests and fix any failures"
Continue: "ok"
Stop condition: tool_not_used (stops when bot doesn't use tools)
```

#### 6. **chain_while** - Chained conditional iteration

Chains prompts repeatedly until a condition is met.
**Example use case:**

```
Prompts: ["Run tests", "Fix failures", "Verify fixes"]
Stop condition: tool_not_used
```

#### 7. **par_branch_while** - Parallel iteration

Runs multiple branches in parallel until conditions are met.
**Example use case:**

```
Prompts: ["Debug file A", "Debug file B", "Debug file C"]
Continue: "ok"
Stop condition: tool_not_used
```

Each file is debugged independently and in parallel.

#### 8. **broadcast_to_leaves** - Apply to all endpoints

Sends the same prompt to every leaf node below current position.

**Example use case:**
After creating multiple files with par_branch_while:

```
Prompt: "Add error handling and logging"
```

Every file gets the same treatment.

### `/broadcast_fp` - Functional Prompts on All Leaves

Like `/fp`, but automatically applies the chosen functional prompt to all leaf nodes.

**Use when:**

- You've created multiple branches and want to process them all
- Applying the same workflow to multiple files/contexts
- Batch operations across your exploration tree

**Example workflow:**

```
# Create multiple analysis branches
You: /fp
System: Choose functional prompt: par_branch
You: [Enter prompts for different analyses]
# Now apply same refinement to all
You: /broadcast_fp
System: Choose functional prompt: single_prompt
You: "Add actionable recommendations"
System: Applied to 5 leaves
```

---

## Advanced Features

### Autonomous Mode

#### `/auto` - Let the Bot Work

Enables autonomous operation where the bot continues working until it stops using tools.

**How it works:**

1. Bot responds to your prompt
2. If tools were used, CLI automatically sends "ok"
3. Bot continues working
4. Repeats until bot responds without using tools
5. Press ESC to interrupt at any time

**Use when:**

- Complex multi-step tasks
- "Figure it out" scenarios
- Letting the bot explore solutions independently

**Example:**

```
You: Fix all the failing tests in this repository
You: /auto
Bot: [runs tests, identifies failures]
System: [auto-sends "ok"]
Bot: [fixes first failure]
System: [auto-sends "ok"]
Bot: [fixes second failure]
...
Bot: All tests are now passing!
System: Auto mode complete (no tools used)
```

### Leaf Combination

#### `/combine_leaves` - Merge Multiple Branches

Combines all leaf nodes below your current position using a recombinator function.

**Available recombinators:**

- `concatenate`: Simple text concatenation
- `llm_merge`: AI-powered intelligent merging
- `llm_vote`: AI chooses the best option
- `llm_judge`: AI evaluates and ranks options

**Use when:**

- Comparing multiple solution attempts
- Synthesizing insights from parallel analyses
- Creating a final report from multiple branches

**Example:**

```
You: /fp... branch... 1. "Review README.md and critique it" 2. "Review setup.py and critique it" 3. "Read main.py and critique it"
You: /combine_leaves
System: Choose recombinator:
  1. concatenate
  2. llm_merge
  3. llm_vote
  4. llm_judge
You: 2
Bot: Great, I can see what I need to do in all three files
```

### Display Modes

#### `/verbose` - Show Everything (Default)
Shows tool requests, results, and API metrics in detail.
**Displays:**
- Tool requests with parameters
- Tool results
- API metrics (tokens, cost, duration) after each response
- Session totals
**Use when:**
- Debugging
- Learning what the bot is doing
- Verifying tool usage
- Monitoring API costs
See [Cost Tracking](docs/observability/COST_TRACKING.md) for details on metrics.

#### `/quiet` - Hide Tool Details
Hides tool requests, results, and metrics, showing only bot responses.
**Use when:**
- Focused on final outputs
- Cleaner display for presentations
- Working with very verbose tools
- Don't need to see API costs

### Git Integration

#### `/auto_stash` - Automatic Git Stashing

Toggles automatic git stashing before each user message.
**How it works:**

- Before each message, creates a git stash
- Uses AI to generate descriptive stash message
- Allows safe experimentation with code changes
**Use when:**
- Bot is making code changes
- You want easy rollback capability
- Experimenting with risky modifications

#### `/load_stash` - Restore Git Stash

Loads a specific git stash by name or index.

**Usage:**

```
/load_stash 0                    # Load most recent stash
/load_stash WIP: refactor main   # Load by name
```

### Configuration

#### `/config` - View/Modify Settings

Shows or modifies CLI configuration settings.

**Usage:**

```
/config              # Show current configuration
/config set key value   # Modify a setting
```

---

## Workflow Examples

### Example 1: Exploring Multiple Solutions

**Scenario:** You want to try different approaches to refactoring a function.

```
You: Read main.py and find the calculate_total function
Bot: [reads file and shows function]
You: /label baseline
# Try approach A
You: Refactor this using list comprehensions
Bot: [shows refactored version A]
You: /label approach_a
# Try approach B
You: /label goto baseline
You: Refactor this using numpy operations
Bot: [shows refactored version B]
You: /label approach_b
# Compare
You: /combine_leaves
System: Choose recombinator: llm_judge
Bot: Approach B is more efficient for large datasets because...
```

### Example 2: Parallel File Creation

**Scenario:** Create multiple related files simultaneously.

```
You: /fp
System: Choose functional prompt: par_branch_while
You: Enter prompts (one per line, empty line to finish):
     Create a Flask API endpoint for users
     Create a Flask API endpoint for products
     Create a Flask API endpoint for orders
     [empty line]
You: Continue prompt: ok
You: Stop condition: tool_not_used
# Bot creates all three files in parallel
You: /broadcast_fp
System: Choose functional prompt: single_prompt
You: Add input validation and error handling
# All three files get validation added
```

### Example 3: Iterative Debugging

**Scenario:** Fix all issues in a codebase.

```
You: Run all tests and show me the failures
Bot: [runs tests, shows 5 failures]
You: /auto
# Bot automatically fixes each failure one by one
Bot: All tests passing!
You: /up
You: /up
You: /up
# Go back to see the progression
You: /leaf
# Review all the fixes that were made
```

### Example 4: Code Review Workflow

**Scenario:** Comprehensive code review with multiple perspectives.

```
You: Read all Python files in the src directory
Bot: [reads files]
You: /label codebase_loaded
You: /fp
System: Choose: par_branch
You: Enter prompts:
     Analyze for security vulnerabilities
     Analyze for performance issues
     Analyze for code quality and maintainability
     Analyze for test coverage gaps
     [empty line]
# Review each analysis
You: /leaf
System: [shows all 4 analyses]
You: /leaf 0  # Jump to security analysis
[review]
You: /right   # Move to performance analysis
[review]
You: /right   # Move to code quality
[review]
# Combine insights
You: /label goto codebase_loaded
You: /combine_leaves
System: Choose: llm_merge
Bot: [provides comprehensive review combining all perspectives]
```

### Example 5: Documentation Generation

**Scenario:** Generate documentation for multiple modules.

```
You: List all Python modules in the project
Bot: [lists modules]
You: /fp
System: Choose: par_branch
You: Enter prompts:
     Generate API documentation for auth.py
     Generate API documentation for database.py
     Generate API documentation for utils.py
     [empty line]
You: /combine_leaves
System: Choose: concatenate
Bot: [combines all documentation]
You: Save this to API_REFERENCE.md
Bot: [saves file]
```

---

## Command Quick Reference

### Navigation

- `/up` - Move up one level
- `/down` - Move down to a reply
- `/left` - Move to left sibling
- `/right` - Move to right sibling
- `/root` - Jump to conversation start
- `/label [name]` - Create/view/goto labels
- `/leaf [number]` - View/jump to leaf nodes

### State Management

- `/save [filename]` - Save bot state
- `/load [filename]` - Load bot state
- `/s [text]` - Save prompt
- `/p [search]` - Load prompt

### Functional Prompts

- `/fp` - Execute functional prompt
- `/broadcast_fp` - Apply FP to all leaves
- `/combine_leaves` - Merge leaf nodes

### Display & Control

- `/verbose` - Show tool details
- `/quiet` - Hide tool details
- `/auto` - Autonomous mode
- `/help` - Show help
- `/exit` - Exit CLI

### Git Integration

- `/auto_stash` - Toggle auto-stashing

### Configuration

- `/config` - View/modify settings

---

## Conclusion

The Bots CLI transforms AI interaction from linear chat into spatial exploration. By treating conversations as navigable trees, you can:

- **Explore** multiple solutions without losing work
- **Compare** different approaches side-by-side
- **Orchestrate** complex multi-step workflows
- **Synthesize** insights from parallel investigations
Master the navigation commands, experiment with functional prompts, and develop workflows that match your thinking process. The CLI is designed to augment your problem-solving, not constrain it.
**Happy exploring!** 🚀
