# CI/CD Strategy - Multi-Tier Approach
## Overview
This project uses a **three-tier CI/CD strategy** designed to balance fast feedback with comprehensive testing. The goal is to enable rapid iteration while maintaining code quality.
## The Three Tiers
### Tier 1: Fast Checks (~5 minutes) ✅ REQUIRED FOR MERGE
**Purpose:** Catch obvious errors quickly and provide immediate feedback.
**Runs on:** Every push and pull request
**Blocks merges:** YES - must pass to merge
**What it checks:**
- Code formatting (Black, isort)
- Linting (flake8)
- Fast unit tests (no API calls, no slow tests)
- Basic import and syntax validation
**When to use:**
- Every commit
- Small fixes and typos
- Documentation updates
- Refactoring work
**Timeout:** 10 minutes
**Platform:** Ubuntu (faster than Windows for linting)
---
### Tier 2: Full Test Suite (75-120 minutes) ℹ️ INFORMATIONAL
**Purpose:** Comprehensive testing including integration tests with real APIs.
**Runs on:**
- Pull requests
- Nightly schedule (2 AM)
**Blocks merges:** NO - results inform but don't block
**What it checks:**
- All unit tests
- Integration tests with live APIs (OpenAI, Anthropic, Gemini)
- Serial tests (race condition sensitive)
- Encoding tests
- Windows-specific behavior
**When to use:**
- Feature branches before merge
- Monitoring overall health
- Investigating test failures in batches
**Timeout:** 120 minutes
**Platform:** Windows (primary target platform)
---
### Tier 3: Deep Integration Tests (Weekly) 📊 NEVER BLOCKS
**Purpose:** Catch regressions over time, expensive/flaky tests, cross-platform validation.
**Runs on:**
- Weekly schedule (Sunday 3 AM)
- Manual trigger for releases
**Blocks merges:** NO - purely informational
**What it checks:**
- Cross-platform matrix (Windows, Ubuntu, macOS)
- Multiple Python versions
- Long-running integration scenarios
- Flaky tests with retries
- Performance benchmarks
**When to use:**
- Pre-release validation
- Long-term regression monitoring
- Platform compatibility verification
**Timeout:** No limit (can run for hours)
**Platform:** Matrix (all platforms)
---
## Workflow Decision Tree
`
┌─────────────────────────────────────┐
│ What are you working on?            │
└─────────────────────────────────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
    ▼            ▼            ▼
┌────────┐  ┌─────────┐  ┌──────────┐
│ Typo/  │  │ Feature │  │ Bug Fix  │
│ Docs   │  │ Branch  │  │          │
└────────┘  └─────────┘  └──────────┘
    │            │            │
    ▼            ▼            ▼
Push to     Open PR      Open PR
main        │            │
│           ▼            ▼
▼       Wait 5min    Wait 5min
Tier 1  Tier 1       Tier 1
passes  passes       passes
│       │            │
▼       ▼            ▼
MERGE   MERGE        MERGE
        │            │
        ▼            ▼
    Tier 2       Tier 2
    runs         runs
    nightly      nightly
    (monitor)    (monitor)
`
## Rationale
### Why Three Tiers?
1. **Fast Feedback Loop:** Developers need to know within minutes if their change breaks something obvious. Waiting 2 hours for linting feedback kills productivity.
2. **Real Integration Testing:** Some bugs only appear with real API calls, real file I/O, and real Windows encoding issues. These tests are slow but necessary.
3. **Flaky Test Isolation:** Some tests are flaky or expensive. Running them weekly prevents them from blocking daily work while still catching regressions.
### Why Tier 2 Doesn't Block?
- Tests take 75-120 minutes (too slow for rapid iteration)
- Some tests are flaky (random failures)
- Integration tests depend on external APIs (can fail due to rate limits, network issues)
- Developers dogfood this tool to build this tool - need to keep it sharp even during debugging quests
**Philosophy:** It's better to merge working code quickly and fix test failures in batches than to block all progress waiting for perfect CI.
## Branch Strategy Alignment
- **main branch:** Protected by Tier 1 only
- **dev branch:** No protection (anything goes)
- **feature/* branches:** Tier 1 required, Tier 2 informational
- **fix/* branches:** Tier 1 required, Tier 2 informational
- **debug/* branches:** No CI requirements (long-term debugging)
## Migration Path
### Current State
- Single CI workflow (main.yml) with 75-120 minute timeout
- All tests required for merge
- Flaky tests block progress
### Target State
- Tier 1: Fast Checks (5 min, required) ✅
- Tier 2: Full Tests (120 min, informational) ✅
- Tier 3: Weekly Deep Tests (scheduled) 🔄
### Implementation Steps
1. ✅ Create fast-checks.yml
2. ✅ Add pytest markers (slow, integration, api, flaky)
3. ✅ Update main.yml to be non-blocking
4. ✅ Update branch protection rules
5. 🔄 Create weekly-deep-tests.yml
6. 🔄 Mark existing tests with appropriate markers
## Monitoring
- **Tier 1 failures:** Fix immediately (blocks merges)
- **Tier 2 failures:** Review daily, fix in batches
- **Tier 3 failures:** Review weekly, investigate trends
## Success Metrics
- Time to merge: < 10 minutes (down from 120 minutes)
- False positive rate: < 5% (flaky tests isolated)
- Regression detection: Within 24 hours (nightly Tier 2)
- Developer happiness: ∞ (no more 2-hour CI waits)
---
**Last Updated:** 2026-04-03
**Status:** Implementation in progress
