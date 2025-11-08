# Namshub System - Implementation Summary
## What We Built
A complete namshub system for the bots framework that allows bots to invoke specialized workflows on themselves.
## Components Created
### 1. Core Tool: invoke_namshub.py
Location: `bots/tools/invoke_namshub.py`
Features:
- `invoke_namshub(namshub_name, **kwargs)` - Main invocation tool
- Automatic state management (saves/restores toolkit and system message)
- Dynamic module loading
- Error handling with detailed tracebacks
- Kwargs support for flexible parameterization
### 2. Helper Library: helpers.py
Location: `bots/namshubs/helpers.py`
Utilities:
- `create_toolkit(bot, *tools)` - Standard toolkit swapping
- `instruction_prompts(prompts)` - Add INSTRUCTION prefix
- `instruction_continue_prompt()` - Standard continue prompt
- `chain_workflow(bot, prompts, ...)` - Convenient chain_while wrapper
- `simple_workflow(bot, prompts, ...)` - Simple chain wrapper
- `iterative_workflow(bot, prompt, ...)` - prompt_while wrapper
- `validate_required_params(**params)` - Parameter validation
- `format_final_summary(...)` - Standard summary formatting
### 3. Example Namshubs
#### namshub_of_code_review.py
- Purpose: Thorough code review
- Pattern: Simple sequential workflow
- Tools: Read-only (view, view_dir, python_view)
- Parameters: target_file (required)
#### namshub_of_pull_requests.py
- Purpose: GitHub PR CI/CD workflow
- Pattern: Complex INSTRUCTION-based workflow
- Tools: Full development toolkit
- Parameters: pr_number (required)
#### namshub_of_test_generation.py
- Purpose: Generate pytest tests
- Pattern: INSTRUCTION-based with file generation
- Tools: Full development toolkit
- Parameters: target_file (required), test_file (optional)
#### namshub_of_documentation.py
- Purpose: Generate/improve Python documentation
- Pattern: INSTRUCTION-based with code modification
- Tools: Code viewing and editing
- Parameters: target_file (required)
### 4. Documentation
#### README.md
- Complete overview of namshub system
- Structure and patterns
- Available namshubs
- Design principles
- Technical details
#### QUICKSTART.md
- Quick reference for creating namshubs
- Basic template
- Helper function reference
- Best practices
- Common mistakes to avoid
#### __init__.py
- Module docstring explaining namshubs
## Key Design Decisions
### 1. INSTRUCTION Pattern
For chain_while workflows:
- Prefix prompts with "INSTRUCTION: "
- Use continue prompt: "Focus on the previous INSTRUCTION. Only move on when explicitly instructed."
- Draws attention and keeps bot focused on completing each step
### 2. Toolkit Swapping
- Create fresh bot with only needed tools
- Swap tool_handler (not individual tools)
- Automatic restoration by invoke_namshub
### 3. Parameter Handling
- Accept kwargs in invoke function
- Validate with validate_required_params()
- Provide clear error messages with usage examples
- Support extraction from conversation context as fallback
### 4. Workflow Patterns
Three main patterns:
- Simple sequential (no iteration)
- Chain with iteration (INSTRUCTION pattern)
- Single task with iteration
### 5. Helper Functions
- Encapsulate common patterns
- Reduce boilerplate
- Enforce consistency
- Make namshubs easier to write
## Usage Example
```python
from bots import AnthropicBot
from bots.tools.invoke_namshub import invoke_namshub
# Create bot and add invoke tool
bot = AnthropicBot()
bot.add_tools(invoke_namshub)
# Invoke namshubs
bot.respond("invoke_namshub('namshub_of_code_review', target_file='main.py')")
bot.respond("invoke_namshub('namshub_of_pull_requests', pr_number='123')")
bot.respond("invoke_namshub('namshub_of_test_generation', target_file='utils.py')")
```
## File Structure
```
bots/
├── tools/
│   └── invoke_namshub.py          # Core invocation tool
└── namshubs/
    ├── __init__.py                # Module initialization
    ├── README.md                  # Complete documentation
    ├── QUICKSTART.md              # Quick reference guide
    ├── helpers.py                 # Helper utilities
    ├── namshub_of_code_review.py
    ├── namshub_of_pull_requests.py
    ├── namshub_of_test_generation.py
    └── namshub_of_documentation.py
```
## Next Steps
Potential future namshubs:
- `namshub_of_refactoring` - Code refactoring workflows
- `namshub_of_security_audit` - Security analysis
- `namshub_of_performance` - Performance optimization
- `namshub_of_migration` - Code migration tasks
- `namshub_of_api_design` - API design and validation
## Technical Notes
### State Management
- Original tool_handler saved before execution
- Original system_message saved before execution
- Both restored in finally block (even on error)
- Ensures bot returns to original state
### Dynamic Loading
- Uses importlib.util for dynamic module loading
- Looks for invoke(), run(), or execute() function
- Passes bot and kwargs to invocation function
- Returns tuple (response, node) or just response
### Error Handling
- Comprehensive try/except blocks
- Detailed error messages with tracebacks
- Clear usage examples in error messages
- Graceful fallback for missing parameters
## Inspiration
The name "namshub" comes from Neal Stephenson's *Snow Crash*, where namshubs are powerful "word programs" that directly affect behavior - fitting for specialized workflow modules that transform bot behavior.
