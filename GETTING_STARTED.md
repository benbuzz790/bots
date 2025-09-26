# Getting Started with Bots Framework

## Quick Start

Welcome to the Bots Framework! This guide will help you get up and running quickly.

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Git (for cloning the repository)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd bots-framework
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your environment:
```bash
python setup.py develop
```

### Your First Bot

Create a simple bot in just a few lines:

```python
from bots import Bot

# Initialize your bot
bot = Bot(name="MyFirstBot")

# Add a simple greeting function
@bot.tool
def greet(name: str) -> str:
    return f"Hello, {name}! Welcome to the Bots Framework!"

# Run your bot
if __name__ == "__main__":
    result = bot.run("greet", name="World")
    print(result)
```

### Next Steps

- Check out the [examples/](examples/) directory for more complex examples
- Read the [API Reference](API_REFERENCE.md) for detailed documentation
- Explore the [Project Overview](PROJECT_OVERVIEW.md) to understand the architecture

### Common Use Cases

1. **Automation Scripts**: Create bots to automate repetitive tasks
2. **Data Processing**: Build bots that process and transform data
3. **API Integration**: Connect different services through bot workflows
4. **Testing**: Use bots for automated testing scenarios

### Getting Help

- Check the [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines
- Review existing tests in the `tests/` directory
- Look at work orders in `_work_orders/` for current development priorities
