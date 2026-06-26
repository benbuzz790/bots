# Installation and Quick Start

This guide gets you from an empty environment to a working bot, then walks up through the patterns you'll reach for as your tasks grow. Each section builds on the one before it, so you can stop whenever the bot does what you need.

## Installation

Install the latest version straight from the repository:

```bash
pip install git+https://github.com/benbuzz790/bots.git
```

If you plan to work on the library itself, clone it and install in editable mode with the development extras:

```bash
git clone https://github.com/benbuzz790/bots.git
cd bots
pip install -e .[dev]
```

You need Python 3.12 or newer and an API key for at least one provider (Anthropic, OpenAI, or Google).

## API keys

A bot reads its key from an environment variable, so you set the key once per shell and never put it in your code. On macOS or Linux:

```bash
export ANTHROPIC_API_KEY="your-key-here"
```

On Windows PowerShell:

```powershell
$env:ANTHROPIC_API_KEY="your-key-here"
```

Use `OPENAI_API_KEY` or `GEMINI_API_KEY` instead, or in addition, for the other providers.

## Level 1: a bot and a tool

A bot responds to a prompt, and you give it abilities by handing it Python functions. There is no schema to write and nothing to register: the function's signature defines the tool's parameters and its docstring tells the model what the tool is for. Write the docstring as if you were explaining the function to a teammate.

```python
import bots

def read_file(file_path: str) -> str:
    """Read and return the contents of a text file.

    Use when you need to see what's in a file on disk.

    Parameters:
        file_path (str): Path to the file to read.

    Returns:
        str: The file's contents, or an error message.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error: {e}"

bot = bots.AnthropicBot()
bot.add_tools(read_file)

print(bot.respond("Read README.md and summarize it in three sentences."))
```

The bot decides on its own to call `read_file`, reads the result, and answers. When you'd rather have a live conversation than a single call, `chat()` opens an interactive terminal session and shows you each tool the bot uses:

```python
bot.chat()   # type messages; "/exit" ends the session
```

## Level 2: tool modules and saved state

Adding tools one function at a time is fine, but most of the time you want a whole toolkit. Passing a module to `add_tools` adds every public function in it at once. The library's built-in modules work exactly like your own:

```python
import bots
import bots.tools.code_tools as code_tools

bot = bots.AnthropicBot()
bot.add_tools(code_tools)   # adds view(), view_dir(), and patch_edit()

bot.respond("Create a Flask app in app.py with a basic /health route.")
```

Once a bot has built up useful context, save it. `save` writes the entire bot to one `.bot` file: the full conversation tree, every tool as source code, and all the configuration. `load` restores it exactly, on this machine or any other.

```python
bot.respond("Read every Python file here and map out the architecture.")
bot.save("codebase_expert.bot")

# later, in a fresh session
expert = bots.load("codebase_expert.bot")
expert.respond("Write thorough tests for the main module.")
```

This turns context into something you build once and reuse. The expensive part, teaching the bot about your project, happens a single time.

## Level 3: functional prompts

A single `respond` is one turn. When a task needs many turns in a known shape, functional prompts supply the shape. They live in `bots.flows.functional_prompts`, and they all take a bot and return the responses and the conversation nodes they produced.

```python
import bots
import bots.flows.functional_prompts as fp
import bots.tools.code_tools as code_tools

bot = bots.AnthropicBot()
bot.add_tools(code_tools)
```

Use `chain` to walk a bot through an ordered sequence where each step builds on the last:

```python
responses, nodes = fp.chain(bot, [
    "Analyze the directory structure.",
    "Read the main application files.",
    "Identify the top security risks.",
    "Write a security audit to security_audit.md.",
])
```

Use `branch` to explore several directions from the same starting point without letting them influence each other:

```python
responses, nodes = fp.branch(bot, [
    "Review the code for security issues.",
    "Review the code for performance problems.",
    "Review the code for maintainability.",
])
```

Use `prompt_while` for the core agentic loop: the bot keeps working, turn after turn, until it stops using tools. This one pattern covers most "just get it done" tasks.

```python
responses, nodes = fp.prompt_while(
    bot,
    "Build a small web app with authentication, a database, and a REST API.",
    continue_prompt="ok",
    stop_condition=fp.conditions.tool_not_used,
)
print(f"Finished in {len(responses)} turns.")
```

## Level 4: parallel and advanced patterns

`tree_of_thought` branches into several perspectives, then synthesizes them into one answer through a recombinator you supply:

```python
def combine(responses, nodes):
    merged = "\n\n".join(responses)
    return f"Combined analysis:\n{merged}", nodes[0]

response, node = fp.tree_of_thought(
    bot,
    [
        "Evaluate the architecture and how it scales.",
        "Assess whether it covers the business requirements.",
        "Review the user experience.",
    ],
    combine,
)
```

`prompt_for` builds a prompt per item from your data and runs them, optionally in parallel branches:

```python
files = ["auth.py", "api.py", "models.py", "utils.py"]

responses, nodes = fp.prompt_for(
    bot,
    files,
    lambda f: f"Do a detailed review of {f}, focusing on best practices.",
    should_branch=True,   # one independent branch per file, in parallel
)
```

`par_dispatch` runs the same functional prompt across a fleet of bots at once. Multiply a bot to get the fleet, prime each member with its own context, then dispatch:

```python
base = bots.AnthropicBot()
base.add_tools(code_tools)
fleet = base * 4   # four independent copies

roles = [
    "You are a security expert. Focus on vulnerabilities.",
    "You are a performance expert. Focus on speed and memory.",
    "You are a UX expert. Focus on the user's experience.",
    "You are a testing expert. Focus on coverage gaps.",
]
for member, role in zip(fleet, roles):
    member.respond(role)

results = fp.par_dispatch(
    fleet,
    fp.chain,
    prompt_list=[
        "Analyze the codebase.",
        "Name the three biggest issues in your area.",
        "Propose fixes with code.",
    ],
)
```

The [Functional Prompts Primer](functional_prompt_primer.md) covers the rest, including iteration with `chain_while`, parallel iteration with `par_branch_while`, and recombining branches.

## Level 5: the CLI

Everything above is also available interactively. Launch the CLI on a new bot, or on a saved one:

```bash
python -m bots.dev.cli
python -m bots.dev.cli codebase_expert.bot
```

Inside, you chat normally and use slash commands to drive the session. `/up`, `/down`, `/left`, and `/right` move around the conversation tree; `/auto` lets the bot work until it stops using tools; and `/fp` opens a wizard that runs any functional prompt with prompts you enter on the spot. The [CLI Primer](CLI_PRIMER.md) is the complete reference.

## Level 6: runtime code generation with @lazy

The `@lazy` decorator defers a function's or class's implementation until the first time it runs, then has a bot write it from the description in the decorator. The body you write is just a placeholder.

```python
from bots import lazy

@lazy("Implement quicksort with clear comments.")
def quicksort(arr: list[int]) -> list[int]:
    pass   # generated on first call

print(quicksort([3, 1, 4, 1, 5, 9, 2, 6]))   # [1, 1, 2, 3, 4, 5, 6, 9]
```

You can give it more context and a specialized bot for harder jobs:

```python
@lazy(
    "Implement a thread-safe LRU cache with TTL support.",
    context="high",                          # include surrounding source as context
    bot=bots.load("architecture_expert.bot"),
)
class TTLCache:
    pass
```

## Where the levels lead

You started with one bot and one function, added a toolkit and saved state, then structured many turns with functional prompts, ran them in parallel, moved into the CLI, and finally let a bot write code for you. Start at whatever level your task needs and climb only as far as it asks you to.
