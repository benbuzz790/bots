# LLM Utilities

LLM Utilities is a comprehensive toolkit for working with Large Language Models (LLMs), managing
conversations with AI assistants, and providing various utility functions for file manipulation
and terminal interactions.
## Project Structure
```
llm-utilities/
├── src/
│   ├── auto_terminal.py
│   ├── bot_mailbox.py
│   ├── bot_tools.py
│   ├── bots.py
│   ├── conversation_node.py
│   ├── terminal_browser.py
│   └── ...
├── tests/
│   ├── test_auto_terminal.py
│   ├── test_bot_mailbox.py
│   ├── test_bot_tools.py
│   ├── test_bots.py
│   ├── test_code_blocks.py
│   └── test_terminal_browser.py
├── data/
│   ├── context.txt
│   └── mailbox_log.txt
├── docs/
└── scripts/
```
## Key Components
### src/auto_terminal.py
The main script that runs an interactive chat application, allowing communication with AI assistants and code execution.
### src/bot_tools.py 
A collection of utility functions for file manipulation, including inserting, replacing, and deleting content in files.
### src/bots.py
Contains implementations for different AI assistants, including base classes and specific implementations for various providers.
### src/bot_mailbox.py
Manages APIs.
### src/terminal_browser.py
Provides rudimentary terminal-based browsing capabilities.
### src/conversation_node.py
A linked-list based implementation of a conversation.
## Testing
The `tests/` directory contains a comprehensive suite of unit tests for the various components of the system. Run these tests to ensure the integrity of the codebase after making changes.
## Usage
1. Ensure all dependencies are installed (requirements.txt file recommended).
2. Run `src/auto_terminal.py` to start the interactive chat application.
3. Use the available commands to interact with AI assistants, execute code, and manage conversations.
## Development Guidelines
1. Always use functions from `bot_tools.py` for file operations to ensure consistency and safety.
2. When adding new features, include corresponding unit tests in the `tests/` directory.
## Code Execution
- Use "epython" and "epowershell" labels for code blocks that should be executed within the chat environment.
- Use regular "python" and "powershell" labels for code demonstrations not intended for execution.
## Contributing
Please read CONTRIBUTING.md (to be created) for details on our code of conduct and the process for submitting pull requests.
## License
This project is licensed under the MIT License - see the LICENSE.md (to be created) file for details.