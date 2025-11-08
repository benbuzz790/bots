# Bots Project Roadmap
**Last Updated:** November 8, 2025
---
## Quick Status
- **Phase 1 (Foundation & Critical Fixes):** 10/14 complete (71%)
- **Phase 2 (Core Features & Expansion):** 1/8 started (12%)
- **Phase 3 (Enhancement & UX):** 1/6 complete, 1/6 partial (25%)
- **Phase 4 (Revenue Features):** 🚧 In development (github-docs-app)
---
## Active Phases
### Foundation & Critical Fixes
- [Phase 1: Foundation & Critical Fixes](active/phase1_foundation.md) - 71% complete
  - ✅ 10 items complete (branch_self, save/load, callbacks, observability, tests)
  - ⚠️ 1 item partial (OpenTelemetry Phase 4)
  - ❌ 3 items not started (Unix/Mac, multi-OS testing, build_messages refactor)
### Core Features & Expansion
- [Phase 2: Core Features & Expansion](active/phase2_features.md) - 12% started
  - ⚠️ 1 item partial (self_tools expansion)
  - ❌ 7 items not started (MCP, LiteLLM, repository tools, CLI config)
### Enhancement & User Experience
- [Phase 3: Enhancement & UX](active/phase3_enhancement.md) - 25% progress
  - ✅ 1 item complete (python_edit feedback)
  - ⚠️ 1 item partial (CLI prettier)
  - ❌ 4 items not started (tutorials, CHATME.bot, file associations)
### Revenue Features
- [Phase 4: Revenue Features](active/phase4_revenue.md) - 🚧 In development
  - 🚧 4 items in progress (GitHub integration, doc output, workflow, MVP)
  - ❌ 2 items not started (auth/billing, multi-tenancy)
  - **github-docs-app:** 81.9% test pass rate (1466/1790), 8-12 hours to 95%
---
## Major Initiatives
Cross-cutting efforts spanning multiple roadmap items:
- [**Observability**](initiatives/observability.md) - ✅ **DONE** (Items 11, 12, 14)
  - OpenTelemetry integration, callbacks, metrics tracking
  - Phase 4 (production observability) pending
- [**Cross-Platform Support**](initiatives/cross_platform.md) - ❌ **NOT STARTED** (Items 38, 39)
  - Unix/Mac compatibility, multi-OS testing
  - Critical for market reach
- [**MCP Integration**](initiatives/mcp_integration.md) - ❌ **NOT STARTED** (Item 13)
  - Model Context Protocol client and server
  - Industry standard, high priority
- [**Documentation Service**](initiatives/documentation_service.md) - 🚧 **IN PROGRESS** (Items 27-32)
  - Automated GitHub documentation bot
  - Primary revenue path
- [**CLI Improvements**](initiatives/cli_improvements.md) - ⚠️ **ONGOING** (Items 2, 5, 6, 40)
  - Recent additions: fork navigation, dynamic prompts, context tools
  - Continuous enhancement
- [**Test Infrastructure**](initiatives/test_infrastructure.md) - ✅ **DONE** (Items 9, 24, 25)
  - Test organization, parallelism, tempfile handling
  - Recent fixes: pytest Windows errors, 9 skipped tests resolved
---
## Recent Completions
- [**October 2025**](completed/2025-10_foundation.md) - Foundation items
  - branch_self tracking, save/load behavior, callbacks, observability
  - 7 items completed
- [**November 2025**](completed/2025-11_infrastructure.md) - Infrastructure & features
  - Namshubs/workflows system, fork navigation, dynamic prompts
  - Test infrastructure fixes, bug fixes (Issues #158-164)
  - 4+ new features delivered
---
## Strategy & Vision
Strategic planning and business model:
- [**Strategic Roadmap**](ROADMAP.md) - Top-level strategic planning
  - Quarterly priorities (Q4 2025, Q1 2026, Q2 2026)
  - Strategic themes, decision framework, risk management
  - Success metrics and resource allocation
- [**Development Philosophy**](PHILOSOPHY.md) - Standards over frameworks
  - Core principle: embrace universal standards (MCP, OpenTelemetry, LiteLLM)
  - Three pillars: standards, differentiators, production readiness
  - Why this matters now
- [**Monetization Strategy**](MONETIZATION.md) - Revenue path
  - Primary target: automated documentation service
  - Secondary targets: code review, bot marketplace
  - Revenue timeline and success metrics
---
## Navigation
- **Search Items:** [Item Index](ITEM_INDEX.md) *(coming soon)*
- **Active Work:** Phase files (above)
- **Completed Work:** Archive files (above)
- **Major Efforts:** Initiative files (above)
- **Strategy:** ROADMAP.md, PHILOSOPHY.md, MONETIZATION.md
---
## Key Priorities
### Critical (Next 2-4 Weeks)
1. **Complete Documentation Service MVP** - 8-12 hours to 95% tests
2. **Tutorial Expansion** - Critical adoption gap (only 1 tutorial exists)
3. **Cross-Platform Support** - Unlock Mac/Linux market
### High (Next 1-3 Months)
1. **MCP Integration** - Industry standard, ecosystem connectivity
2. **Multi-OS Testing** - Validate cross-platform support
3. **OpenTelemetry Phase 4** - Production observability
---
**Maintained by:** Roadmap update namshub (automated)  
**Next Review:** December 31, 2025
