# Bots Project - Strategic Roadmap

**Last Updated:** December 18, 2025
**Vision:** Build the best agentic AI system on industry standards
**Mission:** Conversation trees + functional prompts + standards integration
---

## Executive Summary

The bots project has reached a critical inflection point. After successfully implementing multi-provider support and achieving 97%+ test pass rate, we're positioned to make strategic choices about our future direction.
**Current State:**

- **Strong technical foundation:** Phase 1 is 71% complete (10/14 items done)
- **Active development velocity:** 12 PRs merged in last 3 weeks
- **Documentation service in development:** github-docs-app at 81.9% test pass rate (1466/1790 tests passing), estimated 8-12 hours to reach 95%
- **Multi-provider support:** Currently supports 3 providers (OpenAI, Anthropic, Google). Plans to expand to 100+ via LiteLLM integration.
- **Platform limitation:** Windows-only (limits market reach to Mac/Linux developers)
**Strategic Direction:**

1. **Embrace Universal Standards** (MCP, OpenTelemetry, LiteLLM)
2. **Maintain Core Differentiators** (Conversation trees, functional prompts, branch_self)
3. **Build for Production** (Observability, quality guardrails, configuration)

---

## Strategic Priorities (Next 6 Months)

### Q4 2025: Foundation & Revenue MVP

**Goal:** Complete foundation work and launch documentation service MVP
**Critical Path:**

1. Complete documentation service MVP (8-12 hours test fixes + auth/billing system)
2. Tutorial expansion (7 comprehensive tutorials - critical for adoption)
3. Launch MVP with first 10 paying customers
4. Prove n*log(n) scaling advantage with metrics
**Success Metrics:**

- Documentation service: 95%+ test pass rate
- First 10 paying customers acquired
- $5k MRR by end of Q4 2025
- 7+ comprehensive tutorials published
**Risks:**
- Documentation service not production-ready (no auth/billing yet)
- Tutorial gap hurts adoption (only 1 minimal tutorial exists)
- Revenue timeline may slip without focused effort

### Q1 2026: Platform Expansion

**Goal:** Cross-platform support and ecosystem integration
**Critical Path:**

1. Unix/Mac compatibility (shell abstraction layer, bash/sh support)
2. Multi-OS CI testing (Windows, Linux, macOS matrix)
3. MCP Client integration (connect to MCP ecosystem)
4. LiteLLM integration (instant support for 100+ providers)
**Success Metrics:**

- Tests pass on Windows, Linux, and macOS
- Can connect to any MCP server as client
- Support 100+ LLM providers via LiteLLM
- $10k MRR from documentation service
**Risks:**
- Cross-platform testing complexity
- MCP ecosystem still maturing
- Resource allocation between revenue and platform work

### Q2 2026: Ecosystem & Scale

**Goal:** MCP Server, GUI development, code review service
**Critical Path:**

1. MCP Server implementation (expose our tools to ecosystem)
2. GUI development (funded by documentation service revenue)
3. Code review service launch (leverage same infrastructure)
4. Advanced self-tools expansion (Phases 2-3)
**Success Metrics:**

- Our tools available in Claude Desktop, Cursor, and other MCP clients
- GUI beta launched with visual tree navigation
- Code review service: 10 paying customers
- $20k MRR combined across services

---

## Strategic Themes

### Theme 1: Standards Over Frameworks

**Rationale:** MCP is projected to reach 90% organizational adoption by end of 2025. OpenTelemetry is the de facto standard for observability. LiteLLM provides unified interface to 100+ providers. Building on standards provides network effects and reduces maintenance burden.
**Implementation:**

- **MCP Integration (Item 13)** - HIGH PRIORITY
  - Phase 1: MCP Client (Q1 2026)
  - Phase 2: MCP Server (Q2 2026)
- **OpenTelemetry (Item 14)** - Phases 1-3 DONE, Phase 4 pending
- **LiteLLM (Item 15)** - MEDIUM PRIORITY (Q1 2026)
**Impact:** Network effects, ecosystem integration, reduced maintenance, instant access to growing tool/provider ecosystems

### Theme 2: Production Readiness

**Rationale:** Move from "works on my machine" to "works in production" requires observability, quality guardrails, and proper configuration systems.
**Implementation:**

- **Observability (Item 14)** - MOSTLY DONE (Phases 1-3 complete)
- **Branch protection (Item 26)** - DONE
- **Test infrastructure (Items 9, 24, 25)** - DONE
- **Configuration system (Item 6)** - NOT STARTED
**Impact:** Reliability, debuggability, enterprise-ready, production deployment confidence

### Theme 3: Market Reach

**Rationale:** Windows-only terminal tools limit addressable market significantly. Mac and Linux developers represent a large portion of the developer community.
**Implementation:**

- **Unix/Mac compatibility (Item 38)** - HIGH PRIORITY (Q1 2026)
- **Multi-OS testing (Item 39)** - HIGH PRIORITY (Q1 2026)
- **Tutorial expansion (Item 36)** - CRITICAL (Q4 2025)
**Impact:** 3x market size potential, better adoption, reduced onboarding friction

### Theme 4: Revenue Generation

**Rationale:** Revenue funds future development, validates product-market fit, and enables sustainable growth.
**Implementation:**

- **Documentation service (Items 27-32)** - IN PROGRESS (Q4 2025)
- **Code review service (Item 42)** - FUTURE (Q2 2026)
- **Bot marketplace** - FUTURE (2026+)
**Impact:** Sustainability, growth funding, market validation, competitive advantage proof

---

## Decision Framework

### When to Start New Work

**Criteria:**

1. **Alignment:** Does it align with current quarter strategic goals?
2. **Unblocking:** Does it unblock revenue generation or market reach?
3. **Foundation:** Are dependencies complete and foundation ready?
4. **Capacity:** Do we have bandwidth without overcommitting?
**Priority Levels:**

- **CRITICAL:** Blocks revenue, causes significant user pain, or prevents market access
- **HIGH:** Enables strategic theme, unlocks major capability, or industry standard
- **MEDIUM:** Improves user experience, increases efficiency, or nice capability addition
- **LOW:** Nice-to-have, future consideration, or can be deferred

### When to Defer Work

**Criteria:**

1. **Misalignment:** Doesn't align with strategic themes or current quarter goals
2. **Dependencies:** Foundation not ready or missing critical dependencies
3. **ROI:** Low impact relative to effort required
4. **Standards:** Can be achieved via industry standards (don't build it ourselves)

---

## Resource Allocation

### Current Capacity

- **Development:** Active (12 PRs in last 3 weeks, strong velocity)
- **Testing:** Strong (965+ tests passing, robust infrastructure)
- **Documentation:** Weak (only 1 minimal tutorial, needs 7+ comprehensive tutorials)

### Recommended Allocation (Q4 2025)

- **40%** - Documentation service completion (test fixes, auth/billing, deployment)
- **30%** - Tutorial expansion and documentation (7 tutorials, ~21 hours)
- **20%** - Cross-platform support groundwork (planning, initial implementation)
- **10%** - MCP integration research and Phase 1 planning

### Recommended Allocation (Q1 2026)

- **40%** - Cross-platform support (Unix/Mac compatibility, multi-OS CI)
- **30%** - MCP Client integration
- **20%** - Documentation service optimization and scaling
- **10%** - LiteLLM integration

---

## Risk Management

### Top Risks

**1. Revenue Timeline Slipping**

- **Risk:** Documentation service not production-ready, delaying revenue
- **Impact:** HIGH - Delays funding for future development
- **Mitigation:** Focus 40% capacity on completion, 8-12 hour sprint to 95% test pass rate
- **Contingency:** Simplify MVP scope, launch with manual billing, iterate quickly
**2. Adoption Barrier (Tutorial Gap)**
- **Risk:** Steep learning curve due to insufficient tutorials/documentation
- **Impact:** HIGH - Limits user acquisition and retention
- **Mitigation:** Create 7 comprehensive tutorials (~21 hours total effort)
- **Contingency:** Video tutorials, interactive demos, community-driven documentation
**3. Platform Limitation**
- **Risk:** Windows-only excludes Mac/Linux developers (significant market segment)
- **Impact:** MEDIUM-HIGH - Limits addressable market by ~50-60%
- **Mitigation:** Q1 2026 priority for shell abstraction + multi-OS CI matrix
- **Contingency:** Document WSL workarounds, focus on Windows market initially
**4. Ecosystem Isolation**
- **Risk:** Missing MCP integration as industry standardizes around it
- **Impact:** MEDIUM - Reduces interoperability and ecosystem participation
- **Mitigation:** Q1 2026 MCP Client implementation, Q2 2026 MCP Server
- **Contingency:** Direct integrations with key tools (Claude Desktop, Cursor)

---

## Success Metrics

### Technical Metrics

- **Test pass rate:** Maintain 95%+ (currently 965+ tests passing)
- **Cross-platform:** Windows, Linux, macOS support (currently Windows only)
- **Provider support:** 100+ providers via LiteLLM (currently 3 manual implementations)
- **MCP compatibility:** Client + Server (currently none)
- **Code coverage:** 80%+ across core modules

### Business Metrics

- **Documentation service customers:** 10 by Q4 2025, 50 by Q2 2026
- **Monthly recurring revenue:** $5k Q4 2025, $10k Q1 2026, $20k Q2 2026
- **Tutorial completion:** 7 comprehensive tutorials by Q4 2025
- **GitHub stars:** 500+ (measure of adoption and community interest)
- **Customer retention:** 90%+ monthly retention rate

### Community Metrics

- **Contributors:** 5+ active contributors by Q2 2026
- **Issue response time:** <1 week average response time
- **Documentation quality:** User feedback score 4+/5
- **Community engagement:** Active discussions, feature requests, contributions

---

## Quarterly Review Process

**When:** End of each quarter (December 2025, March 2026, June 2026)
**Review Agenda:**

1. Assess progress against strategic priorities
2. Evaluate success metrics (technical, business, community)
3. Identify blockers, risks, and mitigation effectiveness
4. Adjust priorities and resource allocation for next quarter
5. Update this strategic roadmap document
**Participants:** Core development team + key stakeholders
**Outputs:**

- Updated strategic roadmap
- Adjusted priorities for next quarter
- Risk assessment and mitigation plans
- Resource allocation adjustments

---

## Navigation

**Detailed Planning:**

- [Item Index](ITEM_INDEX.md) - Searchable index of all roadmap items
- [Active Work](README.md) - Current phase status and quick navigation
- [Phase 1: Foundation](active/phase1_foundation.md) - Infrastructure and critical fixes
- [Phase 2: Features](active/phase2_features.md) - Core features and expansion
- [Phase 3: Enhancement](active/phase3_enhancement.md) - UX improvements
- [Phase 4: Revenue](active/phase4_revenue.md) - Documentation service
**Strategic Context:**
- [Philosophy](PHILOSOPHY.md) - Development philosophy and strategic direction details
- [Monetization](MONETIZATION.md) - Business model and revenue strategy details
**Major Initiatives:**
- [Observability](initiatives/observability.md) - OpenTelemetry, callbacks, metrics
- [Cross-Platform Support](initiatives/cross_platform.md) - Unix/Mac compatibility
- [MCP Integration](initiatives/mcp_integration.md) - Model Context Protocol
- [Documentation Service](initiatives/documentation_service.md) - GitHub docs app
- [CLI Improvements](initiatives/cli_improvements.md) - Command-line enhancements
- [Test Infrastructure](initiatives/test_infrastructure.md) - Testing improvements
**Historical Record:**
- [October 2025 Completions](completed/2025-10_foundation.md)
- [November 2025 Completions](completed/2025-11_infrastructure.md)

---
**Document Owner:** Ben Rinauto
**Next Review:** March 31, 2026
**Last Updated:** December 18, 2025
