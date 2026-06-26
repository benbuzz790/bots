# Functional Prompts Primer

A single call to `bot.respond()` is one turn of conversation. Most real work takes many turns arranged in a definite shape: keep going until the job is done, move through a fixed sequence of steps, or try several approaches at once and compare them. Functional prompts are those shapes, written as ordinary Python functions you call on a bot.

Their value comes from one idea: they separate *what* the bot thinks about from *how* the turns are structured. The "what" lives in the prompt strings you pass. The "how" lives in the function. Because the two are independent, the same `prompt_while` that fixes failing tests can write a novel chapter, and the same `branch` that reviews code can weigh three product decisions. You learn the pattern once and reuse it everywhere.

Everything here lives in one module. The examples assume you've imported it and have a bot ready:

```python
import bots
import bots.flows.functional_prompts as fp

bot = bots.AnthropicBot()
```

## The shape of every functional prompt

Each functional prompt takes a bot as its first argument and returns a tuple of two lists: the responses (strings) and the conversation nodes those responses live at. The nodes let you navigate or inspect the resulting tree afterward.

```python
responses, nodes = fp.chain(bot, ["First step.", "Second step."])
print(responses[-1])   # the bot's last reply
```

Two arguments show up again and again and are worth understanding early, because they are where the power lives. A **stop condition** is a function that takes the bot and returns `True` when iteration should end. A **continue prompt** is what gets sent on each turn after the first; it can be a plain string or a function of `(bot, iteration)` that returns a string. Both are just functions, so anything you can compute in Python can drive the loop, including a call to another bot. The [twenty questions example](#putting-it-together-twenty-questions) below leans on exactly that.

## prompt_while: the core agentic loop

`prompt_while` is the pattern you'll reach for most. It sends a first prompt, then keeps sending the continue prompt until the stop condition is met.

```python
fp.prompt_while(
    bot,
    first_prompt,
    continue_prompt="ok",
    stop_condition=fp.conditions.tool_not_used,
)
```

The default stop condition, `tool_not_used`, ends the loop the moment the bot replies without calling a tool. That captures the natural rhythm of an agent: it works, using tools turn after turn, and stops on its own once it has nothing left to do and simply summarizes. The neutral `"ok"` continue prompt nudges it forward without steering it.

```python
responses, nodes = fp.prompt_while(
    bot,
    "Run the test suite and fix every failure you find.",
    continue_prompt="ok",
    stop_condition=fp.conditions.tool_not_used,
)
```

The bot runs the tests, edits a file, runs them again, and keeps going; the loop quietly says "ok" between turns; and when the bot reports success without touching a tool, it's done.

## chain and chain_while: ordered steps

When a task has a natural order, `chain` runs your prompts in sequence within one conversation, so each step sees everything before it.

```python
responses, nodes = fp.chain(bot, [
    "Read the important .md files in this repo.",
    "Run the tests with a generous timeout.",
    "Summarize what's failing and why.",
])
```

`chain_while` is the same sequence, except each step is allowed its own `prompt_while`-style loop before the chain advances. It's a chain of thought where every link can do real, multi-turn work.

```python
responses, nodes = fp.chain_while(
    bot,
    [
        "Check out the repo and read the key modules.",
        "Run the tests.",
        "Open one issue per distinct failure.",
    ],
    stop_condition=fp.conditions.tool_not_used,
    continue_prompt="ok",
)
```

## branch and the parallel family: many directions at once

`branch` starts several independent conversations from the bot's current position. Every branch inherits the same context but develops separately, so one branch's reasoning never leaks into another's. This is how you compare approaches honestly.

```python
responses, nodes = fp.branch(bot, [
    "Review this module for security problems.",
    "Review this module for performance problems.",
    "Review this module for readability.",
])
```

`par_branch` is `branch` run concurrently across threads; `par_branch_while` is `branch` where each path also loops until its stop condition. Reach for `par_branch_while` when you have several independent jobs that each need real work:

```python
responses, nodes = fp.par_branch_while(
    bot,
    [
        "Refactor auth.py until it's clean.",
        "Refactor api.py until it's clean.",
        "Refactor data.py until it's clean.",
    ],
    stop_condition=fp.conditions.tool_not_used,
    continue_prompt="ok",
)
```

The parallel variants make a copy of the bot per branch for thread safety, and a branch that fails comes back as `None` in the results rather than taking down the whole call. They're fast, but running many at once can hit your provider's rate limits, so scale the width to your quota.

## prompt_for: prompts built from data

When you have a list of items and want one prompt each, `prompt_for` builds the prompts for you from a function. Set `should_branch=True` to run them as independent parallel branches, or leave it `False` to run them sequentially in one conversation.

```python
files = ["auth.py", "api.py", "models.py"]

responses, nodes = fp.prompt_for(
    bot,
    files,
    lambda path: f"Review {path} for security issues.",
    should_branch=True,
)
```

## tree_of_thought and recombine: explore, then synthesize

`tree_of_thought` branches into several perspectives and then merges them into a single answer using a recombinator function you provide. The recombinator takes the lists of responses and nodes and returns one `(response, node)` pair.

```python
def combine(responses, nodes):
    merged = "\n".join(f"- {r}" for r in responses)
    return f"Combined analysis:\n{merged}", nodes[0]

response, node = fp.tree_of_thought(
    bot,
    [
        "Evaluate the technical feasibility.",
        "Analyze the business impact.",
        "Assess the user experience.",
    ],
    combine,
)
```

`recombine` is the synthesis step on its own, so you can branch, inspect the results, and only then decide how to merge them. A recombinator can be as simple as concatenation or can itself call a bot to write a real synthesis:

```python
responses, nodes = fp.branch(bot, [
    "Critique README.md.",
    "Critique setup.py.",
    "Critique the main module.",
])

def summarize_with_bot(responses, nodes):
    combiner = bots.load("summarizer.bot")
    joined = "\n\n".join(responses)
    reply = combiner.respond(
        f"Merge these reviews into one prioritized list of actions:\n\n{joined}"
    )
    return reply, combiner.conversation

final, node = fp.recombine(bot, responses, nodes, summarize_with_bot)
```

## broadcast_to_leaves: one prompt to every endpoint

After you've grown a tree with several branches, `broadcast_to_leaves` sends the same prompt to every leaf at once. It's the natural follow-up to a branching workflow: build several files in parallel, then broadcast "add error handling and tests" to all of them. The `skip` argument takes a list of substrings; any leaf whose content matches is left alone.

```python
fp.broadcast_to_leaves(
    bot,
    "Add error handling and a docstring.",
    skip=[],
    stop_condition=fp.conditions.tool_not_used,
)
```

## par_dispatch: one workflow across a fleet

`par_dispatch` runs any functional prompt across a list of bots in parallel. Build the fleet by multiplying a bot, prime each member with its own role or file, then dispatch the same flow to all of them.

```python
fleet = bots.AnthropicBot() * 3
files = ["auth.py", "api.py", "data.py"]
for member, path in zip(fleet, files):
    member.respond(f"Your file is {path}. Review and debug it after the next message.")

results = fp.par_dispatch(
    fleet,
    fp.chain_while,
    prompt_list=[
        "Find and read your file.",
        "Write thorough tests covering the edge cases.",
        "Run the tests and fix what breaks.",
    ],
    stop_condition=fp.conditions.tool_not_used,
)
```

Because the bots in the list are independent, they can even be different providers, which makes `par_dispatch` a clean way to run the same task on Claude, GPT, and Gemini and compare.

## Stop conditions

A stop condition is any function from a bot to a boolean. The library ships the common ones in `fp.conditions`:

- `tool_not_used` — stop once the bot replies without calling a tool. The default, and the right choice for most agentic tasks.
- `tool_used` — the inverse; stop as soon as a tool is used.
- `said_DONE` and `said_READY` — stop when the bot's reply contains "DONE" or "READY". Useful when you want the bot to signal completion in words.
- `error_in_response` — stop if the reply looks like it hit an error.
- `no_new_tools_used` — stop when a turn introduces no tool the previous turn didn't already use.

Writing your own is just writing a function. This one stops when the bot states a confidence level:

```python
def confident(bot):
    return "99% confident" in bot.conversation.content

fp.prompt_while(
    bot,
    "Optimize this function. Keep going until you're 99% confident it's optimal.",
    continue_prompt="Continue optimizing.",
    stop_condition=confident,
)
```

## Continue prompts, static and dynamic

The continue prompt can be a fixed string, but it can also be a function of `(bot, iteration)`, which lets the message adapt as the loop runs. The `fp.dynamic_prompts` helpers cover the common cases. `static` wraps a constant string, and `policy` picks a message from a list of rules based on the bot's state and the iteration count:

```python
continue_prompt = fp.dynamic_prompts.policy(
    rules=[
        (lambda b, i: i > 8, "You've gone many rounds; wrap up now."),
        (lambda b, i: len(b.conversation.content) > 4000, "Be more concise."),
    ],
    default="ok",
)

fp.prompt_while(bot, "Draft the design doc.", continue_prompt=continue_prompt)
```

## Putting it together: twenty questions

Here is the idea taken seriously. Because both the continue prompt and the stop condition are plain functions, the loop that drives one bot can be steered by another bot. [`examples/20_questions.py`](../examples/20_questions.py) builds a complete two-player game out of a single `prompt_while`.

One bot is the guesser. It asks a yes-or-no question each turn, trying to name a secret word. The continue prompt is the clever part: rather than a canned `"ok"`, it's a function that creates a second, cheaper bot to play judge. The judge reads the guesser's latest question, answers it truthfully about the secret word, and that answer becomes the guesser's next prompt. The stop condition reads the conversation tree to see whether the judge has confirmed the guess.

```python
from bots import AnthropicBot, Engines
from bots.flows.functional_prompts import prompt_while

word = input("Pick a thing: ")
guesser = AnthropicBot(model_engine=Engines.CLAUDE45_SONNET, temperature=1.0)

def judge(bot, iteration):
    """Continue prompt: a fresh judge bot answers the guesser's latest question.

    `bot.conversation.content` is the guesser's most recent message, i.e. its
    question. The judge's reply becomes the next prompt sent to the guesser.
    """
    arbiter = AnthropicBot(model_engine=Engines.CLAUDE45_HAIKU, max_tokens=12, temperature=0)
    question = bot.conversation.content
    return arbiter.respond(
        f"You are a 20-questions judge. The secret thing is '{word}'. "
        f"Reply with only: yes, no, sometimes, 'I don't know', or 'you got it!'. "
        f"The question is: {question}"
    )

def solved(bot):
    """Stop condition: end when the judge confirmed, with a safety cap on turns.

    The judge's last answer is the parent of the guesser's current node, since
    the continue prompt became the guesser's most recent prompt.
    """
    judges_answer = bot.conversation.parent.content if bot.conversation.parent else ""
    return "you got it" in judges_answer.lower() or bot.conversation._node_count() > 40

def show(responses, nodes):
    """Callback: print the exchange after each turn."""
    print("Guesser:", responses[-1])
    print("Judge:  ", nodes[-1].parent.content)

prompt_while(
    guesser,
    "Let's play 20 questions. You ask, I answer. Ask your first yes/no question.",
    continue_prompt=judge,
    stop_condition=solved,
    callback=show,
)
```

Nothing in this is a special game mode. `prompt_while` runs its ordinary loop; you supplied a `continue_prompt` that happens to call a model and a `stop_condition` that happens to read the tree. The callback is the same hook every functional prompt offers for observing progress as it happens. Once the loop's behavior is just function arguments, the same machinery gives you a critic that grades each draft, a panel of judges that votes, or two agents negotiating, all from the pieces in this primer.

## Recipes

**The single agentic task.** The most common use of the whole module is one autonomous loop. Describe the goal and let the bot run.

```python
fp.prompt_while(
    bot,
    "Analyze this codebase and write thorough documentation for it.",
    continue_prompt="ok",
    stop_condition=fp.conditions.tool_not_used,
)
```

**List, then execute in parallel.** Ask the bot to break a job into parallelizable pieces, then run those pieces at once. Having the bot produce the list first keeps every piece anchored to the same plan.

```python
import re

plan = bot.respond(
    "Break this project into 5-7 independent, actionable tasks. "
    "Number them like '1. ...', '2. ...'."
)
numbers = [int(n) for n in re.findall(r"(\d+)\.", plan)]
task_prompts = [f"Do task {n} from this list:\n\n{plan}" for n in numbers]

fp.par_branch_while(
    bot,
    task_prompts,
    stop_condition=fp.conditions.tool_not_used,
    continue_prompt="ok",
)
```

**Iterative refinement.** Keep improving until a quality bar is met. The bar can be a phrase the bot must say, or a separate bot that judges.

```python
def good_enough(bot):
    content = bot.conversation.content.lower()
    return any(word in content for word in ("excellent", "ready to ship"))

fp.prompt_while(
    bot,
    "Write a project proposal. Aim for something you'd ship.",
    continue_prompt="Review it once more and improve the weakest part.",
    stop_condition=good_enough,
)
```

## Practical notes

A few habits make these patterns work better. Keep prompts specific; the same clarity that helps a single `respond` helps every step of a chain. Prefer `"ok"` as a continue prompt when you don't have a reason to steer, because it neither pushes the bot toward more action (as "continue" does) nor toward stopping. Use `tool_not_used` as your default stop condition for agentic work, and reach for a custom condition only when you need a sharper finish line. Finally, remember that the parallel functions can hit rate limits, so match the number of concurrent branches to your provider quota.

## In the CLI

Every pattern here is also available interactively. Inside the CLI, `/fp` opens a wizard that lets you pick a functional prompt, enter its prompts, and choose a stop condition on the spot, while `/broadcast_fp` applies a chosen functional prompt to every leaf of the current tree. See the [CLI Primer](CLI_PRIMER.md) for the full set of commands.
