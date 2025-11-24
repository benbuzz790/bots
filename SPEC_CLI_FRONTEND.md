# Specification: CLI Frontend Layer
## Overview
Separate presentation logic from business logic in the CLI by introducing a frontend abstraction layer. This enables multiple frontends (terminal, GUI, web, Obsidian plugin) to share the same command handlers and business logic.
## Motivation
The current CLI mixes concerns:
- Display logic scattered throughout handlers
- Handlers call pretty() directly, making them hard to test
- No clear separation between I/O and business logic
- Difficult to create alternative interfaces (GUI, web, plugins)
With multiple frontends planned (Obsidian plugin, potential GUI), we need a clean abstraction that allows:
- Handlers to be pure functions (input → output)
- Easy testing without I/O
- Multiple frontends sharing the same logic
- Consistent behavior across interfaces
## Design Principles
1. **Incremental refactor** - Change one handler class at a time, test, then move on
2. **TDD approach** - Write tests first to ensure frontend works correctly
3. **Minimal disruption** - Keep existing CLI behavior unchanged externally
4. **Future-proof** - Design for multiple frontends (terminal, GUI, web, plugins)
5. **Pure handlers** - Handlers return data, frontend handles display
## Architecture
### New Structure
\\\
bots/dev/
  cli.py              # Main orchestrator (minimal changes)
  cli_frontend.py     # NEW: Frontend abstraction
  cli_handlers.py     # FUTURE: Consolidated handlers (optional)
  cli_display.py      # FUTURE: Display utilities (optional)
\\\
### Frontend Interface
\\\python
class CLIFrontend(ABC):
    \"\"\"Abstract frontend for CLI interactions.\"\"\"
    # Display methods
    @abstractmethod
    def display_message(self, role: str, content: str) -> None:
        \"\"\"Display a conversation message (user or bot).\"\"\"
    @abstractmethod
    def display_system(self, message: str) -> None:
        \"\"\"Display a system message.\"\"\"
    @abstractmethod
    def display_error(self, message: str) -> None:
        \"\"\"Display an error message.\"\"\"
    @abstractmethod
    def display_metrics(self, metrics: dict) -> None:
        \"\"\"Display API usage metrics.\"\"\"
    @abstractmethod
    def display_tool_call(self, name: str, args: dict) -> None:
        \"\"\"Display a tool being called.\"\"\"
    @abstractmethod
    def display_tool_result(self, name: str, result: str) -> None:
        \"\"\"Display a tool result.\"\"\"
    # Input methods
    @abstractmethod
    def get_user_input(self, prompt: str = ">>> ") -> str:
        \"\"\"Get single-line input from user.\"\"\"
    @abstractmethod
    def get_multiline_input(self, prompt: str) -> str:
        \"\"\"Get multi-line input from user.\"\"\"
    @abstractmethod
    def confirm(self, question: str) -> bool:
        \"\"\"Ask user for yes/no confirmation.\"\"\"
class TerminalFrontend(CLIFrontend):
    \"\"\"Terminal-based frontend implementation.\"\"\"
    # Implements all abstract methods using current pretty(), colors, etc.
\\\
### Handler Return Format
Handlers return structured data instead of calling display functions:
\\\python
# Return format
{
    "type": "system" | "error" | "message" | "metrics" | "tool_call" | "tool_result",
    "content": str | dict,
    "role": str (optional, for messages),
    "name": str (optional, for tools)
}
# Examples:
{"type": "system", "content": "Bot saved to file.bot"}
{"type": "error", "content": "File not found: missing.bot"}
{"type": "message", "role": "assistant", "content": "Here's the answer..."}
{"type": "metrics", "content": {"tokens": 1234, "cost": 0.05}}
{"type": "tool_call", "name": "python_edit", "content": {...}}
\\\
## Implementation Plan
### Phase 1: Foundation (Week 1)
**Goal**: Create frontend abstraction and tests
1. Create cli_frontend.py:
   - Define CLIFrontend abstract base class
   - Implement TerminalFrontend with current behavior
   - Move color constants to frontend
   - Move pretty(), display_metrics(), ormat_tool_data() to frontend
2. Write tests:
   - 	ests/unit/test_cli_frontend.py - Test frontend methods
   - Mock frontend for handler testing
   - Verify display output format
3. Update CLIContext:
   - Add rontend: CLIFrontend field
   - Initialize in CLI.__init__()
**Success Criteria**:
- [ ] CLIFrontend abstract class defined
- [ ] TerminalFrontend implements all methods
- [ ] Tests pass for frontend display methods
- [ ] No changes to CLI behavior yet
### Phase 2: Refactor StateHandler (Week 2)
**Goal**: Prove the pattern with one handler class
1. Update StateHandler:
   - Change methods to return data dicts
   - Remove direct pretty() calls
   - Return structured responses
2. Update CLI._handle_command():
   - Check handler return type
   - If dict, use frontend to display
   - Maintain backward compatibility
3. Write tests:
   - Test StateHandler returns correct data
   - Test CLI displays data correctly
   - Integration test with mock frontend
**Success Criteria**:
- [ ] StateHandler returns data instead of displaying
- [ ] CLI uses frontend to display StateHandler results
- [ ] All existing tests still pass
- [ ] New tests verify data format
### Phase 3: Refactor ConversationHandler (Week 3)
**Goal**: Apply pattern to navigation commands
1. Update ConversationHandler:
   - Return data dicts for all methods
   - Remove pretty() calls
   - Handle tree visualization data
2. Update tests:
   - Verify navigation data format
   - Test with mock frontend
**Success Criteria**:
- [ ] ConversationHandler returns data
- [ ] Navigation commands work identically
- [ ] Tests pass
### Phase 4: Refactor SystemHandler (Week 4)
**Goal**: Handle config and system commands
1. Update SystemHandler:
   - Return data for config, verbose, etc.
   - Remove display logic
2. Update tests
**Success Criteria**:
- [ ] SystemHandler returns data
- [ ] System commands work identically
- [ ] Tests pass
### Phase 5: Refactor PromptHandler (Week 5)
**Goal**: Handle prompt management
1. Update PromptHandler:
   - Return data for save/load/delete
   - Handle prompt selection UI through frontend
2. Update tests
**Success Criteria**:
- [ ] PromptHandler returns data
- [ ] Prompt commands work identically
- [ ] Tests pass
### Phase 6: Refactor DynamicFunctionalPromptHandler (Week 6)
**Goal**: Handle functional prompt execution
1. Update DynamicFunctionalPromptHandler:
   - Return execution results as data
   - Handle parameter collection through frontend
2. Update tests
**Success Criteria**:
- [ ] FP handler returns data
- [ ] FP commands work identically
- [ ] Tests pass
### Phase 7: Cleanup and Documentation (Week 7)
**Goal**: Polish and document
1. Remove old display code:
   - Consolidate color constants
   - Remove unused functions
   - Clean up imports
2. Documentation:
   - Update CLI_PRIMER.md
   - Add frontend guide
   - Document handler return format
3. Create example alternative frontend:
   - Simple GUI or web demo
   - Proves abstraction works
**Success Criteria**:
- [ ] All handlers use frontend
- [ ] No direct display calls in handlers
- [ ] Documentation complete
- [ ] Example alternative frontend works
## Testing Strategy
### Unit Tests
- Test each frontend method independently
- Mock frontend for handler tests
- Verify data format from handlers
### Integration Tests
- Test CLI with real frontend
- Test handler → frontend flow
- Verify display output
### Regression Tests
- All existing CLI tests must pass
- Behavior unchanged from user perspective
## Progress Tracking
### Ledger Format
\\\markdown
## CLI Frontend Refactor Progress
### Phase 1: Foundation
- [x] Create CLIFrontend abstract class
- [x] Implement TerminalFrontend
- [x] Write frontend tests
- [x] Update CLIContext
### Phase 2: StateHandler
- [ ] Refactor StateHandler.save()
- [ ] Refactor StateHandler.load()
- [ ] Update CLI._handle_command()
- [ ] Write tests
[Continue for each phase...]
\\\
## Success Criteria
### Overall Goals
1. **Separation of concerns**: Handlers don't call display functions
2. **Testability**: Handlers can be tested without I/O
3. **Flexibility**: Easy to create new frontends
4. **Compatibility**: Existing CLI behavior unchanged
5. **Documentation**: Clear guide for creating frontends
### Acceptance Tests
- [ ] All existing CLI tests pass
- [ ] New frontend tests pass
- [ ] Handler tests use mock frontend
- [ ] Example alternative frontend works
- [ ] Documentation complete
## Future Enhancements (Out of Scope)
- Rich terminal UI with 	extual or prompt_toolkit
- Web-based frontend
- GUI frontend
- Input history and auto-completion
- Progress bars for long operations
- Mouse support
## Notes
- Keep changes incremental and testable
- Maintain backward compatibility throughout
- Document as we go
- Create reusable patterns for future frontends
