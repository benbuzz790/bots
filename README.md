# bots

**bots built bots**

## What This Is

Most agent frameworks treat conversations as lists of messages. This one treats them as trees.
Why? Because when you're working with an agent, you need to explore. Try different approaches. Backtrack when something doesn't work. Branch to test ideas in parallel. A linear conversation forces you to either lose context or pollute it with failed attempts.
Trees let you explore without losing your place. Every message is a node. Every response creates a branch. You can navigate back to any point and try something different. The agent only sees the path from root to your current position, so context stays clean.
This structure enables something more interesting: agents that manage their own context. An agent can branch itself to explore multiple approaches in parallel. It can navigate its own conversation tree. It can save its stateâ€”complete with tools and contextâ€”and resume later.
The framework emerged from building with it. Every feature exists because it solved a real problem during development. `respond()` wraps API complexity. `save/load` eliminates context repetition. `add_tools()` makes tool creation trivialâ€”just write a Python function. Functional prompts automate common agent workflows. The CLI grew from `chat()` when interactions got complex enough to need dedicated commands. Namshubs package complete workflows because even with the CLI, certain patterns kept repeating.
This is a tool for programming with agents, not just prompting them.

## Getting Started

The simplest entry point:

```python
from bots import AnthropicBot
bot = AnthropicBot()
response = bot.respond("What's the time complexity of quicksort?")
print(response)
```

That's it. `respond()` sends a message and returns the text response. Everything else builds from here.
Add tools by passing Python functions or modules:

```python
import bots.tools.code_tools as code_tools
bot = AnthropicBot()
bot.add_tools(code_tools)
response = bot.respond("Create a Flask app in app.py")
```

The agent can now call those tools. You don't write schemas or wrappersâ€”just pass the functions.
Save the bot's state when you want to preserve context:

```python
bot.save("my_bot.bot")
```

Load it later:

```python
import bots
bot = bots.load("my_bot.bot")
bot.respond("Continue where we left off")
```

The saved bot includes its conversation tree, tools, and configuration. It's completely portable.

## The CLI

For interactive work, use the CLI:

```bash
python -m bots.dev.cli
```

This gives you a terminal interface similar to Claude Code, but with tree navigation built in. The agent has tools for code editing, file operations, and context management.
Try these commands:

- `/help` - see all commands
- `/save filename` - save current state
- `/load filename` - load a saved bot
- `/up`, `/down`, `/left`, `/right` - navigate the conversation tree
- `/label name` - mark the current node for later reference
- `/leaf` - jump to a leaf node and continue from there
The CLI lets you work with the tree structure directly. Branch to explore different approaches, then navigate back to compare results.

## Functional Prompts

When you're programming with agents (not just chatting), you need patterns for structured reasoning. Functional prompts provide these.
The most important pattern is `prompt_while`â€”it lets an agent work iteratively until a task is complete:

```python
from bots.flows import functional_prompts as fp
# Agent works in a loop until it stops using tools
responses, nodes = fp.prompt_while(
    bot,
    "Fix all the bugs in main.py",
    continue_prompt="Keep going",
    stop_condition=fp.conditions.tool_not_used
)
```

This is the core agentic workflow. The agent keeps working, using tools as needed, until the condition is met.
For sequential reasoning, use `chain`:

```python
# Execute prompts in sequence, building context
responses, nodes = fp.chain(bot, [
    "Analyze the codebase structure",
    "Identify the main entry points",
    "Suggest improvements to the architecture"
])
```

These patterns compose. You can chain multiple `prompt_while` calls, branch to explore different approaches, or run the same workflow across multiple files in parallel:

```python
# Run the same workflow on multiple files in parallel
responses, nodes = fp.par_branch_while(bot, [
    "Refactor auth.py until it's clean",
    "Refactor api.py until it's clean",
    "Refactor data.py until it's clean"
], stop_condition=fp.conditions.said_DONE)
```

Functional prompts separate "what to think about" from "how to think about it." The patterns are language-agnosticâ€”they work the same way regardless of what you're asking the agent to do.

## Namshubs

When you find yourself writing the same functional prompt sequences repeatedly, package them as a namshub. A namshub is a complete workflow: system message, tools, and functional prompts bundled together.
From the CLI:

```text\n>>> Please invoke the namshub of pull requests for PR #123
```

The agent loads the PR review workflow, executes it, then returns control to the main conversation. Namshubs are pre-written tasks that any agent can invoke.
The name comes from Snow Crashâ€”namshubs "reprogram" the agent temporarily for a specific task, then restore its original state.

## Why Trees Matter

The tree structure isn't just an implementation detailâ€”it's the primary interface for working with agents.
When you branch, you're not just creating parallel conversations. You're exploring a decision space. Each branch represents a different approach, a different set of assumptions, a different line of reasoning.
When you navigate, you're not just moving through history. You're choosing which context to build on. The agent only sees the path from root to your current position, so you control exactly what it knows.
When you save, you're not just preserving a conversation. You're capturing a complete agent stateâ€”tools, context, and position in the exploration space. You can share it, resume it, or fork it.
This makes agents more like development tools than chat interfaces. You explore with them, backtrack when needed, and build up context incrementally.

## Installation

```bash
pip install git+https://github.com/benbuzz790/bots.git
```

Set up your API key:

- [OpenAI](https://platform.openai.com/docs/quickstart)
- [Anthropic](https://docs.anthropic.com/en/docs/initial-setup#set-your-api-key)

## Architecture

The framework has three layers:
**Foundation** (`bots.foundation`): Core abstractions for bots, tools, and conversations. Provider-agnostic interface with implementations for OpenAI, Anthropic, and Gemini.
**Flows** (`bots.flows`): Functional prompts for structured reasoning. Patterns like chain, branch, iterate, and parallel dispatch.
**Development** (`bots.dev`): CLI for interactive work with tree navigation, state management, and real-time tool display.

## Documentation

- [Installation Guide](installation_quickstart.md) - Detailed setup instructions
- [CLI Primer](CLI_PRIMER.md) - Complete guide to CLI commands and workflows
- [Functional Prompts Primer](functional_prompt_primer.md) - Deep dive into functional prompt patterns
- [Contributing Guide](CONTRIBUTING.md) - How to contribute to the project
- [Testing Guide](TESTING.md) - Running and writing tests

### Component Documentation

- [Tool Handling](bots/foundation/tool_handling.md) - How tool serialization works
- [Python Edit Tool](bots/tools/python_edit.md) - Reliable Python code editing
- [Branch Self Tool](bots/tools/branch_self.md) - Agent self-branching capabilities
- [Namshubs Guide](bots/namshubs/README.md) - Creating and using namshubs
- [Namshubs Quickstart](bots/namshubs/QUICKSTART.md) - Getting started with namshubs

### Observability

- [Observability Setup](docs/observability/SETUP.md) - Configuring metrics and tracing
- [Cost Tracking](docs/observability/COST_TRACKING.md) - Monitoring API costs
- [Callbacks](docs/observability/CALLBACKS.md) - Using callback hooks

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE.md](LICENSE.md)

## Status

This framework is under active development. While it's being used successfully for real projects, expect changes and bugs.
