# Agent Development Guidelines
This document provides guidance for AI agents working on this project. These principles ensure consistent, high-quality development practices.
## Core Development Principles
### 1. Incremental Development
**Keep changes small and focused:**
- Break large changes into smaller, manageable pieces
- Work within token limits by making incremental edits
- Test each increment before moving to the next
**Why:** Large changes increase the risk of errors and make debugging difficult. Small, focused changes are easier to review, test, and roll back if needed.
### 2. Explicit Path Management
**Use full relative paths:**
- Avoid `cd` commands in terminal operations
- Always specify complete relative paths for file operations
- Terminal state is stateful and can cause unexpected behavior
**Why:** Explicit paths ensure predictable, reproducible operations regardless of current working directory state.
### 3. YAGNI and KISS
**You Aren't Gonna Need It (YAGNI):**
- Don't add features until they're actually needed
- Resist the temptation to build for hypothetical future requirements
- Focus on current, concrete requirements
**Keep It Simple, Stupid (KISS):**
- Prefer simple solutions over complex ones
- Avoid over-engineering
- Choose clarity over cleverness
**Why:** Simpler code is easier to understand, maintain, debug, and extend. Premature optimization and feature creep lead to unnecessary complexity.
### 4. Defensive Programming (NASA Methodology)
**Build robust, reliable code:**
- Always validate inputs and check types
- Always validate outputs before returning
- Use asserts *in production code*
- Fail gracefully with clear diagnostic information
**Why:** Based on NASA's defensive assert methodology, this approach catches errors early, provides clear diagnostics, and ensures systems fail safely rather than silently.
## Implementation Checklist
When working on any task, ensure:
- [ ] Changes are broken into small, reviewable increments
- [ ] All file operations use explicit relative paths
- [ ] No unnecessary features or complexity added
- [ ] Input validation and type checking implemented
- [ ] Error handling with meaningful messages included
- [ ] Appropriate logging added for debugging
- [ ] Output validation confirms expected results
- [ ] Code is simple and maintainable
## Testing Standards
- Write tests for new functionality
- Ensure tests are deterministic and reproducible
- Use fixtures for complex test data
- Test error cases, not just happy paths
- Keep test code as clean as production code
## Documentation Standards
- Document why, not just what
- Keep documentation close to code
- Update docs when changing functionality
- Include examples for complex features
- Write for future maintainers (including yourself)
---
*These guidelines apply to all development work on this project. Individual tasks may have additional specific requirements.*
