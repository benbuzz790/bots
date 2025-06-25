# Installation and Quick Start
## Installation
### Basic Installation
`bash
pip install git+https://github.com/benbuzz790/bots.git
`
### Development Installation
`bash
git clone https://github.com/benbuzz790/bots.git
cd bots
pip install -e .[dev]
`
### Requirements
- Python 3.6+
- API key from OpenAI or Anthropic
## API Key Setup
Set your API key as an environment variable:
**For Anthropic (Claude):**
`bash
export ANTHROPIC_API_KEY="your-api-key-here"
`
**For OpenAI (GPT):**
`bash
export OPENAI_API_KEY="your-api-key-here"
`
**Windows PowerShell:**
`powershell
$env:ANTHROPIC_API_KEY="your-api-key-here"
$env:OPENAI_API_KEY="your-api-key-here"
`
## Usage Patterns: From Basic to Advanced
### Level 1: Basic Bot Interaction
#### Simple Tool Creation and Usage
`python
import bots
def read_file(file_path: str) -> str:
    """Read and return file contents.
    Use when you need to read text files from the filesystem.
    Parameters:
    - file_path (str): Path to the file to read
    Returns:
    str: File contents or error message
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error: {str(e)}"
# Create bot and add tool
bot = bots.AnthropicBot()
bot.add_tools(read_file)
# Single interaction
response = bot.respond("Read the README.md file and summarize it")
print(response)
`
#### Interactive Chat
`python
# Start interactive terminal chat
bot.chat()
`
### Level 2: Tool Modules and State Management
#### Using Built-in Tool Modules
`python
import bots
import bots.tools.code_tools as code_tools
bot = bots.AnthropicBot()
bot.add_tools(code_tools)  # Adds multiple code-related tools
# Bot now has access to:
# - view()
# - view_dir()
# - patch_edit()
response = bot.respond("Create a Flask app in app.py with basic routing")
`
#### Bot State Persistence
`python
import bots
import bots.tools.code_tools as code_tools
# Create and configure bot
bot = bots.AnthropicBot()
bot.add_tools(code_tools)
# Build context
bot.respond("Analyze the current directory structure")
bot.respond("Read all Python files and understand the codebase")
# Save complete bot state (conversation + tools + context)
bot.save("codebase_expert.bot")
# Later: Load bot with all context preserved
expert_bot = bots.load("codebase_expert.bot")
expert_bot.respond("Create comprehensive tests for the main module")
`
### Level 3: Functional Prompts - Structured Workflows
#### Sequential Processing (Chain)
`python
import bots.flows.functional_prompts as fp
bot = bots.AnthropicBot()
bot.add_tools(code_tools)
# Execute prompts in sequence, building context
responses, nodes = fp.chain(bot, [
    "Analyze the current directory structure",
    "Read the main application files", 
    "Identify potential security vulnerabilities",
    "Create a security audit report in security_audit.md"
])
# Each step builds on previous context
for i, response in enumerate(responses):
    print(f"Step {i+1}: {response[:100]}...")
`
#### Parallel Exploration (Branch)
`python
# Explore multiple approaches without cross-contamination
responses, nodes = fp.branch(bot, [
    "Analyze the code for security issues",
    "Analyze the code for performance bottlenecks", 
    "Analyze the code for maintainability problems",
    "Analyze the code for testing gaps"
])
# Each analysis starts from the same initial context
for analysis_type, response in zip(['Security', 'Performance', 'Maintainability', 'Testing'], responses):
    print(f"{analysis_type} Analysis: {response[:100]}...")
`
#### Iterative Refinement (Autonomous Mode)
`python
# Let the bot work autonomously until completion
responses, nodes = fp.prompt_while(
    bot,
    "Create a complete web application with authentication, database, and API",
    continue_prompt="ok",  # Simple continuation
    stop_condition=fp.conditions.tool_not_used  # Stop when bot stops using tools
)
print(f"Completed in {len(responses)} iterations")
`
### Level 4: Advanced Patterns and Parallel Processing
#### Tree-of-Thought Reasoning
`python
def combine_analyses(responses, nodes):
    """Synthesize multiple analysis perspectives"""
    combined = "\\n".join(f"{r}" for r in responses)
    return f"Comprehensive Analysis:\\n{combined}", nodes[0]
# Branch, analyze, then synthesize
response, node = fp.tree_of_thought(
    bot,
    [
        "Evaluate technical architecture and scalability",
        "Assess business logic and requirements coverage", 
        "Review user experience and interface design",
        "Analyze security and compliance aspects"
    ],
    combine_analyses
)
`
#### Multi-Bot Parallel Dispatch
`python
# Create specialized bots for different tasks
base_bot = bots.AnthropicBot()
base_bot.add_tools(code_tools)
# Create multiple bot instances
bot_fleet = base_bot * 5
# Prime each bot with specific context
contexts = [
    "You are a security expert. Focus on vulnerabilities.",
    "You are a performance expert. Focus on optimization.",
    "You are a UX expert. Focus on user experience.", 
    "You are a testing expert. Focus on test coverage."
]
for bot, context in zip(bot_fleet, contexts):
    bot.respond(context) # prime with context
# Execute same workflow across all bots in parallel
results = fp.par_dispatch(
    bot_fleet,
    fp.chain,
    prompts=[
        "Analyze the current codebase",
        "Identify the top 3 issues in your domain",
        "Propose specific solutions with code examples"
    ]
)
`
#### Dynamic Prompt Generation
`python
# Generate prompts from data
files = ["auth.py", "api.py", "models.py", "utils.py"]
def review_prompt(filename):
    return f"Perform a detailed code review of {filename}, focusing on best practices and potential issues"
# Process all files in parallel
responses, nodes = fp.prompt_for(
    bot,
    files,
    review_prompt,
    should_branch=True  # Parallel processing
)
`
### Level 5: CLI Integration and Advanced Navigation
#### Advanced CLI Usage
`bash
# Start CLI with pre-loaded bot
python -m bots.dev.cli my_expert.bot
# In CLI - navigate conversation tree
>>> /up      # Move up in conversation history
>>> /down    # Move down to child nodes
>>> /left    # Navigate between branches
>>> /right   # Navigate between branches
>>> /goto 5  # Jump to specific node
# Autonomous mode
>>> /auto    # Bot continues working until no tools are used
# Functional prompt wizard
>>> /fp      # Interactive functional prompt selection
# Broadcast a fp to all conversation endpoints
>>> /broadcast_fp
`
#### CLI Functional Prompt Integration
`bash
# In CLI session
>>> /fp
Select functional prompt:
1. chain
2. branch  
3. prompt_while
4. par_branch_while
>>> 3
Enter initial prompt: Create comprehensive documentation
Enter continue prompt: ok
Select stop condition:
1. tool_not_used
2. tool_used  
3. said_DONE
>>> 1
# Bot executes autonomous workflow
`
### Level 6: Runtime Code Generation with @lazy
#### Basic Lazy Functions
`python
from bots import lazy
@lazy("Implement quicksort with detailed comments")
def quicksort(arr: list[int]) -> list[int]:
    pass  # Implementation generated at runtime
# First call triggers LLM code generation
result = quicksort([3, 1, 4, 1, 5, 9, 2, 6])
print(result)  # [1, 1, 2, 3, 4, 5, 6, 9]
`
#### Advanced Lazy with Context
`python
@lazy(
    "Implement a thread-safe LRU cache with TTL support",
    context='high',  # Include full codebase context
    bot=bots.load('architecture_expert.bot')  # Use specialized bot
)
class TTLCache:
    pass  # Full class implementation generated at runtime
# Usage triggers implementation generation
cache = TTLCache(max_size=100, ttl_seconds=300)
cache.put("key", "value")
`
### Level 7: Production Workflows
#### Complete Project Analysis Pipeline
`python
import bots
import bots.flows.functional_prompts as fp
import bots.tools.code_tools as code_tools
# Create specialized analysis bot
analyzer = bots.AnthropicBot(name="project_analyzer")
analyzer.add_tools(code_tools)
# Build comprehensive project understanding
fp.chain_while(analyzer, [
    "Scan the entire project directory structure",
    "Read and analyze all configuration files (package.json, requirements.txt, etc.)",
    "Read and understand the main application entry points",
    "Map out the project architecture and dependencies"
])
# Save the context-rich bot
analyzer.save("project_expert.bot")
# Parallel analysis across multiple dimensions
analysis_bot = bots.load("project_expert.bot")
analyses, nodes = fp.par_branch_while(
    analysis_bot,
    [
        "Create comprehensive API documentation",
        "Generate detailed deployment guide", 
        "Write complete testing strategy",
        "Produce security assessment report",
        "Create performance optimization plan"
    ],
    stop_condition=fp.conditions.tool_not_used,
    continue_prompt="ok"
)
print(f"Generated {len(analyses)} comprehensive reports")
`
#### Continuous Integration Workflow
`python
# CI/CD bot that can be triggered by webhooks
ci_bot = bots.AnthropicBot(name="ci_assistant")
ci_bot.add_tools([code_tools, testing_tools, deployment_tools])
# Autonomous CI workflow
fp.prompt_while(
    ci_bot,
    "Analyze the latest commit, run all tests, check code quality, and deploy if everything passes",
    continue_prompt="ok",
    stop_condition=fp.conditions.tool_not_used
)
`
## Key Concepts Progression
1. **Basic**: Single bot, simple tools, direct interaction
2. **Intermediate**: Tool modules, state persistence, conversation management  
3. **Advanced**: Functional prompts, structured workflows, parallel processing
4. **Expert**: Branching-bot systems, dynamic generation, production pipelines
Each level builds on the previous, allowing you to start simple and scale to sophisticated AI-powered workflows as your needs grow.
