# Getting Started with Bots Framework

## Introduction

Welcome to the Bots Framework! This tutorial will guide you through the basics of creating and using bots.

## Prerequisites

- Python 3.8 or higher
- Basic understanding of Python programming
- Familiarity with command line interfaces

## Your First Bot

### Step 1: Installation

```bash
pip install -r requirements.txt
```

### Step 2: Create a Simple Bot

```python
from bots import AnthropicBot

# Create a basic bot
my_bot = AnthropicBot(name="HelloBot")

# Add a simple greeting function
from bots.dev.decorators import toolify
@toolify
def greet(name: str) -> str:
    print( f"Hello, {name}! Welcome to the Bots Framework." )
    return "greeting sent successfully"

# Run the bot
if __name__ == "__main__":
    text_response = my_bot.respond("My name is Ben. Greet me.")
    print(text_response)
```

### Step 3: Test Your Bot

Save the code above as `hello_bot.py` and run:

```bash
python hello_bot.py
> Hello, Ben! Welcome to the Bots Framework.
> Claude: Sure, let me use that tool to greet you.
```

## Next Steps

- Explore the examples in the `examples/` directory
