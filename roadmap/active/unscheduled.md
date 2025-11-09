# Unscheduled Items

**Status:** Low Priority / Future Consideration  
**Last Updated:** November 8, 2025

---

## Overview

This file contains roadmap items that are not currently scheduled for any phase. These are good ideas that may be implemented in the future, but are not prioritized given current strategic goals.

---

## Low Priority Items

### Item 3: JavaScript GUI / Frontend Backend for CLI

**Status:** ❌ NOT STARTED

**Goal:** Create web-based GUI that interfaces with CLI backend

**Architecture Options:**

- Thin Client: FastAPI backend + React frontend + WebSocket
- Electron App: Package CLI with Electron
- Jupyter-style Notebook: Web-based notebook interface

**Features:**

- Visual tree navigation
- Drag-and-drop
- Side-by-side comparison
- Visual FP builder

**Priority:** Low-Medium

**Effort:** Very High

**Note:** This is a Phase 4 item that will be funded by documentation service revenue. Not prioritized until revenue is established.

**Related:** See large_refactor_tasks.md item 2 - "GUI over the cli"

---

### Item 1: Expand Provider Base (Manual Implementation)

**Status:** ❌ NOT STARTED (Superseded by Item 15 - LiteLLM)

**Goal:** Add support for additional LLM providers

**Current State:**

- Supports Anthropic Claude, OpenAI GPT, and Google Gemini
- v3.0.0 achieved multi-provider support with 97%+ test pass rate

**Potential Providers:**

- Cohere
- Mistral AI
- Local models (Ollama, LM Studio)
- Azure OpenAI (separate from standard OpenAI)
- AWS Bedrock
- Hugging Face Inference API

**Priority:** Low (superseded by LiteLLM integration which provides 100+ providers)

**Note:** Item 15 (LiteLLM Integration) is the preferred approach for provider expansion. Manual implementation is only needed for providers requiring fine-grained control.

---

### Item 19: AST Warnings Cleanup

**Status:** ❌ NOT STARTED

**Goal:** Clean up AST warnings

**Priority:** Low

**Effort:** Low

---

### Item 22: Terminal Tool Output Format

**Status:** ✅ COMPLETE

**Goal:** Implicit [dir]> format like in terminal_tools.py

**Note:** Marked as complete in original roadmap.

---

### Item 23: Tool Configurations in CI/CD

**Status:** ❌ NOT STARTED

**Goal:** Tool factories respecting CI/CD constraints

**Priority:** Medium

**Effort:** Medium

**Note:** May become higher priority as CI/CD complexity increases.

---

### Item 42: Issue Resolver GitHub App

**Status:** ❌ NOT STARTED

**Goal:** Automated issue resolution through PR submissions

**Description:**
A GitHub App that monitors repository issues and automatically submits PRs with fixes, similar to CodeRabbit's review capabilities but focused on issue resolution.

**Components:**

1. **Issue Monitoring:** Webhook listener for new issues and comments
2. **Issue Analysis:** Use conversation trees to explore issue context
3. **Solution Generation:** Use branch_self to explore multiple solution approaches
4. **PR Submission:** Create branch with fix and submit PR
5. **Feedback Loop:** Monitor PR comments and iterate

**Competitive Advantages:**

- Conversation tree exploration shows reasoning process
- branch_self enables exploring multiple solution approaches
- OpenTelemetry tracking for cost and performance metrics
- Self-context management for handling complex issues

**Pricing Model:**

- $100-300/month per repository
- Free tier for open source (marketing + training data)
- Usage-based for high-volume repos
- Can bundle with documentation service

**Priority:** Medium (Phase 4 - After Documentation Service Launch)

**Effort:** High - Requires robust issue analysis and code generation

**Impact:** High - Second revenue stream, leverages same infrastructure as documentation service

---

### Item 43: Revert README.md to Non-Sample Version

**Status:** ❌ NOT STARTED (May be obsolete)

**Goal:** Restore README.md to proper project documentation

**Issue:** README.md was replaced with a sample file containing placeholder content

**Solution:** Revert README.md to the last non-sample version from git history

**Priority:** Low (may already be resolved)

**Effort:** Low (simple git revert)

---

### Item 44: Remove Print Statements from terminal_tools.py

**Status:** ❌ NOT STARTED

**Goal:** Remove print statements from file operation functions

**Issue:** terminal_tools.py contains print statements when file operations are performed

**Solution:** Remove print statements from file operation functions

**Priority:** Low-Medium (code quality)

**Effort:** Low (simple cleanup)

**Related:** Item 11 (Remove print statements from anthropic_bots.py - DONE)

---

### Item 51: Cache Controller Enhancement

**Status:** ❌ NOT STARTED

**Goal:** Enhance cache_controller to support multiple providers and intelligently select cache points

**Current State:**

- Anthropic supports prompt caching with manually managed cache breakpoints
- Only 4 cache points allowed (Anthropic limitation)
- No caching support for Gemini or OpenAI
- Cache points are not optimally placed in conversation tree

**Components:**

1. **Add Caching for Gemini and OpenAI:**
   - Implement caching for Google Gemini (context caching API)
   - Implement caching for OpenAI (prompt caching if/when available)
   - Unified cache controller interface across providers

2. **Intelligent Cache Point Selection for Anthropic:**
   - Automatically pick the most efficient forking points in conversation tree
   - Score each point by number of descendants, depth, and frequency of access
   - Select top 4 scoring points as cache breakpoints
   - Update cache points dynamically as tree grows

**Benefits:**

- Cost reduction through optimal cache placement
- Performance improvement with effective caching
- Multi-provider support
- Automatic cache point management

**Priority:** Medium-High (cost optimization, multi-provider support)

**Effort:** Medium (Phase 1), High (Phase 2-3)

**Impact:** High - Significant cost savings and performance improvement

**Related:** Item 14 (OpenTelemetry - for cache metrics), Item 15 (LiteLLM - multi-provider support)

---

## Summary

**Total Unscheduled Items:** 10

**Categories:**

- **GUI/Frontend:** 1 item (Item 3 - very high effort, low-medium priority)
- **Provider Expansion:** 1 item (Item 1 - superseded by LiteLLM)
- **Code Quality:** 3 items (Items 19, 44, 43 - low priority)
- **Infrastructure:** 1 item (Item 23 - medium priority)
- **Revenue Features:** 1 item (Item 42 - medium priority, future)
- **Performance:** 1 item (Item 51 - medium-high priority)
- **Complete:** 1 item (Item 22)

**May Be Promoted:**

- Item 51 (Cache Controller) - Medium-High priority, cost optimization
- Item 23 (Tool Configurations in CI/CD) - Medium priority
- Item 42 (Issue Resolver) - Medium priority, second revenue stream

**Likely to Remain Unscheduled:**

- Item 3 (GUI) - Will be funded by revenue, not prioritized until then
- Item 1 (Manual Provider Expansion) - Superseded by LiteLLM
- Items 19, 43, 44 (Code Quality) - Low priority cleanup tasks

---

**Navigation:**

- [Back to Roadmap](../ROADMAP.md)
- [Phase 1: Foundation](phase1_foundation.md)
- [Phase 2: Features](phase2_features.md)
- [Phase 3: Enhancement](phase3_enhancement.md)
- [Phase 4: Revenue](phase4_revenue.md)
