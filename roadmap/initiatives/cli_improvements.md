# CLI Improvements Initiative

**Status:** Ongoing ??  
**Last Updated:** November 8, 2025

## Overview

Continuous enhancement of the CLI user experience through better visual presentation, new commands, configuration options, and quality-of-life improvements. The CLI is the primary interface for most users, making these improvements critical for adoption and satisfaction.

## Related Items

- **Item 2:** Make CLI Prettier - ?? PARTIAL (Metrics added, more work remains)
- **Item 5:** Ensure CLI Haiku Bots Match Provider - ? NOT STARTED
- **Item 6:** Configure CLI More Thoroughly - ? NOT STARTED
- **Item 40:** .bot File Association - ? NOT STARTED
See also: [Phase 2: Features](../active/phase2_features.md#item-6), [Phase 3: Enhancement](../active/phase3_enhancement.md#item-2)

## Recent Improvements ?

### Context Management Tools (PR #125, Oct 2025)

- **list_context:** Display bot messages with labels for removal
- **remove_context:** Remove bot-user message pairs by label
- **Auto-prompt:** Context reduction when token threshold exceeded
- **Session metrics:** Token/cost tracking and display

### Fork Navigation (PR #170, Nov 2025)

- **/prev_fork:** Navigate to previous conversation fork
- **/next_fork:** Navigate to next conversation fork
- **Interactive prompt loading:** Fuzzy search, previews, numeric selection

### Dynamic Prompts (PR #161, Oct 2025)

- **Dynamic prompts infrastructure:** Foundation for adaptive, state-aware prompts
- **policy() method:** Enable sophisticated prompt strategies

### Command Improvements (PR #161, Oct 2025)

- **/auto mode:** Properly displays user messages and metrics
- **/p command:** Shows best match first, defaults to it
- **/d command:** Delete prompts from prompt library
- **/r command:** Show recent prompts with persistent recency list
- **/add_tool command:** Add tools dynamically during conversation
- **/config enhancements:** Options for auto mode prompts, max_tokens, temperature
- **Multi-command parsing:** Commands like /config set X /auto work correctly

### Metrics Display (PR #124, Oct 2025)

- **Clean metrics summary:** Tokens, cost, response time (no verbose traces)
- **Session-wide totals:** Track cumulative usage across conversation
- **Default exporter:** Changed from 'console' to 'none' for cleaner output

## Item 2: Make CLI Prettier (?? PARTIAL)

**Status:** Metrics and session tracking delivered, visual improvements remain

### Completed ?

- Session-wide metrics display (tokens, cost, response time)
- Auto-prompt for context reduction when threshold exceeded
- Clean metrics summary (no verbose traces)

### Remaining Work ?

- **Color coding** for different message types
- **Syntax highlighting** for code in tool results
- **Progress indicators** for long-running operations (see Item 12 - Callbacks)
- **Rich text formatting** (using rich or textual library)
- **Better error message formatting**
- **Visual conversation tree** display

### Implementation Ideas

**Color Coding:**

```python
from colorama import Fore, Style
# User messages: Blue
print(f"{Fore.BLUE}User: {message}{Style.RESET_ALL}")
# Bot messages: Green
print(f"{Fore.GREEN}Bot: {message}{Style.RESET_ALL}")
# Tool calls: Yellow
print(f"{Fore.YELLOW}Tool: {tool_name}{Style.RESET_ALL}")
# Errors: Red
print(f"{Fore.RED}Error: {error}{Style.RESET_ALL}")
```

**Syntax Highlighting:**

```python
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import TerminalFormatter
# Highlight code in tool results
highlighted = highlight(code, PythonLexer(), TerminalFormatter())
print(highlighted)
```

**Progress Indicators:**

```python
from rich.progress import Progress
with Progress() as progress:
    task = progress.add_task("[cyan]Generating response...", total=100)
    # Update progress as bot works
```

## Item 5: CLI Haiku Bots Match Provider (? NOT STARTED)

**Goal:** Initialize utility bots from same provider as main CLI bot
**Current Issue:**

- CLI uses one provider (e.g., Anthropic)
- Utility bots (for quick tasks) may use different provider
- Inconsistent experience and unnecessary API key requirements
**Provider Model Tiers:**
- **Anthropic:** Sonnet (flagship) / Haiku (fast)
- **OpenAI:** GPT-4 Turbo (flagship) / GPT-4o-mini (fast)
- **Google:** Gemini Pro (flagship) / Gemini Flash (fast)
**Implementation:**

```python
# Detect main bot's provider
if isinstance(main_bot, AnthropicBot):
    utility_bot = AnthropicBot(model="claude-3-5-haiku-20241022")
elif isinstance(main_bot, OpenAIBot):
    utility_bot = OpenAIBot(model="gpt-4o-mini")
elif isinstance(main_bot, GeminiBot):
    utility_bot = GeminiBot(model="gemini-1.5-flash")
```

**Benefits:**

- Consistent provider experience
- Single API key needed
- Cost optimization (use fast models for utility tasks)

## Item 6: Configure CLI More Thoroughly (? NOT STARTED)

**Goal:** Comprehensive configuration system with plugin support
**Configuration Categories:**

### 1. Display Settings

- Color scheme (light/dark/custom)
- Syntax highlighting on/off
- Progress indicators on/off
- Metrics display format
- Conversation tree visualization

### 2. Behavior Settings

- Auto-save frequency
- Context reduction threshold
- Default continue prompt
- Tool execution confirmation
- Error handling strategy

### 3. Provider Settings

- Default provider (Anthropic/OpenAI/Google)
- Default models (flagship/fast)
- API key management
- Rate limiting
- Cost budgets

### 4. Plugin System

- Load custom tools from directory
- Load custom namshubs
- Load custom callbacks
- Plugin discovery and management
**Configuration File Format:**

```yaml
# ~/.bots/config.yaml
display:
  colors: true
  syntax_highlighting: true
  progress_indicators: true
  metrics_format: "compact"
behavior:
  autosave: true
  autosave_frequency: 300  # seconds
  context_threshold: 100000  # tokens
  confirm_tool_execution: false
provider:
  default: "anthropic"
  models:
    flagship: "claude-3-5-sonnet-20241022"
    fast: "claude-3-5-haiku-20241022"
  cost_budget: 10.00  # USD per session
plugins:
  tools_dir: "~/.bots/plugins/tools"
  namshubs_dir: "~/.bots/plugins/namshubs"
  auto_load: true
```

**CLI Commands:**
`ash

# View configuration

bots config show

# Set configuration value

bots config set display.colors true

# Reset to defaults

bots config reset

# Load plugin

bots plugin load my_custom_tools.py
`

## Item 40: .bot File Association (? NOT STARTED)

**Goal:** Double-click .bot files to open in terminal with CLI loaded
**Current State:**

- CLI supports loading: python -m bots.dev.cli [filepath]
- No file association - must manually type command
- Double-clicking .bot files doesn't work
**Implementation Approach:**

### Phase 1: Console Entry Point

```python
# setup.py
setup(
    ...
    entry_points={
        'console_scripts': [
            'bbots-cli=bots.dev.cli:main',
        ],
    },
)
```

Creates bots-cli command available system-wide.

### Phase 2: Platform-Specific File Associations

**Windows:**

```reg
; bots-file-association.reg
Windows Registry Editor Version 5.00
[HKEY_CLASSES_ROOT\.bot]
@="BotsFile"
[HKEY_CLASSES_ROOT\BotsFile]
@="Bots Conversation File"
[HKEY_CLASSES_ROOT\BotsFile\shell\open\command]
@="cmd.exe /k bbots-cli \"%1\""
```

**macOS:**

```xml
<!-- Info.plist -->
<key>CFBundleDocumentTypes</key>
<array>
    <dict>
        <key>CFBundleTypeName</key>
        <string>Bots Conversation File</string>
        <key>CFBundleTypeExtensions</key>
        <array>
            <string>bot</string>
        </array>
        <key>CFBundleTypeRole</key>
        <string>Editor</string>
    </dict>
</array>
```

**Linux:**

```desktop
# bots.desktop
[Desktop Entry]
Name=Bots CLI
Exec=x-terminal-emulator -e bbots-cli %f
Type=Application
MimeType=application/x-bot
```

### Phase 3: Automated Installer

```python
# install_file_associations.py
import platform
import subprocess
def install_associations():
    system = platform.system()
    if system == "Windows":
        install_windows_association()
    elif system == "Darwin":
        install_macos_association()
    elif system == "Linux":
        install_linux_association()
```

**Benefits:**

- Better user experience
- Faster workflow (double-click vs typing command)
- More "native" application feel

## Success Metrics

### Item 2 (CLI Prettier)

- ? Metrics display implemented
- ? Session tracking implemented
- ? Color coding implemented
- ? Syntax highlighting implemented
- ? Progress indicators implemented
- ? Rich text formatting implemented

### Item 5 (Haiku Bots)

- ? Utility bots match main bot provider
- ? Cost optimization achieved
- ? Single API key workflow

### Item 6 (Configuration)

- ? Configuration file format defined
- ? Configuration loading/saving implemented
- ? CLI config commands implemented
- ? Plugin system implemented

### Item 40 (File Association)

- ? Console entry point created
- ? Windows association working
- ? macOS association working
- ? Linux association working

## Next Steps

1. **Complete Item 2 (CLI Prettier):**
   - Add color coding with colorama
   - Add syntax highlighting with pygments
   - Integrate progress indicators with callbacks
   - Consider rich library for advanced formatting
2. **Implement Item 5 (Haiku Bots):**
   - Detect main bot provider
   - Initialize utility bots with matching fast model
   - Test with all 3 providers
3. **Design Item 6 (Configuration):**
   - Define configuration file format
   - Implement configuration loading/saving
   - Add CLI config commands
   - Design plugin system architecture
4. **Implement Item 40 (File Association):**
   - Add console entry point to setup.py
   - Create platform-specific association files
   - Write installation script
   - Test on all platforms

---
**Initiative Owner:** Core Team  
**Priority:** MEDIUM-HIGH  
**Related Initiatives:** [Observability](observability.md), [Cross-Platform](cross_platform.md)
