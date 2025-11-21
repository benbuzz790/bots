# CLI Refactor Branch - Bug Fixes and Improvements to Cherry-Pick
This document lists bug fixes and improvements from the rchive/cli-refactor-attempts branch that should be cherry-picked into main, independent of the larger refactor work.
## 1. Enhanced Backup System
**Location:** ots/dev/cli.py - CLIContext class
**What it does:**
- Complete bot backup system (not just conversation backup)
- Uses bot's built-in copy mechanism (ot * 1) for proper serialization
- Stores metadata (timestamp, reason, conversation depth, token count)
- Supports auto-backup before user messages
- Supports auto-restore on errors
**Key improvements over current system:**
- Current main only backs up conversation nodes
- Archive branch backs up entire bot state (tools, callbacks, configuration)
- Prevents concurrent backups with ackup_in_progress flag
- Allows multiple restores to same checkpoint (doesn't clear backup)
- Better error messages with timestamps and context
**Methods to add:**
- CLIContext.create_backup(reason: str) -> bool
- CLIContext.restore_backup() -> str
- CLIContext.has_backup() -> bool
- CLIContext.get_backup_info() -> str
- CLIContext._get_conversation_depth() -> int
**Config additions:**
- uto_backup: bool - automatically backup before user messages
- uto_restore_on_error: bool - automatically restore on chat errors
**Commands to add:**
- /backup - manually create backup
- /restore - restore from backup
- /backup_info - show backup metadata
- /undo - alias for /restore
## 2. Improved Error Handling in Chat
**Location:** ots/dev/cli.py - _handle_chat() method
**What it does:**
- Try/except around chat execution
- On error, attempts auto-restore if enabled
- Falls back to old conversation backup system if new backup unavailable
- Clear error messages with context
**Current behavior:**
- Errors may leave bot in inconsistent state
- No automatic recovery
**Improved behavior:**
`python
except Exception as e:
    pretty(f"Chat error: {str(e)}", "Error", ...)
    # Try new backup system first
    if context.config.auto_restore_on_error and context.has_backup():
        result = context.restore_backup()
        pretty(result, "system", ...)
    elif context.conversation_backup:
        # Fallback to old system
        bot.tool_handler.clear()
        bot.conversation = context.conversation_backup
        pretty("Restored conversation from backup", "system", ...)
`
## 3. BackupHandler Class
**Location:** ots/dev/cli.py - new class
**What it does:**
- Dedicated handler for backup commands
- Clean separation of concerns
- Consistent with other handler classes (ConversationHandler, StateHandler, etc.)
**Methods:**
`python
class BackupHandler:
    def backup(self, bot, context, args) -> str
    def restore(self, bot, context, args) -> str
    def backup_info(self, bot, context, args) -> str
    def undo(self, bot, context, args) -> str  # alias for restore
`
## 4. Terminal Settings Management
**Location:** ots/dev/cli.py -
estore_terminal() function
**What it does:**
- Properly restore terminal settings on Unix systems after raw mode
- Prevents terminal corruption on errors or interrupts
**Current issue:**
- Terminal may be left in raw mode if errors occur
- User has to manually reset terminal
**Fix:**
`python
def restore_terminal(old_settings):
    """Restore terminal settings on Unix systems."""
    if platform.system() != "Windows" and old_settings is not None:
        fd = sys.stdin.fileno()
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
`
**Usage in autonomous mode:**
`python
try:
    old_settings = setup_raw_mode()
    # ... autonomous execution ...
    restore_terminal(old_settings)
except KeyboardInterrupt:
    if context.old_terminal_settings:
        restore_terminal(context.old_terminal_settings)
except Exception as e:
    if context.old_terminal_settings:
        restore_terminal(context.old_terminal_settings)
`
## 5. Auto-Backup Before User Messages
**Location:** ots/dev/cli.py - _handle_chat() method
**What it does:**
- Optionally create backup before each user message
- Configurable via /config set auto_backup true
- Provides safety net for experimentation
**Implementation:**
`python
def _handle_chat(self, bot: Bot, user_input: str):
    # Auto-backup before user message (if enabled)
    if self.context.config.auto_backup:
        self.context.create_backup("before_user_message")
    # ... rest of chat handling ...
`
## 6. Conversation Backup Compatibility
**Location:** Throughout navigation commands
**What it does:**
- Maintains context.conversation_backup for backward compatibility
- Set before navigation operations (up, down, left, right, root, etc.)
- Allows quick undo of navigation mistakes
**Pattern:**
`python
def up(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
    context.conversation_backup = bot.conversation
    bot.conversation = bot.conversation.parent.parent
    # ...
`
## 7. Config Display Improvements
**Location:** ots/dev/cli.py - SystemHandler.config()
**What it does:**
- Shows backup-related settings in /config output
- Clear indication of auto-backup and auto-restore status
**Addition to config display:**
`python
f"    auto_backup: {context.config.auto_backup}",
f"    auto_restore_on_error: {context.config.auto_restore_on_error}",
`
## Implementation Priority
**High Priority (Core Functionality):**
1. Enhanced backup system (CLIContext methods)
2. Improved error handling in chat
3. Terminal settings management
4. BackupHandler class
**Medium Priority (Quality of Life):**
5. Auto-backup before user messages
6. Config display improvements
**Low Priority (Nice to Have):**
7. Conversation backup compatibility (already partially exists)
## Testing Checklist
After implementing these fixes:
- [ ] /backup creates backup successfully
- [ ] /restore restores bot state correctly
- [ ] /backup_info shows accurate metadata
- [ ] Auto-backup works before user messages
- [ ] Auto-restore works on chat errors
- [ ] Terminal doesn't get corrupted on errors
- [ ] Config shows backup settings
- [ ] Backward compatibility maintained (existing code still works)
- [ ] Multiple restores to same checkpoint work
- [ ] Backup prevents concurrent operations
## Notes
- The backup system uses ot * 1 which properly handles callbacks, api_key, and other bot-specific concerns
- The backup metadata includes timestamp, reason, conversation depth, and token count for debugging
- The system gracefully degrades if backup fails (doesn't interrupt user flow)
- Auto-restore is opt-in to avoid surprising users
- The backup system is independent of the save/load system (different use cases)
