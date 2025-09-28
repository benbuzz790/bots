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
from bots import Bot

# Create a basic bot
my_bot = Bot(name="HelloBot")

# Add a simple greeting function
@my_bot.tool
def greet(name: str) -> str:
    return f"Hello, {name}! Welcome to the Bots Framework."

# Run the bot
if __name__ == "__main__":
    result = my_bot.run("greet", name="World")
    print(result)
```

### Step 3: Test Your Bot
Save the code above as `hello_bot.py` and run:
```bash
python hello_bot.py
```

## Next Steps
- Explore the examples in the `examples/` directory
- Read the API reference in `API_REFERENCE.md`
- Check out advanced features in the documentation

## Common Issues
- Make sure all dependencies are installed
- Check Python version compatibility
- Verify configuration files are properly set up
