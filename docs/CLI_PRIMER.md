# CLI Primer

The `bots` CLI is an interactive terminal for working with an agent, much like other coding assistants, with one structural difference: the conversation is a tree you can navigate, not a flat transcript you can only scroll. You chat with the bot normally, and you use slash commands to move around that tree, save and restore state, and run the functional prompts from the library without writing any Python.

The reason for the tree is that real work branches. You try one approach, it stalls, and you want to back up and try another without dragging the dead end into everything that follows. In a flat chat you'd either lose the earlier state or pollute the context. Here you return to any earlier point and branch off cleanly; the bot only ever sees the path from the root to where you currently stand.

## Launching

Start a fresh bot:

```bash
python -m bots.dev.cli
```

Or open one you saved earlier, with its whole conversation, tools, and configuration intact:

```bash
python -m bots.dev.cli path/to/mybot.bot
```

Once inside, type a message to talk to the bot, type a slash command to control the session, press Ctrl+C to interrupt a long-running operation, and type `/exit` to quit. Type `/help` at any time for the full command list.

## Moving around the tree

You are always positioned at one node. The basic moves walk the immediate neighborhood: `/up` goes back to the previous message, `/down` moves forward to a reply (it asks which one if the node has several), and `/left` and `/right` step between sibling branches at the same level. `/root` jumps all the way back to the start of the conversation.

`/up` is effectively an undo for the conversation, though not for anything the bot did to your filesystem. A common rhythm is to send a task, dislike the result, `/up` to before it, and try a different phrasing:

```text
You: Refactor this using inheritance.
Bot: [does something you don't like]
You: /up
You: Refactor this using composition instead.
```

When the tree gets deep, two commands jump between the points that matter. `/lastfork` moves up to the nearest node that has more than one reply, and `/nextfork` searches downward to the next one. Forks are where you made a choice, so these let you hop between decision points instead of stepping one node at a time.

`/label` turns a node into a named bookmark. Run it bare to list your labels, give it a name to bookmark the current node, and use `goto` to jump back:

```text
/label                    # list all labels
/label baseline           # bookmark the current node as "baseline"
/label goto baseline      # jump back to it
```

Labels make branching explorations manageable: bookmark a hard-won state, try something risky, and return instantly if it doesn't work out.

`/leaf` shows the endpoints of the tree, that is, every branch you've carried to a conclusion. Run it bare to list the leaves with previews, or give it a number to jump to one:

```text
/leaf        # list every endpoint below you
/leaf 2      # jump to leaf #2
```

## Letting the bot work on its own

`/auto` turns the current bot loose. After it responds, if it used any tools the CLI automatically sends "ok", and the bot keeps going, turn after turn, until it finally responds without using a tool. This is the interactive twin of the `prompt_while` pattern, and it's how you hand off a multi-step job. Press ESC to interrupt.

```text
You: Find and fix every failing test in this repo.
You: /auto
Bot: [runs tests, fixes one, continues...]
Bot: All tests pass now.   # no tool used, so /auto stops
```

## Running functional prompts

The library's functional prompts are available without code through `/fp`, which opens a wizard. It lists the patterns, asks for the prompts each one needs, and asks for a stop condition where relevant. So you can run a parallel branch across three files, or a `prompt_while` loop on a single task, entirely from the terminal.

```text
You: /fp
System: Choose a functional prompt:
  1. chain
  2. branch
  3. prompt_while
  4. par_branch_while
  ...
You: 4
System: Enter prompts (one per line, blank line to finish):
  Create a Flask endpoint for users
  Create a Flask endpoint for products
  Create a Flask endpoint for orders

System: Stop condition? tool_not_used
# the three endpoints are built in parallel, each as its own branch
```

`/broadcast_fp` is the same wizard, but it applies your chosen pattern to every leaf of the tree at once. After the example above, you could broadcast a single follow-up to all three new branches:

```text
You: /broadcast_fp
System: Choose a functional prompt: single_prompt
You: Add input validation and error handling.
# every endpoint gets the same treatment
```

`/combine_leaves` merges the endpoints below your current node into one result using a recombinator. `concatenate` simply joins them; `llm_merge` has a bot synthesize them into a unified answer; `llm_vote` has a bot pick the best one; and `llm_judge` has a bot rank them with reasoning. Use it to pull several parallel explorations back together:

```text
You: /combine_leaves
System: Choose a recombinator:
  1. concatenate
  2. llm_merge
  3. llm_vote
  4. llm_judge
You: 2
Bot: [a single review synthesized from all the branches]
```

## Saving, loading, and undoing

`/save` writes the whole bot to a `.bot` file, including the entire conversation tree, every tool as source code, and the configuration; `/load` restores it. Loading drops you at the most recent node of the saved conversation. Give either a filename, or run it bare to be prompted.

```text
/save my_helper.bot
/load my_helper.bot
```

For lighter-weight safety within a session, the CLI keeps a backup of the bot state. `/backup` takes a snapshot on demand, `/backup_info` reports what's stored, and `/restore` rolls back to it. `/undo` is a shorthand for `/restore`, handy right after a step you'd rather take back.

If the bot is editing real files, `/auto_stash` adds a layer of protection by creating a git stash before each of your messages, with an AI-generated description, so you can experiment and roll the working tree back. `/load_stash` restores a specific stash by index or name.

```text
/auto_stash          # toggle automatic git stashing on
/load_stash 0        # restore the most recent stash
```

## A reusable prompt library

Prompts you type often can be saved and recalled. `/s` saves a prompt (your last message, or text you give it), and `/p` searches your saved prompts and pre-fills the match into your input so you can edit it before sending. `/r` lists your most recent prompts, and `/d` deletes one.

```text
/s Review this code for race conditions and report each with a line number.
/p race            # find and pre-fill the saved "race conditions" prompt
```

## Tools and models

`/add_tool` loads a Python file's functions into the running bot as tools, so you can extend a bot mid-session without restarting. `/models` prints every model the library knows, with its provider, a rough capability rating, its token limit, and its cost. `/switch` changes the current bot's model; with no argument it lists the models available from the current provider, and with one it switches.

```text
/models              # see everything available, with cost and capability
/switch              # list this provider's models
/switch claude-opus-4-6
```

## Display and configuration

By default the CLI is verbose: it shows each tool request with its arguments, the tool's result, and the API metrics (tokens, cost, duration) after every response, which is what you want while learning or debugging. `/quiet` hides all of that and shows only the bot's replies, and `/verbose` turns it back on. `/clear` clears the screen, and `/config` shows or changes session settings such as the color mode. See [Cost Tracking](observability/COST_TRACKING.md) for what the metrics mean.

## A worked example

Suppose you want to review a codebase from several angles and then merge the findings. Read the code once, bookmark that state, fan out into independent reviews, then recombine them:

```text
You: Read every Python file under src/ and get oriented.
Bot: [reads the files]
You: /label loaded

You: /fp
System: Choose: branch
System: Enter prompts:
  Review for security vulnerabilities.
  Review for performance problems.
  Review for maintainability.
# three independent reviews, each from the same loaded context

You: /leaf            # browse the three reviews
You: /label goto loaded
You: /combine_leaves
System: Choose: llm_merge
Bot: [one prioritized review combining all three perspectives]
```

The shared "loaded" context was paid for once, the three reviews never contaminated each other, and the merge produced a single answer, all without leaving the terminal.

## Command reference

Navigation:

| Command | Effect |
| --- | --- |
| `/up`, `/down` | Move to the parent, or to a reply |
| `/left`, `/right` | Move between sibling branches |
| `/root` | Jump to the start of the conversation |
| `/lastfork`, `/nextfork` | Jump to the nearest branch point up or down |
| `/label [name\|goto name]` | List, create, or jump to a bookmark |
| `/leaf [n]` | List the endpoints, or jump to one |

Working with the bot:

| Command | Effect |
| --- | --- |
| `/auto` | Let the bot work until it stops using tools |
| `/fp` | Run a functional prompt via a wizard |
| `/broadcast_fp` | Apply a functional prompt to every leaf |
| `/combine_leaves` | Merge the endpoints below you with a recombinator |

State and safety:

| Command | Effect |
| --- | --- |
| `/save [file]`, `/load [file]` | Save or load the whole bot |
| `/backup`, `/restore`, `/backup_info`, `/undo` | In-session state snapshots |
| `/auto_stash`, `/load_stash [id]` | Git stashing before each message |

Prompts, tools, and models:

| Command | Effect |
| --- | --- |
| `/s`, `/p`, `/r`, `/d` | Save, find, list, and delete saved prompts |
| `/add_tool` | Add a Python file's functions as tools |
| `/models`, `/switch [model]` | List models, or change the current one |

Display and session:

| Command | Effect |
| --- | --- |
| `/verbose`, `/quiet` | Show or hide tool details and metrics |
| `/clear`, `/config` | Clear the screen, or view/change settings |
| `/help`, `/exit` | Show all commands, or quit |
