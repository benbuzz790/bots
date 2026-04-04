# Branching Patterns Reference

This document provides detailed examples of common branching strategies for work order execution.

---

## Common Patterns

### 1. Gather-then-Parallel
Gather context first, then branch on each file/task. Clean and keeps branches coordinated.

### 2. Multi-Layer Hierarchy
Identify submodules, define ICDs, define requirements, then branch to implement (may recurse).

### 3. Sequential with Verification
Do work in sequence, verify at each step.

### 4. Parallel with Stitching
Parallel work followed by integration/verification branch.

### 5. Hypothesis Branching
```pattern
Gather initial context → Formulate hypotheses → Branch in parallel →
Synthesize findings ( → If debugging, Implement fix → Verify)
```
---

## Example 1: Gather-then-Parallel

**Best for**: Multiple independent files that need similar changes

**Phase 1 - Context Gathering** (main thread):
- Gather requirements
- Understand codebase
- Identify files to modify

**Phase 2 - Parallel Implementation**:
```python
branch_self([
  "Fix file1.py: [specific task]",
  "Fix file2.py: [specific task]",
  "Fix file3.py: [specific task]"
], allow_work=True, parallel=True, recombine='concatenate')
```

**Phase 3 - Verification** (stitching branch):
```python
branch_self([
  "Verify all changes work together, run tests, check requirements"
], allow_work=True)
```

**File Assignments**:
- Branch 1: file1.py
- Branch 2: file2.py
- Branch 3: file3.py
- Verification: runs tests, no file edits

**Key Points**:
- Context gathering prevents branches from duplicating work
- Each branch has clear file ownership (NO OVERLAP)
- Verification branch ensures integration works
- Branches report results in final text block

---

## Example 2: Multi-Layer Hierarchy

**Best for**: Large projects with clear module boundaries, requires good SPEC.md

**Phase 1 - Architecture** (main thread):
1. Identify submodules from SPEC.md
2. Define ICDs (Interface Control Documents) between submodules
3. Define requirements for each submodule

**Phase 2 - Submodule Implementation** (hierarchical branching):
```python
branch_self([
  "Implement Module A (may branch further into files)",
  "Implement Module B (may branch further into files)",
  "Implement Module C (may branch further into files)"
], allow_work=True, parallel=True, recombine='concatenate')
```

Each submodule branch may itself:
- Break down into smaller components
- Define internal interfaces
- Branch again at the file level

**Phase 3 - Hierarchical Stitching**:
```python
branch_self([
  "Integrate Module A + Module B, verify ICD compliance",
  "Integrate Module C with A+B, verify system requirements",
  "Run full test suite, verify Definition of Done"
], allow_work=True, parallel=False, recombine='concatenate')
```

**File Assignments**:
- Module A branches: [files in module A]
- Module B branches: [files in module B] (NO OVERLAP with A)
- Module C branches: [files in module C] (NO OVERLAP with A, B)

**Key Points**:
- ICDs defined BEFORE implementation begins
- Hierarchical decomposition continues until file level
- Stitching happens hierarchically (integrate pairs, then combine)
- Each level verifies its contracts/interfaces

---

## Example 3: Sequential with Checkpoints

**Best for**: Tasks with strong dependencies, exploratory work

**Phase 1**: [First task]
- Do work
- Verify completion
- Report findings

**Phase 2**: [Second task, depends on Phase 1]
- Use results from Phase 1
- Do work
- Verify completion

**Phase 3**: [Final integration]
- Combine all work
- Run full tests

**Key Points**:
- Each phase completes before next begins
- Good for when you don't know requirements upfront
- Less parallelism but more flexibility

---

## Example 4: Parallel with Stitching

**Best for**: Independent tasks that need final integration

**Phase 1 - Parallel Work**:
```python
branch_self([
  "Task A: [description]",
  "Task B: [description]",
  "Task C: [description]"
], allow_work=True, parallel=True, recombine='concatenate')
```

**Phase 2 - Stitching**:
```python
branch_self([
  "Integrate A+B+C, resolve conflicts, verify system works"
], allow_work=True)
```

**Key Points**:
- Maximum parallelism upfront
- Single stitching phase at end
- Good when tasks are mostly independent

---

## Ground Rules (Universal)

1. **Clear Definition of Done**: Each branch must have explicit, measurable completion criteria
2. **Report in Text**: Branches report results in their final text block, not in files
3. **Concatenate by Default**: Use 'concatenate' recombination unless specific reason otherwise
4. **No File Conflicts**: Two branches must never interact with the same file
5. **Explicit File Assignment**: List exactly which files each branch will modify
6. **Context First**: Gather context before parallel branching
7. **Stitch After Parallel**: Use stitching/verification branches after parallel work
8. **ICDs for Hierarchy**: For hierarchical branching, define ICDs first

---

## Choosing a Pattern

**Use Gather-then-Parallel when**:
- Multiple files need similar changes
- Changes are independent
- You know what needs to be done upfront

**Use Multi-Layer Hierarchy when**:
- Project is large with clear modules
- You have a good SPEC.md
- Modules have well-defined interfaces

**Use Sequential when**:
- Strong dependencies between tasks
- Exploratory work where requirements emerge
- Need to make decisions based on previous results

**Use Parallel with Stitching when**:
- Tasks are mostly independent
- Want maximum parallelism
- Integration is straightforward
