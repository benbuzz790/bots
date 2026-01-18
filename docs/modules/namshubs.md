# Namshubs Module

**Module**: `bots/namshubs/`
**Version**: 3.0.0

## Overview

Specialized bot workflows and automation

## Architecture

```
namshubs/
├── __init__.py
├── helpers.py
├── namshub_of_branch_planning.py
├── namshub_of_documentation.py
├── namshub_of_enki.py
├── namshub_of_pull_requests.py
├── namshub_of_roadmap_updates.py
├── namshub_of_unit_testing.py
```

## Key Components

*Documentation in progress*


## Usage Examples

```python
from bots.namshubs import *

# Usage examples coming soon
```

## API Reference

### Classes and Functions

| Name | Type | Description |
|------|------|-------------|
| `create_toolkit` | Function | Merge additional tools into bot's existing toolkit. |
| `instruction_prompts` | Function | Prefix each prompt with 'INSTRUCTION: ' for better attention |
| `instruction_continue_prompt` | Function | Return the standard continue prompt for INSTRUCTION-based wo |
| `chain_workflow` | Function | Execute a chain_while workflow with sensible defaults. |
| `simple_workflow` | Function | Execute a simple chain workflow without iteration. |
| `iterative_workflow` | Function | Execute an iterative workflow with a single prompt. |
| `validate_required_params` | Function | Validate that required parameters are provided. |
| `format_final_summary` | Function | Format a standard final summary for namshub completion. |
| `invoke` | Function | Execute the documentation generation namshub. |
| `invoke` | Function | Execute the Enki workflow to create a new namshub. |
| `invoke` | Function | Execute the PR workflow namshub. |
| `invoke` | Function | Execute the roadmap update workflow. |
| `invoke` | Function | Execute the unit testing workflow to create comprehensive te |
