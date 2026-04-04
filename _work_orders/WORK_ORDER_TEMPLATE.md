# WO###: [Descriptive Title]

**Project**: [Project Name]
**Created**: [Date]
**Priority**: [High/Medium/Low]

---

## Objective

[Clear, concise statement of what needs to be accomplished]

---

## Definition of Done

- [ ] [Specific, measurable criterion 1]
- [ ] [Specific, measurable criterion 2]
- [ ] [Specific, measurable criterion 3]
- [ ] All tests pass
- [ ] Changes committed to git

---

## Branching Plan

**Pattern**: [Gather-then-parallel / Multi-layer hierarchy / Sequential / Custom]

**Phases**:

**Phase 1**: [Description]
- [What happens]
- [branch_self call if applicable]

**Phase 2**: [Description]
- [What happens]
- [branch_self call if applicable]

**Phase 3**: [Description]
- [What happens]
- [branch_self call if applicable]

**File Assignments**:
- Phase/Branch 1: [files]
- Phase/Branch 2: [files] (NO OVERLAP)
- Phase/Branch 3: [files] (NO OVERLAP)

**Coordination**: [ICDs, dependencies, sequencing requirements]

---

## Context & Constraints

**Background**: [Relevant context, links to SPEC.md sections]

**Requirements**:
- [Requirement 1]
- [Requirement 2]

**Constraints**:
- [Constraint 1]
- [Constraint 2]

---
## Execution Log

<!-- Update this section as work progresses -->

| Phase | Status | Completed | Notes |
|-------|--------|-----------|-------|
| Phase 1 | ⬜ Not Started | | |
| Phase 2 | ⬜ Not Started | | |
| Phase 3 | ⬜ Not Started | | |

**Status Legend**: ⬜ Not Started | 🔄 In Progress | ✅ Complete | ❌ Blocked | ⏭️ Skipped

---

## Completion Protocol

### During Execution

As each task/subtask completes:
1. Check off the corresponding item in **Definition of Done**
2. Update the **Execution Log** table with status and timestamp
3. Add any relevant notes or issues encountered

### Upon Work Order Completion

When all Definition of Done items are checked:

1. **Update Status Header**:
   - Add `**STATUS**: ✅ COMPLETE` after the title
   - Add `**Completed**: [Date]`

2. **Write Completion Summary**:
   ```
   ## Completion Summary

   **Completed**: [Date/Time]
   **Token Usage**: [If tracked]
   **Iterations**: [If tracked]

   ### What Was Done
   - [Bullet points of accomplishments]

   ### Issues Encountered
   - [Any problems and how they were resolved]

   ### Follow-up Items
   - [Any items for future work orders]
   ```

3. **Archive**: Move completed work order to `_work_orders/archive/`

---


## Notes

[Additional considerations for the project agent]

See BRANCHING_PATTERNS.md for detailed examples of branching strategies.
