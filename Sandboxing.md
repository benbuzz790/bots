# Sandboxing Considerations for Bots
## Overview
This document outlines sandboxing considerations for the bots library, specifically for the `execute_python` and `execute_powershell` tools that allow LLM agents to execute arbitrary code.
## Current State
The bots CLI provides two powerful execution tools:
- **`execute_python`** - Executes arbitrary Python code in a subprocess
- **`execute_powershell`** - Executes arbitrary PowerShell commands in a stateful session
Both tools are currently **unrestricted** and can:
- Access/modify any files on the system
- Make network calls
- Execute system commands
- Access environment variables and credentials
## Key Finding: Two Different Sandboxing Concerns
### 1. `execute_python` - Sandbox the User Code
The `execute_python` function is **trusted code** that creates a wrapper and subprocess. What needs sandboxing is the **user-provided Python code** that gets executed within that subprocess.
**Sandboxing approach:**
- AST-based validation (parse and reject dangerous operations before execution)
- Restricted imports (whitelist/blacklist)
- Filesystem restrictions (limit file access to specific directories)
- Restricted builtins (remove dangerous functions like `open`, `eval`, `exec`, `__import__`)
- Network restrictions (optional - block socket operations)
### 2. `execute_powershell` - Sandbox the PowerShell Commands
The `execute_powershell` function and `PowerShellManager` class are **trusted Python code** that manage PowerShell sessions. What needs sandboxing is the **PowerShell commands** that get sent to the session.
**Important:** You cannot sandbox the Python code managing PowerShell sessions - it needs full privileges to manage subprocesses, threads, and I/O pipes.
**Sandboxing approach:**
- Command filtering (block dangerous cmdlets like `Remove-Item`, `Invoke-Expression`)
- Path restrictions (only allow operations in certain directories)
- Execution policy enforcement
- Command validation before sending to PowerShell
## Why Not Wrap PowerShell in Python's exec()?
This approach was considered but has significant drawbacks:
### Cons:
1. **Loss of statefulness** - The current `execute_powershell` maintains a persistent session where you can `cd`, set variables, and activate virtual environments. Wrapping each call would make them isolated.
2. **Performance overhead** - Would spawn: Python GÂ∆ Python subprocess GÂ∆ PowerShell subprocess (instead of reusing existing session)
3. **Complexity** - Would need to write Python code that calls PowerShell, with escaping challenges
4. **Doesn't solve the problem** - The Python wrapper managing PowerShell is trusted code; it's the PowerShell commands that need restriction
## Available Sandboxing Libraries
### For Python:
1. **RestrictedPython** - Restricts Python code execution by compiling with limited builtins
2. **codejail** (by edX) - Uses AppArmor on Linux for OS-level sandboxes
3. **Custom AST validation** - Parse code and reject dangerous patterns
4. **seccomp filters** (Linux only) - Block system calls at kernel level
### For PowerShell:
1. **Constrained Language Mode** - PowerShell's built-in restricted mode
2. **Command allowlisting/blocklisting**
3. **AppLocker** or **Windows Defender Application Control** (enterprise)
## Recommended Approach
### Multi-layered security:
1. **For `execute_python`:**
   - AST validation to reject dangerous operations
   - Restricted imports (whitelist safe modules)
   - Custom builtins dictionary (remove dangerous functions)
   - Filesystem path restrictions
2. **For `execute_powershell`:**
   - Command validation before execution
   - Dangerous cmdlet blocklist
   - Path restrictions for file operations
   - Consider limited statefulness for better security
3. **Shared configuration:**
   - Single configuration file defining allowed operations
   - Consistent security policies across both tools
   - Audit logging for all executed commands
## Implementation Status
**Not yet implemented** - This document serves as design notes for future sandboxing work.
## References
- RestrictedPython: https://github.com/zopefoundation/RestrictedPython
- edX codejail: https://github.com/openedx/codejail
- Python AST module: https://docs.python.org/3/library/ast.html
- PowerShell Constrained Language Mode: https://devblogs.microsoft.com/powershell/powershell-constrained-language-mode/
---
*Document created: 2025*
*Last updated: 2025*
