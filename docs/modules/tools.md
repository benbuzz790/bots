# Tools Module

**Module**: `bots/tools/`
**Version**: 3.0.0

## Overview

Bot tools for code editing, execution, and terminal operations

## Architecture

```
tools/
├── __init__.py
    ├── beyond_reach.py
    ├── cathedral_bells.py
    ├── cotton_club_stomp.py
    ├── double_helix.py
    ├── first_light.py
    ├── impossible_dream.py
    ├── lightning_fingers.py
    ├── maple_leaf_sprint.py
    ├── perpetual_motion.py
    └── ... (14 more files)
```

## Key Components

*Documentation in progress*


## Usage Examples

```python
from bots.foundation import ClaudeBot
from bots.tools import python_view, python_edit

# Create a bot with tools
bot = ClaudeBot(tools=[python_view, python_edit])

# Bot can now view and edit Python files
response = bot("Show me the main function in app.py")
```

## API Reference

### Classes and Functions

| Name | Type | Description |
|------|------|-------------|
| `play_beyond_reach` | Function | Play the Beyond Reach composition. |
| `play_cathedral_bells` | Function | Play the Cathedral Bells composition. |
| `play_cotton_club_stomp` | Function | Play the Cotton Club Stomp composition. |
| `play_double_helix` | Function | Play the Double Helix composition. |
| `play_first_light` | Function | Play the First Light composition. |
| `play_impossible_dream` | Function | Play the Impossible Dream composition. |
| `play_lightning_fingers` | Function | Play the Lightning Fingers composition. |
| `play_maple_leaf_sprint` | Function | Play the Maple Leaf Sprint composition. |
| `play_perpetual_motion` | Function | Play the Perpetual Motion composition. |
