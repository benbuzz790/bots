# LLM Utilities
LLM Utilities is a toolkit for working with Large Language Models (LLMs), managing conversations with AI assistants, and providing various utility functions for file manipulation by bots.
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
│   ├── reddit_style_GUI.py
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
│   └── *.bot
│   └── ...
├── docs/
└── scripts/
```
## Key Components
### .bot files
These files are JSON formatted representations of conversations, essentially. They also include information about the model used to generate the conversation and the last-known values of some standard parameters. The idea of a .bot is to "save readiness" for a task. I.e. say you'd like to make a bot that complains about Mondays. You can have a conversation with that bot about how you would like it to behave, and save it. Later, you can load that conversation and resume speaking with Garfield.bot, or use it as a "bot function" to get a "one-shot" response from someone who hates Mondays.
### src/auto_terminal.py
The main script that runs an interactive chat application, allowing communication with AI assistants and code execution. It relies on Codey, a bot in the data directory, which I've made familiar with the capabilities of this chat application. Codey can use powershell and python to modify files for you, and in fact has written much of this very file, as well as src, and almost all of the tests.
### src/bot_tools.py 
A collection of utility functions for bots to improve file manipulation reliability.
### src/bots.py
Contains implementations for different AI assistants, including base classes and specific implementations for various providers.
### src/bot_mailbox.py
Manages APIs.
### src/terminal_browser.py
Provides rudimentary terminal-based browsing capabilities.
### src/conversation_node.py
A linked implementation of a conversation, notionally an M-Tree but potentially a directed graph, if you tried hard enough.
### src/reddit_style_GUI.py
For viewing and experimenting with .bot files.
## Testing
The `tests/` directory contains a comprehensive suite of unit tests for the various components of the system. Run these tests to ensure the integrity of the codebase after making changes.
## Usage
1. Ensure all dependencies are installed (Note from Codey: requirements.txt file recommended).
2. Run `src/auto_terminal.py` to start the interactive chat application.
3. Use the available commands to interact with AI assistants, execute code, modify files, automate debugging, etc.
## Development Guidelines
1. (BOTS): Always use functions from `bot_tools.py` for file operations to ensure consistency and safety.
2. (EVERYONE): When adding new features, include corresponding unit tests in the `tests/` directory.
## Code Execution (BOTS)
- Use "epython" and "epowershell" labels for code blocks that should be executed within the chat environment.
- Use regular "python" and "powershell" labels for code demonstrations not intended for execution.
## Contributing
Please read CONTRIBUTING.md (to be created) for details on our code of conduct and the process for submitting pull requests.
## License
This project is licensed under the MIT License - see the LICENSE.md (to be created) file for details.