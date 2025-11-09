# Phase 2: Core Features & Expansion

**Status:** 1/8 Partial (12.5%)  
**Priority:** Medium  
**Last Updated:** November 8, 2025

---

## Overview

Phase 2 focuses on expanding core capabilities through industry standards integration (MCP, LiteLLM), advanced functional prompts, repository-level tools, and comprehensive CLI configuration. These features build on the solid foundation from Phase 1.

---

## Partial Items ⚠️

### Item 10: Expand self_tools Beyond branch_self

**Status:** ⚠️ PARTIAL (PR #125, Oct 13, 2025)

**Delivered:**

- list_context: Display bot messages with labels for removal
- remove_context: Remove bot-user message pairs by label
- CLI auto-prompts context reduction when token threshold exceeded
- Session-wide metrics tracking and display

**Remaining Work:**

- **Phase 1:** fork_from_node (create branch from earlier point)
- **Phase 2:** summarize_context, merge_branches
- **Phase 3:** mark_checkpoint, goto_checkpoint

**Proposed Additional Tools:**

- delete_stale_context: Remove outdated message pairs
- summarize_context: Replace verbose history with summary
- fork_from_node: Create branch from earlier point
- merge_branches: Combine insights from multiple branches
- list_conversation_nodes: Get overview of structure
- mark_checkpoint: Create named checkpoint
- goto_checkpoint: Navigate to checkpoint

**Priority:** Medium-High

**Effort:** Medium (each phase 1-2 weeks)

---

## Not Started ❌

### Item 13: MCP Integration (Model Context Protocol)

**Status:** ❌ NOT STARTED

**Goal:** Integrate MCP as both client and server

**Current State:**

- No MCP support
- Tools are bot-specific, not accessible to other MCP clients

#### MCP as Client (Priority 1)

**Purpose:** Connect to existing MCP servers to access their tools

**Benefits:**

- Instant access to growing MCP ecosystem
- Standardized tool connectivity (like USB-C for AI)
- Compatible with Claude Desktop, Cursor, and other MCP clients
- No need to build custom integrations for each tool

**MCP Ecosystem (October 2025):**

- 90% of organizations projected to use MCP by end of 2025
- Major adoption: Microsoft, OpenAI, Google DeepMind
- Early adopters: Block, Apollo, Zed, Replit, Codeium, Sourcegraph
- Microsoft has MCP in Azure AI Foundry
- Market growing from $1.2B (2022) to $4.5B (2025)

**Implementation Steps:**

1. Install MCP Python SDK: `pip install mcp`
2. Create MCPToolWrapper class to convert MCP tools to bot-compatible functions
3. Add `bot.add_mcp_server(name, command)` method
4. Handle async MCP communication
5. Test with popular MCP servers (filesystem, github, etc.)

#### MCP as Server (Priority 2)

**Purpose:** Expose your bot's tools as MCP server for other applications

**Benefits:**

- Your excellent tools (python_edit, branch_self, etc.) become available to entire MCP ecosystem
- Other developers can use them in Claude Desktop, Cursor, Windsurf, etc.
- Positions your project as valuable MCP tool provider
- Increases project visibility and adoption

**Tools to Expose:**

- python_edit - Scope-aware Python editing
- python_view - Scope-aware Python viewing
- branch_self - Parallel conversation exploration
- execute_python - Python code execution
- execute_powershell - PowerShell execution
- All self_tools (when implemented)

**Priority:** High (Phase 1 for Client, Phase 2 for Server)

**Effort:** Medium (Phase 1), Medium-High (Phase 2)

**Why MCP Over LangChain:**

- Simpler protocol vs. complex framework
- Industry standard emerging NOW
- LangChain itself is adapting to MCP (released MCP adapters)
- "USB-C for AI" - universal connectivity standard
- Less complexity than direct LangChain integration

**Related Initiative:** [MCP Integration](../initiatives/mcp_integration.md)

---

### Item 15: LiteLLM Integration for Provider Expansion

**Status:** ❌ NOT STARTED

**Goal:** Use LiteLLM as unified API layer for 100+ LLM providers

**Current State:**

- Manual implementation for each provider (Anthropic, OpenAI, Gemini)
- Each provider requires custom code for API calls, message formatting, tool handling
- Adding new providers is time-consuming

**What is LiteLLM:**
LiteLLM provides a unified interface for 100+ LLM providers:

- OpenAI, Anthropic, Google, Cohere, Mistral, Replicate
- Azure OpenAI, AWS Bedrock, Vertex AI
- Local models (Ollama, LM Studio, vLLM)
- Open source models (Llama, Mistral, etc.)

**Benefits:**

- **Instant Provider Support:** 100+ providers immediately available
- **Unified Interface:** Same code works across all providers
- **Active Maintenance:** LiteLLM team handles provider API changes
- **Cost Tracking:** Built-in cost calculation for all providers

**Implementation Approach:**

**Option 1: LiteLLM as Base Layer**
Create LiteLLMBot class that uses litellm.completion() for all providers

**Option 2: Hybrid Approach (Recommended)**

- Keep native implementations for primary providers (Anthropic, OpenAI, Gemini)
- Use LiteLLM for quick support of additional providers
- Best of both worlds: control + breadth

**Considerations:**

- **Pros:** Instant 100+ provider support, unified interface, active maintenance
- **Cons:** Abstraction layer overhead, less control over provider-specific features

**Implementation Steps:**

1. Install LiteLLM: `pip install litellm`
2. Create LiteLLMBot class extending BaseBot
3. Implement _call_api() using litellm.completion()
4. Test with multiple providers
5. Add provider configuration
6. Update documentation
7. Add tests for LiteLLM integration

**Priority:** Medium

**Effort:** Low - LiteLLM handles most complexity

**Impact:** High - Instant support for 100+ providers

**Related Items:** Item 5 (CLI Haiku Bots), Item 1 (Expand Provider Base)

---

### Item 48: Functional Prompts on Specific Branches

**Status:** ❌ NOT STARTED

**Goal:** Enable applying any functional prompt to specific nodes in conversation tree

**Current State:**

- Functional prompts always operate from `bot.conversation` (current node)
- No built-in way to apply FPs to specific branches in conversation tree
- Workaround requires manual conversation manipulation

**Use Cases:**

1. **Continue specific branch:** Apply `prompt_while` to Branch B while leaving A and C untouched
2. **Parallel branch processing:** Apply same FP to all branches (e.g., "write tests" for each file)
3. **Nested workflows:** Create complex multi-level branching with different FPs per branch
4. **Branch recovery:** Resume work on abandoned branches
5. **Selective processing:** Different FPs for different branches based on content

**Implementation Approach:**

**Phase 1: Helper Function** (Low effort, high value)
Create `apply_to_node(bot, node, fp_function, *args, **kwargs)` that temporarily sets bot.conversation to target node, executes FP, then restores original conversation.

**Phase 2: Convenience Functions** (If Phase 1 sees adoption)

- `apply_to_branches(bot, nodes, fp_function, ...)` - Apply FP to multiple nodes
- `apply_to_leaves(bot, fp_function, ...)` - Apply FP to all leaf nodes
- `apply_to_matching(bot, condition, fp_function, ...)` - Apply to nodes matching condition

**Phase 3: Context Manager** (Most elegant)
Create context manager for cleaner syntax when working with specific nodes.

**Benefits:**

- Natural extension of existing conversation tree patterns
- Enables sophisticated multi-branch reasoning
- Low implementation cost, high value
- No breaking changes (pure addition)

**Priority:** Medium-High (powerful feature, low cost)

**Effort:** Low (Phase 1), Medium (Phases 2-3)

---

### Item 41: Repository-Level Tools

**Status:** ❌ NOT STARTED

**Goal:** Tools that operate on entire codebase rather than individual files

**Current State:**

- File-level tools exist (view, edit individual files)
- Meta-tools exist (coordinate multiple bots/files)
- **Gap:** No true repository-wide awareness tools

**What "Repository-Level Tools" Means:**

- Understand repository structure (git repos, project layout, dependencies)
- Provide repository-wide context and awareness
- Enable cross-file operations (refactoring, analysis, testing)

**Proposed Tool Categories:**

**1. Repository Analysis:**

- `analyze_repository_structure()` - Map entire repo structure
- `find_dependencies()` - Analyze import graphs
- `identify_entry_points()` - Find main files, CLIs, APIs
- `analyze_test_coverage()` - Repository-wide coverage

**2. Repository Navigation:**

- `search_codebase(query)` - Search across all files
- `find_definition(symbol)` - Locate function/class definitions
- `find_usages(symbol)` - Find all usages
- `get_call_graph()` - Generate call graph

**3. Repository Operations:**

- `refactor_across_files(old, new)` - Rename across repo
- `update_imports()` - Fix imports repository-wide
- `run_repository_tests()` - Full test suite execution
- `generate_documentation()` - Create repo-wide docs

**4. Repository Context:**

- `get_repository_summary()` - High-level overview
- `get_architecture_diagram()` - Architecture visualization
- `get_recent_changes()` - Git history
- `get_project_metadata()` - Package info, dependencies

**5. Repository Management:**

- `create_module(name, spec)` - Create new module
- `remove_module(name)` - Remove module + references
- `merge_modules()` - Combine modules
- `split_module()` - Break large modules

**Implementation Phases:**

1. **Phase 1:** Basic repository context (structure, search, summary)
2. **Phase 2:** Advanced navigation (symbols, call graphs, dependencies)
3. **Phase 3:** Repository operations (refactoring, testing, docs)

**Use Cases:**

- Onboarding new bots with full repo context
- Large cross-file refactorings
- Architecture analysis and understanding
- Repository-wide code quality checks
- Auto-generating comprehensive documentation

**Priority:** Medium

**Effort:** High (requires integration with AST, git, testing frameworks)

---

### Item 6: Configure CLI More Thoroughly

**Status:** ❌ NOT STARTED

**Goal:** Comprehensive configuration system with plugin support

**Categories:**

- Display settings (colors, formatting, verbosity)
- Behavior settings (autosave, context limits, default tools)
- Provider settings (default provider, model selection, API keys)
- Plugin system (extensibility)

**Priority:** Medium-High

**Effort:** Medium

**Related Items:** Item 5 (CLI Haiku Bots)

**Related Initiative:** [CLI Improvements](../initiatives/cli_improvements.md)

---

### Item 16: Centralized File-Writing Wrapper

**Status:** ❌ NOT STARTED

**Goal:** Wrapper with BOM removal logic (for all tools using toolify decorator?)

**Priority:** Medium

**Effort:** Low

---

### Item 18: Bot Requirements System

**Status:** ❌ NOT STARTED

**Goal:** bot.requirements parameter for tool dependencies

**Priority:** Medium

**Effort:** Medium

---

## Summary

**Progress:** 1/8 partial (12.5%)

**Partial:** 1 item

- Item 10 (Expand self_tools - list/remove_context done, phases 1-3 remaining)

**Not Started:** 7 items

- Item 13 (MCP Integration - HIGH priority, industry standard)
- Item 15 (LiteLLM - MEDIUM priority, 100+ providers)
- Item 48 (FP on branches - MEDIUM-HIGH priority, low effort)
- Item 41 (Repository tools - MEDIUM priority, high effort)
- Item 6 (Configure CLI - MEDIUM-HIGH priority)
- Item 16 (File-writing wrapper - MEDIUM priority, low effort)
- Item 18 (Bot requirements - MEDIUM priority)

**Key Priorities:**

1. **MCP Integration (Item 13)** - Industry standard, high impact
2. **FP on Specific Branches (Item 48)** - Low effort, high value
3. **Configure CLI (Item 6)** - Improves user experience
4. **LiteLLM (Item 15)** - Instant 100+ provider support

**Strategic Note:**
Phase 2 focuses on ecosystem integration (MCP, LiteLLM) and advanced capabilities (repository tools, FP on branches). MCP integration is particularly critical as it's becoming the industry standard for AI tool connectivity.

---

**Navigation:**

- [Back to Roadmap](../ROADMAP.md)
- [Phase 1: Foundation](phase1_foundation.md)
- [Phase 3: Enhancement](phase3_enhancement.md)
- [All Initiatives](../initiatives/)
