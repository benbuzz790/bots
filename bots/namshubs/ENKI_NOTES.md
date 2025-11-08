# Enki Development Notes
## Purpose
This document tracks thoughts, feedback, and iterations on the namshub_of_enki design.
It serves as a working memory for improving Enki's ability to create high-quality namshubs.
---
## Version 1.0 - Initial Draft (Current)
### What Works
- G�� Clear sequential workflow with 6 phases
- G�� Embedded design principles in system message
- G�� Interactive requirements gathering (first step asks questions)
- G�� Test creation and execution included
- G�� Proper parameter validation
- G�� Uses chain_workflow appropriately
- G�� Tests pass with mocked bot
### What Doesn't Work / Issues
- G�� Doesn't branch before starting workflow - loses context if workflow is long
- G�� Namshub name extraction is clunky (defaults to "new_namshub")
- G��n+� System message is very long - might hit token limits
- G��n+� Requirements gathering is unstructured - bot might miss important details
- G��n+� No reference to existing namshubs unless explicitly asked
- G��n+� No dry-run or design-only mode
### Observations
1. **Context preservation**: The workflow can be long (6 phases with iteration). Should branch first to preserve the calling context.
2. **Requirements format**: Would benefit from a structured template (checklist format?)
3. **System message length**: Contains all principles + template + commands. Could be split or condensed.
4. **Name extraction**: Should parse the task_description or requirements response to extract the namshub name automatically.
### Ideas for Next Iteration
1. **Branch first**: Add initial step to branch the bot before starting the workflow
2. **Structured requirements**: Use a checklist format for gathering requirements
3. **Auto-extract name**: Parse requirements response to find namshub name
4. **Reference examples**: Optionally view existing namshubs if task is similar
5. **Dry-run mode**: Parameter to design without implementing
---
## Version 1.1 - Branch First (In Progress)
### Changes
- Adding initial branch before workflow starts
- This preserves the calling context and allows Enki to work in isolation
### Rationale
When Enki is invoked, the calling bot may have important context that shouldn't be polluted by Enki's workflow. By branching immediately, we:
- Preserve the original conversation state
- Allow Enki to work in a clean context
- Make it easier to return to the original state after completion
### Implementation Notes
- Need to branch before configuring toolkit and system message
- The branch should be the first thing that happens in invoke()
- After branching, proceed with normal workflow
---
## Future Considerations
### Testing Strategy
- Current tests use mocked responses - need real bot tests
- Should test with various task complexities
- Need to verify actual file creation and test execution
- Consider reliability testing (does it work consistently?)
### Toolkit Decisions
- Current: view, view_dir, python_view, python_edit, execute_powershell, execute_python
- Redundancy is good (powershell + python for execution)
- Should Enki have access to more tools? (git commands? file operations?)
- Should toolkit vary based on task type?
### Workflow Patterns
- chain_while is appropriate for sequential phases with iteration
- Could some phases benefit from branching? (e.g., explore multiple designs in parallel?)
- Should requirements gathering use a different pattern?
### System Message Design
- Currently embeds everything - principles, template, commands
- Alternative: Shorter system message + reference documents
- Could use dynamic prompts to inject relevant principles per phase
- Trade-off: completeness vs. token efficiency
### Error Handling
- What if test fails repeatedly?
- What if file creation fails?
- What if requirements are incomplete?
- Should Enki ask for help or abort?
---
## Questions for Future Exploration
1. **How much autonomy should Enki have?**
   - Should it make design decisions or always ask?
   - When should it reference existing namshubs?
2. **What's the right level of specificity?**
   - Very prescriptive (like PR namshub) vs. more flexible
   - How to guide users to provide enough detail?
3. **How to handle different namshub types?**
   - Simple read-only analysis vs. complex multi-phase workflows
   - Should Enki have templates for common patterns?
4. **Integration with other namshubs?**
   - Should Enki be able to call other namshubs?
   - How to handle dependencies between namshubs?
---
## Lessons Learned
### From PR Namshub
- Very specific commands work well
- Including common pitfalls in system message is valuable
- branch_self usage should be explicit with clear instructions
- Verification steps are important (run linters again, etc.)
### From Design Principles Discussion
- Redundant tools provide flexibility
- execute_powershell is excellent all-purpose backup
- _while patterns are stronger than plain patterns
- INSTRUCTION pattern helps focus
- Bounded execution is critical
### From Testing
- Mocked tests are good for structure validation
- Need real tests to verify actual functionality
- Test setup documentation is important
- Custom tests per namshub are necessary
---
## Changelog
### 2024-XX-XX - v1.0 Initial Draft
- Created namshub_of_enki with 6-phase workflow
- Created test suite with mocked responses
- Tests pass successfully
### 2024-XX-XX - v1.1 Branch First
- Adding branch at start of workflow to preserve context
- (In progress)
---
## Update: Version 1.1 - Branch First (Completed)
### Changes Made
- G�� Added branching at the start of invoke() before configuring toolkit
- G�� Preserves original conversation state by creating a branch
- G�� Enki workflow now runs in isolation from calling context
### Implementation Details
`python
# Save the original conversation state
original_conversation = bot.conversation
# Create a branch for the Enki workflow
bot.conversation = original_conversation._add_reply(
    content=f"Starting Enki workflow to create: {namshub_name}",
    role="assistant"
)
# Then proceed with toolkit configuration and workflow...
`
### Benefits
1. **Context preservation**: Original conversation remains clean
2. **Isolation**: Enki's work doesn't pollute the main conversation tree
3. **Clarity**: Clear separation between "invoking Enki" and "Enki's work"
4. **Debugging**: Easier to trace what Enki did vs. what the caller did
### Testing
- G�� Both tests still pass
- G�� No breaking changes to the interface
- G�� Branching happens transparently
### Next Steps
Consider for v1.2:
- Structured requirements gathering (checklist format)
- Auto-extract namshub name from requirements
- Optionally reference existing namshubs for similar tasks
---
## Namshub Created: namshub_of_issue_resolution
### Date
2025-11-02
### Purpose
Handles the complete GitHub issue resolution workflow from reading the issue through creating a PR and invoking the PR namshub for CI/CD handling.
### Workflow (9 phases)
1. Read Issue - Use gh CLI to view issue details
2. Analyze Codebase - Understand structure and plan implementation
3. Create Feature Branch - Create issue-specific branch
4. Implement Solution - Make focused changes, use branch_self for parallelism
5. Create/Update Tests - Add tests and verify they pass
6. Verify Locally - Run linters and full test suite
7. Commit and Push - Stage, commit, and push changes
8. Create Pull Request - Use gh CLI to create PR with issue link
9. Invoke PR Namshub - Hand off to namshub_of_pull_requests for CI/CD
### Toolkit
- execute_powershell (primary - for git, gh CLI)
- view, view_dir (read codebase)
- python_view (examine Python files)
- python_edit (make changes)
### Key Features
- Branches first to preserve context
- Auto-extracts issue number from conversation
- Links PR to issue with Fixes syntax
- Invokes PR namshub at the end (composition!)
- Uses branch_self for parallel implementation tasks
### Testing
- 3 tests created and passing
- Full workflow, validation, and context extraction tested
### Lessons Learned
- Namshub composition works! Invoking PR namshub at the end is clean
- 9 phases is manageable with chain_while
- Branching first is essential
---
## Namshub Created: namshub_of_unit_testing
### Date: 2025-11-04
### Purpose
Generate comprehensive unit tests for bots framework code with 95% coverage target.
### Requirements Gathered
- Target: Internal bots framework code only
- Input: target_file parameter (required)
- Test location: tests/unit/ with subfolder structure mirroring source
- Coverage: 95% target with happy and sad path scenarios
- Style: Pytest functions (not unittest classes)
- Mocking: Use existing fixtures when available, create new when needed
- Workflow: Context gathering branch ? Plan ? Parallel generation ? Verify
### Design Decisions
**Toolkit:**
- view, view_dir - Code examination
- python_view - Python code analysis
- python_edit - Test file creation
- execute_powershell - Primary test execution
- execute_python - Backup test execution
**Workflow Pattern:**
1. Context gathering via branch_self (analyze file, check existing tests, run coverage)
2. Plan test files and fixtures (main branch)
3. Parallel test generation via branch_self (one branch per file to avoid corruption)
4. Verify tests collect and run (collection errors NOT OK, test failures OK)
5. Final summary with coverage report
**Key Features:**
- Branches first to preserve context
- Uses branch_self for context gathering (reports findings up)
- Uses branch_self for parallel test generation (one file per branch)
- Verifies tests collect properly (failures acceptable, collection errors not)
- Auto-determines test file path with subfolder structure
- 95% coverage target
### System Message Highlights
- Embedded testing principles (coverage, organization, mocking, structure)
- Specific commands for common operations
- References to existing fixtures
- Clear distinction: collection errors NOT OK, test failures OK
### Testing
- ? Created tests/integration/test_namshub_of_unit_testing.py
- ? Tests parameter validation
- ? Tests full workflow with mocked responses
- ? Both tests pass
### Observations
- This namshub demonstrates good use of branch_self for both context gathering and parallel work
- Clear separation: one branch gathers context, main branch plans, multiple branches execute
- File-per-branch strategy prevents corruption
- Verification step ensures quality (tests must collect)
### Potential Improvements
- Could add retry logic if tests fail to collect
- Could generate fixture files automatically if needed
- Could integrate with CI/CD to run tests in pipeline
- Could track coverage trends over time
---
## E2E Testing Challenges - namshub_of_unit_testing
### Date: 2025-11-04
### Challenge
Creating automated E2E tests for the unit testing namshub is difficult because:
1. It requires real API calls (expensive and slow)
2. The bot's behavior can vary between runs
3. File creation in isolated environments has import issues
4. The workflow is complex with multiple branching steps
### Current Test Coverage
- ? Unit tests with mocked responses (tests/integration/test_namshub_of_unit_testing.py)
- ? Tests parameter validation
- ? Tests workflow structure
- ?? E2E test attempted but incomplete (tests/e2e/test_namshub_of_unit_testing_real.py)
### Recommendation
For now, rely on:
1. Unit tests with mocked responses for structure validation
2. Manual testing on real repo code when making changes
3. Future: Consider adding observability/logging to track namshub execution
### Manual Testing Procedure
To manually test the namshub:
1. Create a bot: `bot = AnthropicBot()`
2. Add invoke_namshub tool: `bot.add_tools(invoke_namshub)`
3. Invoke: `bot.respond("invoke_namshub('namshub_of_unit_testing', target_file='path/to/file.py')")`
4. Verify test files are created in tests/unit/
5. Run: `pytest tests/unit/path/to/test_file.py --collect-only`
6. Check coverage: `pytest tests/unit/path/to/test_file.py --cov=path/to/file.py`
### Future Improvements
- Add logging/tracing to track namshub execution steps
- Create simpler E2E tests that verify workflow completion without file validation
- Consider snapshot testing for generated test files
- Add retry logic for API failures
---
## Update: namshub_of_issue_resolution v1.1 - Pluralized and Manual FP
### Changes Made
1. **Pluralized workflow** - Prompts now handle multiple related issues by default
2. **Manual functional prompting** - Replaced helper function with direct fp.chain_while call
3. **INSTRUCTION pattern applied** - All prompts use INSTRUCTION prefix
4. **Enhanced issue discovery** - Bot looks for similar/linked issues to address together
### Key Improvements
**Pluralization:**
- System message and prompts written to handle multiple issues naturally
- Bot searches for related issues: gh issue list --search "is:open"
- Groups issues that should be addressed together
- PR links to all issues: "Fixes #N\nFixes #M"
- Commit messages mention all issues addressed
**Manual Functional Prompting:**
- Direct use of fp.chain_while instead of chain_workflow helper
- Explicit stop_condition: fp.conditions.tool_not_used
- Explicit continue_prompt with INSTRUCTION focus
- More control and visibility of the pattern being used
**Why Manual FP?**
- More explicit about what's happening
- Easier to customize stop conditions and continue prompts
- Better for understanding the underlying patterns
- Helpers are convenient but can obscure the mechanism
### Testing
- All 3 tests still pass
- Fixed f-string escaping issue ({{}} for literal braces in examples)
### Lessons Learned
- **Pluralization without distinction** - Writing prompts as if multiple is default makes them flexible
- **Manual FP is clearer** - Seeing the actual fp.chain_while call is more educational
- **INSTRUCTION pattern works well** - Keeps bot focused on current step
- **F-string escaping matters** - Use {{}} for literal braces in f-strings
---
## Update: Fixed INSTRUCTION Prefix Duplication
### Date
2025-11-04
### Changes Made
**1. Updated helpers.py::instruction_prompts()**
- Added check to prevent duplicate INSTRUCTION prefixes
- If prompt already starts with "INSTRUCTION: ", don't add another
- If prompt doesn't have prefix, add it as normal
- Prevents "INSTRUCTION: INSTRUCTION: ..." duplication
**2. Updated namshub_of_unit_testing.py**
- Removed "INSTRUCTION: " prefix from all workflow_prompts
- Prompts now start directly with content
- chain_workflow() adds the prefix via instruction_prompts()
- Cleaner separation: prompts are content, helper adds formatting
### Why This Matters
**Problem:**
- When prompts already had "INSTRUCTION: " prefix
- And chain_workflow() called instruction_prompts()
- Result: "INSTRUCTION: INSTRUCTION: Do something..."
**Solution:**
- instruction_prompts() now checks for existing prefix
- Namshub prompts don't include prefix (helper adds it)
- Clean separation of concerns
### Implementation Approach
Did both tasks directly (not via branch_self) since:
- Simple, straightforward changes
- No dependencies between tasks
- Quick verification possible
### Testing
- Verified instruction_prompts() prevents duplicates
- Tested with normal prompts, mixed prompts, and all-prefixed prompts
- All cases work correctly
### Lessons Learned
- **Idempotent helpers are better** - Functions should handle being called multiple times
- **Separation of concerns** - Prompts are content, helpers add formatting
- **Simple fixes don't need branching** - Sometimes direct edits are clearest
