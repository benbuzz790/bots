# Getting Started with Bots
Welcome to the **bots** framework! This guide will walk you through everything you need to know to start building powerful AI agents, from basic interactions to advanced workflows.
## Table of Contents
1. [Installation & Setup](#installation--setup)
2. [Your First Bot](#your-first-bot)
3. [Adding Tools to Your Bot](#adding-tools-to-your-bot)
4. [Saving and Loading Bots](#saving-and-loading-bots)
5. [Functional Prompts: Chaining Conversations](#functional-prompts-chaining-conversations)
6. [Parallel Processing with Branching](#parallel-processing-with-branching)
7. [Advanced Workflows](#advanced-workflows)
8. [Building Custom Tools](#building-custom-tools)
9. [The Lazy Decorator: Runtime Code Generation](#the-lazy-decorator-runtime-code-generation)
10. [CLI Interface](#cli-interface)
11. [Real-World Examples](#real-world-examples)
## Installation & Setup
### 1. Install the Package
`ash
pip install git+https://github.com/benbuzz790/bots.git
`
### 2. Set Up Your API Keys
You'll need an API key from either OpenAI or Anthropic (or both):
**For Anthropic (Claude):**
`ash
# Windows
set ANTHROPIC_API_KEY=your_api_key_here
# macOS/Linux
export ANTHROPIC_API_KEY=your_api_key_here
`
**For OpenAI (GPT):**
`ash
# Windows
set OPENAI_API_KEY=your_api_key_here
# macOS/Linux
export OPENAI_API_KEY=your_api_key_here
`
Get your API keys:
- [Anthropic API Key](https://docs.anthropic.com/en/docs/initial-setup#set-your-api-key)
- [OpenAI API Key](https://platform.openai.com/docs/quickstart)
## Your First Bot
Let's start with the simplest possible bot interaction:
`python
# basic_bot.py
import bots
# Create a bot (uses Claude by default)
bot = bots.AnthropicBot()
# Have a conversation
response = bot.respond("Hello! What can you help me with?")
print(response)
# Start an interactive chat
bot.chat()  # Type 'exit' to quit
`
**What's happening here:**
- AnthropicBot() creates a new Claude-powered bot
- espond() sends a single message and gets a response
- chat() starts an interactive terminal session
**Try it yourself:**
1. Save the code above as asic_bot.py
2. Run python basic_bot.py
3. Chat with your bot!
## Adding Tools to Your Bot
Bots become powerful when you give them tools. Let's create a bot that can read files:
`python
# file_reader_bot.py
import bots
def read_file(file_path: str) -> str:
    """Read and return the contents of a text file.
    Use when you need to read the contents of a text file from the filesystem.
    Parameters:
    - file_path (str): The path to the file to be read
    Returns:
    str: The contents of the file, or an error message if reading fails
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as e:
        return f"Error: {str(e)}"
# Create bot and add the tool
bot = bots.AnthropicBot()
bot.add_tools(read_file)
# Now your bot can read files!
bot.chat()
`
**Try asking your bot:**
- "Can you read the README.md file?"
- "What's in my config.txt file?"
- "Read setup.py and tell me what this project does"
**Key points about tools:**
- Tools must be functions that return strings
- Include clear docstrings with "Use when..." sections
- Handle errors gracefully
- The bot automatically knows when and how to use your tools
## Saving and Loading Bots
One of the most powerful features is saving your bot's complete state:
`python
# persistent_bot.py
import bots
import bots.tools.code_tools as code_tools
# Create and configure a bot
bot = bots.AnthropicBot(name="MyCodeBot")
bot.add_tools(code_tools)  # Add built-in code tools
# Have some conversations to build context
bot.respond("Please analyze the structure of this project")
bot.respond("What programming languages are used here?")
# Save the entire bot state
bot.save("my_code_bot.bot")
# Later, load the bot with all its context
loaded_bot = bots.load("my_code_bot.bot")
loaded_bot.respond("Based on what you learned earlier, what should I work on next?")
`
**What gets saved:**
- Complete conversation history
- All added tools and their source code
- Bot configuration and parameters
- The bot "remembers" everything from previous sessions
## Functional Prompts: Chaining Conversations
Functional prompts let you create sophisticated conversation workflows:
`python
# chain_example.py
import bots
import bots.flows.functional_prompts as fp
import bots.tools.code_tools as code_tools
bot = bots.AnthropicBot()
bot.add_tools(code_tools)
# Chain: Execute prompts in sequence, each building on the previous
prompts = [
    "Look at the current directory structure",
    "Read the main Python files", 
    "Identify the core functionality",
    "Suggest improvements to the code organization"
]
responses, nodes = fp.chain(bot, prompts)
# Each response builds on all previous context
for i, response in enumerate(responses):
    print(f"Step {i+1}: {response[:100]}...")
`
**Chain vs Single Prompts:**
- Single prompt: One question, one answer
- Chain: Each step builds on all previous steps
- Perfect for analysis workflows, step-by-step tasks
## Parallel Processing with Branching
Sometimes you want to explore multiple approaches simultaneously:
`python
# branch_example.py
import bots
import bots.flows.functional_prompts as fp
import bots.tools.code_tools as code_tools
bot = bots.AnthropicBot()
bot.add_tools(code_tools)
# Branch: Explore different analysis approaches in parallel
analyses = [
    "Analyze this codebase for security vulnerabilities",
    "Analyze this codebase for performance bottlenecks", 
    "Analyze this codebase for maintainability issues",
    "Analyze this codebase for testing coverage"
]
responses, nodes = fp.branch(bot, analyses)
# Each analysis starts fresh, exploring different aspects
for i, response in enumerate(responses):
    print(f"Analysis {i+1}: {response[:100]}...")
`
**When to use branching:**
- Comparing different approaches
- Parallel analysis of different aspects
- Exploring multiple solutions to the same problem
## Advanced Workflows
### Conditional Loops with prompt_while
Continue working until a condition is met:
`python
# iterative_improvement.py
import bots
import bots.flows.functional_prompts as fp
import bots.tools.code_tools as code_tools
bot = bots.AnthropicBot()
bot.add_tools(code_tools)
# Keep improving code until no more tools are used
responses, nodes = fp.prompt_while(
    bot,
    "Analyze the code and fix any issues you find",
    continue_prompt="Continue improving",
    stop_condition=fp.conditions.tool_not_used  # Stop when bot doesn't use tools
)
print(f"Completed {len(responses)} improvement iterations")
`
### Parallel Processing with par_branch
Process multiple items simultaneously:
`python
# parallel_processing.py
import bots
import bots.flows.functional_prompts as fp
import bots.tools.code_tools as code_tools
# Create multiple bots for parallel work
bots_list = [bots.AnthropicBot() for _ in range(3)]
for bot in bots_list:
    bot.add_tools(code_tools)
# Process different files in parallel
file_analyses = [
    "Analyze main.py for code quality",
    "Analyze utils.py for code quality", 
    "Analyze config.py for code quality"
]
# Each bot works on a different file simultaneously
responses, nodes = fp.par_branch(bots_list, file_analyses)
`
## Building Custom Tools
Tools are the key to extending your bot's capabilities. Here's how to build effective ones:
### Tool Requirements
`python
def my_tool(parameter: str) -> str:
    """Brief description of what the tool does.
    Use when you need to [specific use case].
    Parameters:
    - parameter (str): Description of the parameter
    Returns:
    str: Description of what gets returned
    """
    try:
        # Your tool logic here
        result = do_something(parameter)
        return result
    except Exception as e:
        return f"Error: {str(e)}"
`
### Example: Web Scraper Tool
`python
# web_tools.py
import requests
from bs4 import BeautifulSoup
def scrape_webpage(url: str) -> str:
    """Scrape and return the text content of a webpage.
    Use when you need to get the text content from a website or webpage.
    Parameters:
    - url (str): The URL of the webpage to scrape
    Returns:
    str: The text content of the webpage, or an error message
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        return text[:5000]  # Limit length
    except Exception as e:
        return f"Error scraping {url}: {str(e)}"
# Use the tool
import bots
bot = bots.AnthropicBot()
bot.add_tools(scrape_webpage)
bot.respond("Can you scrape https://example.com and summarize what you find?")
`
### Tool Collections
You can add entire modules as tools:
`python
import bots
import bots.tools.code_tools as code_tools
import bots.tools.terminal_tools as terminal_tools
bot = bots.AnthropicBot()
bot.add_tools(code_tools)      # File operations, code analysis
bot.add_tools(terminal_tools)  # Command execution
bot.add_tools(my_custom_tools) # Your custom tool module
`
## The Lazy Decorator: Runtime Code Generation
The @lazy decorator generates code implementations at runtime:
`python
# lazy_example.py
from bots import lazy
@lazy("Sort using a divide-and-conquer approach with O(n log n) complexity")
def mergesort(arr: list[int]) -> list[int]:
    pass  # Implementation generated by LLM on first call
@lazy("Implement a key-value store with LRU eviction policy")
class Cache:
    pass  # Class implementation generated by LLM
# Use them normally - implementation happens automatically
sorted_array = mergesort([3, 1, 4, 1, 5, 9])
cache = Cache()
`
**Lazy decorator options:**
`python
@lazy(
    "Implementation description",
    bot=my_saved_bot,           # Use specific bot
    context='high',             # Context level: none, low, medium, high, very_high
    model_engine=Engines.GPT4   # Specific model
)
def my_function():
    pass
`
**Context levels:**
- 
one: No additional context
- low: Minimal context (class or module)
- medium: Entire current file
- high: Current file plus interfaces of other files
- ery_high: All Python files in directory
## CLI Interface
The CLI provides an advanced interface for working with bots:
`ash
# Start the CLI
python -m bots.dev.cli
# Or load a specific bot
python -m bots.dev.cli my_bot.bot
`
**Key CLI commands:**
- /up, /down, /left, /right - Navigate conversation tree
- /auto - Enable autonomous mode (bot continues until no tools used)
- /save filename - Save current bot state
- /load filename - Load a bot file
- /fp - Run functional prompt wizard
- /verbose - Show tool outputs
- /quiet - Hide tool outputs
- /help - Show all commands
**CLI Workflow Example:**
1. Start CLI: python -m bots.dev.cli
2. Add tools: ot.add_tools(code_tools)
3. Start analysis: "Please analyze this codebase"
4. Enable auto mode: /auto
5. Let bot work autonomously until complete
6. Save results: /save analysis_bot.bot
## Real-World Examples
### 1. Code Review Bot
`python
# code_review_bot.py
import bots
import bots.flows.functional_prompts as fp
import bots.tools.code_tools as code_tools
def create_code_review_bot():
    bot = bots.AnthropicBot(name="CodeReviewer")
    bot.add_tools(code_tools)
    # Build context about the project
    setup_prompts = [
        "Read the README.md to understand this project",
        "Look at the directory structure",
        "Identify the main Python files"
    ]
    fp.chain(bot, setup_prompts)
    return bot
# Create and save the bot
review_bot = create_code_review_bot()
review_bot.save("code_reviewer.bot")
# Use for reviews
review_bot.respond("Please review the changes in main.py and suggest improvements")
`
### 2. Documentation Generator
`python
# doc_generator.py
import bots
import bots.flows.functional_prompts as fp
import bots.tools.code_tools as code_tools
import bots.tools.python_editing_tools as edit_tools
bot = bots.AnthropicBot(name="DocGenerator")
bot.add_tools(code_tools)
bot.add_tools(edit_tools)
# Generate documentation for all Python files
doc_prompts = [
    "Find all Python files in this project",
    "For each file, check if it has proper docstrings",
    "Add missing docstrings following Google style",
    "Create a comprehensive API documentation file"
]
responses, nodes = fp.chain_while(
    bot,
    doc_prompts,
    stop_condition=fp.conditions.tool_not_used
)
`
### 3. Test Generator
`python
# test_generator.py
import bots
import bots.flows.functional_prompts as fp
import bots.tools.code_tools as code_tools
bot = bots.AnthropicBot(name="TestGenerator")
bot.add_tools(code_tools)
# Generate comprehensive tests
test_workflow = [
    "Analyze the main application code",
    "Identify functions and classes that need testing",
    "Create comprehensive pytest test files",
    "Ensure good test coverage for edge cases"
]
fp.chain(bot, test_workflow)
bot.save("test_generator.bot")
`
## Best Practices
### 1. Tool Design
- **Single purpose**: Each tool should do one thing well
- **Error handling**: Always catch and return errors as strings
- **Clear documentation**: Include "Use when..." in docstrings
- **String inputs/outputs**: Prefer strings for reliability
### 2. Bot Management
- **Save frequently**: Save bot states after building useful context
- **Descriptive names**: Use clear names for saved bots
- **Context building**: Let bots learn about your project first
### 3. Workflow Design
- **Chain for sequential**: Use chain() when each step builds on previous
- **Branch for parallel**: Use ranch() for independent analyses
- **Loops for iteration**: Use prompt_while() for iterative improvement
### 4. Performance
- **Parallel processing**: Use par_branch() for independent tasks
- **Context management**: Higher context levels cost more but give better results
- **Tool efficiency**: Efficient tools make bots faster
## Troubleshooting
### Common Issues
**Bot not using tools:**
- Check tool docstrings have "Use when..." sections
- Ensure tools return strings
- Verify tools are properly added with ot.add_tools()
**API errors:**
- Verify API keys are set correctly
- Check internet connection
- Ensure sufficient API credits
**Performance issues:**
- Use appropriate context levels for @lazy
- Consider parallel processing for independent tasks
- Save and reuse bots with built context
### Getting Help
- Check the [GitHub repository](https://github.com/benbuzz790/bots) for issues
- Look at the examples directory for more patterns
- Use the CLI /help command for interface help
## Next Steps
Now that you understand the basics, try:
1. **Build a custom tool** for your specific needs
2. **Create a specialized bot** for your domain
3. **Experiment with functional prompts** for complex workflows
4. **Try the CLI interface** for interactive development
5. **Explore the lazy decorator** for runtime code generation
The bots framework is designed to grow with your needs. Start simple and gradually add complexity as you become more comfortable with the patterns.
Happy bot building! 🤖
