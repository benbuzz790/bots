# bots

**bots built bots.**

`bots` is a Python library for programming *with* language models instead of just prompting them. A bot is a model plus everything that makes it useful in code: its tools, its full conversation history, its configuration, and the ability to save all of that to a file and load it back later. You work with one through a small, predictable interface, and you compose those calls into larger workflows when a single call isn't enough.

## What makes it different

Most agent frameworks store a conversation as a flat list of messages. `bots` stores it as a tree. Every prompt you send is a node, every reply is a child, and you can move to any node and continue from there.

This matters because real work with an agent is rarely a straight line. You try an approach, it doesn't pan out, and you want to go back and try another one without dragging the failed attempt along in the context. A flat list forces a bad trade: either you lose the earlier state, or you keep talking and let the dead end pollute everything that follows. A tree lets you return to any earlier point and branch off in a new direction. The model only ever sees the path from the root to wherever you currently are, so each branch stays clean.

Branching also gives you parallelism for free. A common pattern is to spend a few turns building shared context, then split into several branches that each carry that context forward and do independent work at the same time. You will see this throughout the library, from the `branch` functional prompt to the agent's own `branch_self` tool.

The design is emergent. Every feature exists because it solved a real problem while building with the library. `respond()` hides the per-provider API differences. `save()` and `load()` came from getting tired of rebuilding context. `add_tools()` made tool creation trivial: you write a Python function, and that's the whole tool. Functional prompts captured the workflows that kept recurring. The CLI grew out of `bot.chat()` once interactions got complicated enough to need real commands.

## The main interface

Almost everything you do runs through a `Bot` object, and a bot does four things: it responds, it uses tools, it saves and loads, and it copies itself. Once you know those four, you know the library.

### Responding

Create a bot and call `respond`. It sends your message, handles any tool use, and returns the final text.

```python
from bots import AnthropicBot

bot = AnthropicBot()
answer = bot.respond("What's the time complexity of quicksort?")
print(answer)
```

`AnthropicBot()` needs no arguments. It defaults to a current Claude model and reads your key from the `ANTHROPIC_API_KEY` environment variable, so the common case stays a single line. When you need control, the constructor takes it:

```python
from bots import AnthropicBot, Engines

bot = AnthropicBot(
    model_engine=Engines.CLAUDE46_SONNET,
    max_tokens=8000,
    temperature=0.2,
    name="reviewer",
)
```

There are sibling classes for the other providers, `ChatGPT_Bot` for OpenAI and a Gemini bot for Google, and they share the same interface. Swapping providers means swapping the constructor; the rest of your code does not change.

### Tools

A tool is a Python function. You hand the function to the bot, and the bot can call it. You do not write a JSON schema or a wrapper, and you do not register anything. The function's signature becomes the tool's parameters and its docstring becomes the description the model reads, so a clear docstring is the whole interface.

```python
def get_stock_price(ticker: str) -> str:
    """Look up the latest closing price for a stock ticker.

    Use when the user asks about a specific company's share price.

    Parameters:
        ticker (str): The stock symbol, e.g. "AAPL".

    Returns:
        str: A human-readable price, or an error message.
    """
    ...

bot.add_tools(get_stock_price)
bot.respond("How much is Apple trading at?")  # the bot decides to call get_stock_price
```

`add_tools` is deliberately forgiving about what you pass it. A single function, a list of functions, an imported module, or a path to a `.py` file all work, and you can mix them in one call. Passing a module adds every public function in it at once, which is how you equip a bot with a whole toolkit:

```python
import bots.tools.code_tools as code_tools

bot.add_tools(code_tools)            # adds view(), view_dir(), patch_edit()
bot.respond("Create a Flask app in app.py with a /health route")
```

The library ships with tools for editing code, running terminal commands, browsing the web, and editing Python and Markdown reliably. They are ordinary modules, so you add them exactly the way you would add your own.

### Saving and loading

Calling `save` writes the entire bot to a single `.bot` file: the whole conversation tree, every tool as hashed source code, and all the configuration. `load` brings it back exactly as it was. The file is self-contained and portable, so a bot you build on one machine runs on another with no extra setup.

```python
import bots

bot.respond("Read every file in this repo and summarize the architecture.")
bot.save("repo_expert.bot")

# tomorrow, or on another machine
expert = bots.load("repo_expert.bot")
expert.respond("Now write integration tests for the payment module.")
```

This is what makes context reusable. You pay the cost of teaching a bot about your codebase once, save the result, and start every later session from that primed state instead of explaining everything again.

### Copying

Multiplying a bot by an integer returns that many independent copies, each carrying the full configuration, tools, and conversation so far. This is how you fan one primed bot out into a fleet that works in parallel.

```python
team = expert * 5   # five independent clones, each already knows the repo
```

### Chatting

For a quick back-and-forth in the terminal, `chat()` opens an interactive loop and shows you which tools the bot uses as it works. It's the fastest way to poke at a bot you just built.

```python
bot.chat()   # type your messages; "/exit" ends the session
```

## Functional prompts

A single `respond` call is one turn. Real tasks take many turns in a definite shape: keep going until the work is done, walk through a fixed sequence of steps, or try several approaches side by side. Functional prompts are that shape, captured as composable functions. They separate *what* you want the bot to think about, which lives in your prompts, from *how* the turns are structured, which lives in the function. Because the structure is independent of the content, the same pattern works whether you're fixing bugs, writing prose, or analyzing data.

```python
from bots.flows import functional_prompts as fp
```

### The core loop: `prompt_while`

The single most important pattern is `prompt_while`. It sends a prompt, then keeps prompting the bot to continue until a stop condition is satisfied. The default condition stops as soon as the bot answers without using a tool, which is exactly the agentic loop you want: the bot works, using tools turn after turn, and stops on its own once it has nothing left to do.

```python
responses, nodes = fp.prompt_while(
    bot,
    "Fix every failing test in this project.",
    continue_prompt="ok",
    stop_condition=fp.conditions.tool_not_used,
)
```

The bot runs the tests, edits a file, runs them again, and continues on its own. Between each turn the loop simply says "ok" and lets it keep working. When it finally responds with a summary and no tool call, the loop ends. `prompt_while` returns the list of responses and the list of conversation nodes they live at, so you can inspect or navigate the result.

### A sequence of steps: `chain` and `chain_while`

When a task has a natural order, `chain` runs your prompts one after another in the same conversation, so each step builds on the last.

```python
responses, nodes = fp.chain(bot, [
    "Read the important .md files in this repo.",
    "Run the test suite with a generous timeout.",
    "Write a short report of what's failing and why.",
])
```

`chain_while` is the same idea, except each step gets to run its own agentic loop before moving on. It's a chain of thought where every link is allowed to do real work:

```python
responses, nodes = fp.chain_while(bot, [
    "Check out the repo and read the key modules.",
    "Run the tests.",
    "Open one issue per distinct failure.",
], stop_condition=fp.conditions.tool_not_used)
```

### Trying approaches in parallel: `branch` and `par_branch_while`

`branch` starts several independent conversations from the current point. Each branch sees the same shared context but develops on its own, so the approaches never contaminate each other.

```python
responses, nodes = fp.branch(bot, [
    "Review this module for security problems.",
    "Review this module for performance problems.",
    "Review this module for readability problems.",
])
```

`par_branch_while` does the same but runs the branches at once and lets each one loop until it's done. It's the fast way to apply the same kind of work across many targets:

```python
responses, nodes = fp.par_branch_while(bot, [
    "Refactor auth.py until it's clean.",
    "Refactor api.py until it's clean.",
    "Refactor data.py until it's clean.",
], stop_condition=fp.conditions.tool_not_used)
```

These compose. You can chain several `prompt_while` calls, branch and then recombine the branches into one synthesized answer with `recombine`, or broadcast a single follow-up prompt to every leaf of the tree with `broadcast_to_leaves`. The [Functional Prompts Primer](docs/functional_prompt_primer.md) walks through the full set.

### Functional prompting in earnest: twenty questions

The `continue_prompt` and `stop_condition` arguments are not limited to fixed strings and the built-in conditions. They are just functions, which means the logic that drives the loop can be anything you can write in Python, including another bot. [`examples/20_questions.py`](examples/20_questions.py) uses this to turn `prompt_while` into a two-player game.

One bot is the guesser. It asks a yes-or-no question each turn and tries to identify a secret word. The trick is the `continue_prompt`: instead of a canned "ok", it is a function that spins up a second, cheaper bot to act as the judge. The judge reads the guesser's latest question, answers it truthfully about the secret word, and that answer becomes the guesser's next prompt. The loop stops when the judge confirms the guess.

```python
from bots import AnthropicBot, Engines
from bots.flows.functional_prompts import prompt_while

word = input("Pick a thing: ")
guesser = AnthropicBot(model_engine=Engines.CLAUDE45_SONNET, temperature=1.0)

def judge(bot, iteration):
    """Continue prompt: a fresh judge bot answers the guesser's latest question."""
    arbiter = AnthropicBot(model_engine=Engines.CLAUDE45_HAIKU, max_tokens=12, temperature=0)
    question = bot.conversation.content
    return arbiter.respond(
        f"You are a 20-questions judge. The secret thing is '{word}'. "
        f"Reply with only: yes, no, sometimes, 'I don't know', or 'you got it!'. "
        f"Here is the question: {question}"
    )

def solved(bot):
    """Stop condition: end when the judge confirms, with a safety cap on turns."""
    judges_answer = bot.conversation.parent.content if bot.conversation.parent else ""
    return "you got it" in judges_answer.lower() or bot.conversation._node_count() > 40

prompt_while(
    guesser,
    "Let's play 20 questions. You ask, I answer. Ask your first yes/no question.",
    continue_prompt=judge,
    stop_condition=solved,
)
```

Nothing here is special-cased by the library. `prompt_while` runs its ordinary loop; you supplied a `continue_prompt` that happens to call a model and a `stop_condition` that reads the conversation tree. That is the whole point of functional prompts. Once the structure is a plain function argument, you can build a judge, a critic, a voting panel, or a negotiation between two agents out of the same small set of pieces.

## The CLI

For interactive work, the CLI gives you a terminal much like Claude Code, with the conversation tree built in.

```bash
python -m bots.dev.cli
```

The bot comes equipped with tools for editing code, running commands, and managing its own context. Beyond chatting, you navigate the tree directly: `/up`, `/down`, `/left`, and `/right` move between nodes, `/label` bookmarks a node so you can jump back to it, and `/leaf` lists the endpoints you've explored. `/auto` turns the current bot loose to work until it stops using tools, and `/fp` launches a wizard for running any functional prompt interactively. Run `/help` to see everything, and read the [CLI Primer](docs/CLI_PRIMER.md) for the full tour.

## Agents that manage their own context

Because a bot can branch, copy, and save itself, you can hand those same abilities to the agent as tools and let it manage its own context. With the self-management tools loaded, a bot can split itself into parallel branches to tackle independent subtasks (`branch_self`), spin up a focused subagent for a contained job (`subagent`), add new tools to itself mid-task (`add_tools`), or prune parts of its history it no longer needs (`remove_context`). Giving an agent the boring job of managing its own context, rather than doing it for it, *appears to work* well in practice. See [`bots/tools/branch_self.md`](bots/tools/branch_self.md) for the details.

## Installation

```bash
pip install git+https://github.com/benbuzz790/bots.git
```

You'll need Python 3.12 or newer and an API key for whichever provider you use. Set it as an environment variable before you start:

```bash
export ANTHROPIC_API_KEY="..."   # or OPENAI_API_KEY, or GEMINI_API_KEY
```

The [Installation and Quick Start guide](docs/installation_quickstart.md) covers Windows and development setups and walks from a first response up to production workflows.

## Architecture

The library is three layers, each building on the one below it.

**Foundation** (`bots.foundation`) holds the core abstractions: the `Bot` class, the tool handler, and the conversation tree. It defines one provider-agnostic interface and implements it for Anthropic, OpenAI, and Gemini, which is why your code reads the same regardless of which model is behind it.

**Flows** (`bots.flows`) is the functional prompts: `chain`, `branch`, `prompt_while`, and the rest, plus the conditions and recombinators that control them.

**Development** (`bots.dev`) is the CLI and the interactive tooling built on top of the first two layers.

## Documentation

- [Installation and Quick Start](docs/installation_quickstart.md) — setup and a graded tour from basic to advanced
- [CLI Primer](docs/CLI_PRIMER.md) — every command and the workflows they enable
- [Functional Prompts Primer](docs/functional_prompt_primer.md) — the patterns in depth, with recipes
- [Tool Handling](docs/tool_handling.md) — how tools are serialized and restored
- [Python Edit Tool](bots/tools/python_edit.md) — reliable, structure-aware Python editing
- [Branch Self Tool](bots/tools/branch_self.md) — how a bot branches itself
- [Observability Setup](docs/observability/SETUP.md), [Cost Tracking](docs/observability/COST_TRACKING.md), and [Callbacks](docs/observability/CALLBACKS.md) — metrics, tracing, and hooks
- [Contributing Guide](CONTRIBUTING.md) and [Testing Guide](tests/TESTING.md)

## License

MIT. See [LICENSE.txt](LICENSE.txt).

## Status

`bots` is under active development. It's used for real work today, but expect rough edges and changes as it evolves.
