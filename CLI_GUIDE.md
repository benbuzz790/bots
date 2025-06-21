# CLI Guide: Interactive Bot Interface
The bots CLI provides a powerful interactive terminal interface for working with AI bots. It combines conversational AI with advanced navigation, state management, and functional programming capabilities.
## Quick Start
### Starting the CLI
`ash
# Start with a new bot
python -m bots.dev.cli
# Load an existing bot
python -m bots.dev.cli mybot.bot
# Auto-add .bot extension
python -m bots.dev.cli saved_conversation
`
### Basic Usage
Once started, you can:
- **Chat normally**: Type messages to interact with the bot
- **Use commands**: Prefix with / for special commands
- **Navigate conversations**: Move through conversation history like a tree
- **Execute functional prompts**: Run complex AI workflows
## Core Concepts
### Conversation Tree Structure
The CLI treats conversations as a tree where:
- Each message creates a new node
- You can branch conversations at any point
- Navigate up/down and left/right through the tree
- Save positions with labels for quick access
### Tool Integration
Bots have access to powerful tools:
- **PowerShell execution**: Run system commands
- **Python execution**: Execute Python code
- **File operations**: Read, write, and edit files
- **Code editing**: Specialized Python editing tools
## Command Reference
### Navigation Commands
#### /up - Move Up in Conversation Tree
Moves to the parent node (previous turn) in the conversation.
`
>>> /up
Moved up conversation tree
`
**Use case**: "Rewind" a conversation to try a different approach.
#### /down - Move Down in Conversation Tree
Moves to a child node (next turn). If multiple replies exist, prompts for selection.
`
>>> /down
Reply index (max 2): 1
Moved down conversation tree
`
#### /left / /right - Navigate Siblings
Move between alternative conversation branches at the same level.
`
>>> /left
Moved left in conversation tree
>>> /right  
Moved right in conversation tree
`
#### /root - Go to Root
Jump to the beginning of the conversation tree.
`
>>> /root
Moved to root of conversation tree
`
#### /leaf [number] - Show and Navigate to Leaves
Display all conversation endpoints (leaves) and optionally jump to one.
`
>>> /leaf
Found 3 leaf nodes:
  1. [depth 4]: Analyzing the code structure...
  2. [depth 3] (labels: debug): Found the bug in line 42...
  3. [depth 5]: Implementation complete...
Enter a number (1-3) to jump to that leaf, or press Enter to stay: 2
Jumped to leaf 2: Found the bug in line 42...
`
**Direct jump**: /leaf 2 jumps directly to leaf 2.
### State Management Commands
#### /save - Save Bot State
Save the complete bot state including conversation history and tools.
`
>>> /save
Save filename (without extension): my_project_bot
Bot saved to my_project_bot.bot
`
#### /load - Load Bot State
Load a previously saved bot with all context restored.
`
>>> /load
Load filename: my_project_bot.bot
Bot loaded from my_project_bot.bot. Conversation restored to most recent message.
`
### Labeling and Bookmarks
#### /label - Label Current Node
Save the current conversation position with a memorable name.
`
>>> /label
Label: working_solution
Saved current node with label: working_solution
`
#### /goto - Go to Labeled Node
Jump to a previously labeled conversation node.
`
>>> /goto
Label: working_solution
Moved to node labeled: working_solution
`
#### /showlabels - Show All Labels
Display all saved labels and their associated content.
`
>>> /showlabels
Saved labels:
  'working_solution': The implementation works correctly...
  'debug_point': Found an issue with the validation...
`
### Advanced Features
#### /auto - Autonomous Mode
Let the bot work independently until it stops using tools.
`
>>> /auto
Bot running autonomously. Press ESC to interrupt...
[Bot continues working until completion]
Bot finished autonomous execution
`
**Key features**:
- Bot sends "ok" messages to itself
- Continues until no tools are used
- Press ESC to interrupt
- Useful for letting the bot complete complex tasks
#### /fp - Functional Prompts Wizard
Execute sophisticated AI workflows with dynamic parameter collection.
`
>>> /fp
Available functional prompts:
  1. single_prompt
  2. chain
  3. branch
  4. tree_of_thought
  5. prompt_while
  6. chain_while
  7. branch_while
Select functional prompt (number or name): 3
Collecting parameters for branch:
  Parameter: prompts (default: required)
Enter prompts (empty line to finish):
Prompt 1: Analyze the security aspects
Prompt 2: Review performance implications  
Prompt 3: Check for usability issues
Executing branch...
[Creates three parallel conversation branches]
`
#### /broadcast_fp - Broadcast to Multiple Leaves
Execute functional prompts on selected conversation endpoints.
`
>>> /broadcast_fp
Found 4 leaf nodes:
  1. [depth 3]: Security analysis complete...
  2. [depth 4]: Performance looks good...
  3. [depth 2]: UI needs improvement...
  4. [depth 5]: All tests passing...
Select leaves to broadcast to (e.g., '1,3,5' or 'all' for all leaves): 1,3
Select functional prompt to broadcast:
  1. single_prompt
  2. chain
  [...]
Select functional prompt: 1
Enter prompt: Summarize your findings
Broadcasting single_prompt to 2 selected leaves...
Broadcast completed: 2 successful
`
#### /combine_leaves - Merge Conversation Endpoints
Combine multiple conversation branches using AI-powered recombination.
`
>>> /combine_leaves
Found 3 leaves to combine.
Available recombinators:
  1. concatenate
  2. llm_judge
  3. llm_vote
  4. llm_merge
Select recombinator: 4
Combining 3 leaves using llm_merge...
[AI merges the different conversation branches into a unified result]
`
### Configuration Commands
#### /verbose / /quiet - Control Tool Output
Toggle display of tool requests and results.
`
>>> /verbose
Tool output enabled
>>> /quiet  
Tool output disabled
`
#### /config - View/Modify Settings
Show or change CLI configuration.
`
>>> /config
Current configuration:
    verbose: True
    width: 1000
    indent: 4
>>> /config set width 80
Set width to 80
`
### System Commands
#### /help - Show Help
Display comprehensive help information.
#### /exit - Exit CLI
Quit the CLI interface.
## Common Workflows
### 1. Exploratory Analysis
`ash
# Start with a broad question
>>> Analyze this codebase for potential improvements
# Branch into specific areas
>>> /fp
# Select "branch" and add prompts:
# - Security analysis
# - Performance review  
# - Code quality check
# Navigate between branches
>>> /leaf
# Jump between different analysis results
# Combine insights
>>> /combine_leaves
# Use llm_merge to synthesize findings
`
### 2. Iterative Development
`ash
# Start development task
>>> Create a REST API for user management
# Save progress points
>>> /label
Label: initial_implementation
# Let bot work autonomously
>>> /auto
# If issues arise, backtrack
>>> /goto
Label: initial_implementation
# Try alternative approach
>>> Let's use FastAPI instead of Flask
`
### 3. Debugging Session
`ash
# Load project context
>>> /load project_bot.bot
# Analyze the issue
>>> There's a bug in the authentication module
# Create debugging branches
>>> /fp
# Use "branch" with prompts:
# - Check input validation
# - Review error handling
# - Test edge cases
# Navigate to most promising lead
>>> /leaf 2
# Continue investigation
>>> /auto
`
### 4. Code Review Workflow
`ash
# Load the codebase context
>>> Read all Python files in the src directory
# Create comprehensive review
>>> /fp
# Use "par_branch" for parallel analysis:
# - Security vulnerabilities
# - Performance bottlenecks
# - Code style issues
# - Documentation gaps
# Broadcast follow-up questions
>>> /broadcast_fp
# Select all leaves, use single_prompt:
# "Provide specific recommendations"
# Synthesize final report
>>> /combine_leaves
# Use llm_merge for comprehensive summary
`
## Tips and Best Practices
### Navigation Tips
- Use /label frequently to mark important conversation points
- /leaf is great for seeing all conversation endpoints at once
- /root followed by /down lets you replay conversations step by step
### Functional Prompt Tips
- **chain**: Use for sequential tasks that build on each other
- **branch**: Use for exploring multiple approaches simultaneously  
- **prompt_while**: Use for iterative refinement until a condition is met
- **tree_of_thought**: Use for complex reasoning that needs multiple perspectives
### State Management Tips
- Save bots with descriptive names: project_analysis.bot, debug_session.bot
- Use labels for major milestones: working_version, efore_refactor
- Load saved bots to continue work sessions
### Tool Integration Tips
- Enable /verbose when debugging tool usage
- Use /quiet for cleaner output during autonomous mode
- The bot can read files, execute code, and make system changes - be careful!
### Autonomous Mode Tips
- Use /auto for tasks that require multiple tool calls
- Press ESC to interrupt if the bot gets stuck
- Save state before using /auto in case you need to backtrack
## Troubleshooting
### Common Issues
**Bot not responding to commands**
- Ensure commands start with /
- Check /help for correct command syntax
**Navigation confusion**
- Use /showlabels to see saved positions
- Use /leaf to see all conversation endpoints
- Use /root to start over
**Tool output overwhelming**
- Use /quiet to reduce verbosity
- Use /config set width 80 for narrower output
**Functional prompt errors**
- Check parameter requirements with the wizard
- Some prompts need specific conditions or recombinators
### Recovery Options
- Conversation backup is automatic - most commands can be undone
- Use /goto with labels to return to known good states
- /load a saved bot to restore a previous session
## Advanced Features
### Custom Function Filters
The CLI supports custom function filters for limiting available functional prompts:
`python
def my_filter(name, func):
    # Only allow certain functional prompts
    return name in ['chain', 'branch', 'single_prompt']
cli = CLI(function_filter=my_filter)
`
### Callback Customization
Different callback types control how tool results are displayed:
- **Standard**: Shows tool results based on verbose setting
- **Quiet**: Shows only tool names used
- **Verbose**: Always shows full tool details
- **Message-only**: Shows only bot responses
### Integration with Other Tools
The CLI integrates seamlessly with:
- Git operations (through terminal tools)
- Python development (through code editing tools)
- File system operations (through PowerShell tools)
- Custom tools added to bots
This makes it a powerful environment for AI-assisted development, analysis, and automation tasks.
