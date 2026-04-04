# PR###: [Descriptive Title]

**Project**: [Project Name]
**Created**: [Date]
**Target PR**: [Feature branch → main/dev]

---

## Objective

[What this PR will accomplish and why it should be merged]

---

## Definition of Done

- [ ] PR created with clear description
- [ ] All tests pass locally
- [ ] Code committed and pushed
- [ ] CodeRabbit review completed and addressed
- [ ] Poggio documentation updates applied and pulled
- [ ] All remote CI tests pass
- [ ] Manual testing completed for core functionality
- [ ] PR approved and ready for merge

---

## Branching Plan

**Pattern**: Sequential with iterative refinement

**Phase 1**: PR Creation
- Create feature branch and implement changes
- Write clear PR description with context

**Phase 2**: Local Testing & Debugging
- Run full test suite locally
- Use per-file branching to fix test failures
- Commit and push when all tests pass

**Phase 3**: Remote Integration Loop
- Wait for automated tools (CodeRabbit, Poggio, CI)
- Pull any updates and address feedback
- Repeat until no changes required

**Phase 4**: Final Review & Merge
- Manual functionality testing
- Final approval and merge

**File Assignments**:
- Phase 1: All implementation files
- Phase 2: Test fixes per file (NO OVERLAP between file branches)
- Phase 3: Tool feedback integration (NO OVERLAP)
- Phase 4: Manual validation only

**Coordination**: Let automated tools complete before manual review

---

## Context & Constraints

**Background**: [Link to related issues or context]

**Implementation Type**: [Feature/Bugfix/Refactor/Documentation]
**Breaking Changes**: [Yes/No - describe if yes]

**Testing Focus**:
- [Main functionality to test]
- [Edge cases to verify]
- [Integration points to check]

---

## Phase 1: PR Creation

### Create Feature Branch
```powershell
# Create and switch to feature branch
git checkout -b feature/[descriptive-name]

# Implement your changes
# [Implementation work happens here]

# Stage changes
git add .
git status  # Review what's being committed
```

### Create PR
```powershell
# Push feature branch
git push origin feature/[descriptive-name]

# Create PR with GitHub CLI
gh pr create --title "[Descriptive Title]" --body "
## What This Does
[Clear description of changes]

## Why This Matters
[Business/technical justification]

## Testing Done
[Local testing performed]

## Breaking Changes
[None/List any breaking changes]
"

# Get the PR number for reference
gh pr view --json number | ConvertFrom-Json | Select-Object -ExpandProperty number
```

---

## Phase 2: Local Testing & Debugging

### Run Full Test Suite
```powershell
# Run all tests locally (adjust for your project)
pytest --tb=short -v  # Python projects
# npm test  # Node.js projects
# make test  # Make-based projects

# Note which specific files have test failures
```

### Fix Test Failures (Per-File Branching)
```python
# Use branch_self to fix test failures in parallel
# Only include files that actually have failures
branch_self([
    "Fix test failures in [specific_test_file.py] - focus only on this file",
    "Fix test failures in [another_test_file.py] - focus only on this file"
], allow_work=True, parallel=True)
```

### Commit When Tests Pass
```powershell
# Verify all tests pass locally
pytest  # Must be green before proceeding

# Commit and push
git add .
git commit -m "[Descriptive commit message]

- [Specific change 1]
- [Specific change 2]"

git push origin feature/[descriptive-name]
```

---

## Phase 3: Remote Integration Loop

### Wait for Automated Tools (10 minutes)
```powershell
# Wait 10 minutes for tools to complete:
# - CodeRabbit: ~2-5 minutes
# - Poggio: ~5-10 minutes
# - CI: varies by project

Start-Sleep 600  # 10 minutes
```

### Check CodeRabbit Comments (Context-Protected)
```powershell
# Count CodeRabbit comments (Windows PowerShell)
$coderabbitCount = gh pr view --json comments | ConvertFrom-Json | Where-Object {$_.user.login -eq "coderabbitai"} | Measure-Object | Select-Object -ExpandProperty Count
Write-Host "CodeRabbit comments: $coderabbitCount"

# Check for Poggio comments too
$poggioCount = gh pr view --json comments | ConvertFrom-Json | Where-Object {$_.user.login -eq "poggio-bot"} | Measure-Object | Select-Object -ExpandProperty Count
Write-Host "Poggio comments: $poggioCount"
```

### Pull Poggio Updates (Context-Protected)
```powershell
# Pull any documentation updates from Poggio
git pull origin feature/[descriptive-name]

# Check what changed (names only, not content)
git log --oneline -3
git diff HEAD~1 --name-only
```

### Check CI Status (Context-Protected)
```powershell
# Get CI status summary (Windows PowerShell)
$checks = gh pr checks --json | ConvertFrom-Json
$checks | Select-Object name, conclusion | Format-Table

# Count failed checks
$failedCount = $checks | Where-Object {$_.conclusion -eq "failure"} | Measure-Object | Select-Object -ExpandProperty Count
Write-Host "Failed checks: $failedCount"
```

### Address Issues and Repeat
```powershell
# If issues found:
# 1. Address CodeRabbit suggestions
# 2. Review Poggio updates
# 3. Fix CI failures

# After making changes:
git add .
git commit -m "Address automated feedback: [specific changes]"
git push origin feature/[descriptive-name]

# Wait 10 minutes and repeat until no changes needed
Start-Sleep 600
```

---

## Phase 4: Final Review & Merge

### Final Status Check (Context-Protected)
```powershell
# Get summary status only
$prStatus = gh pr view --json state,mergeable | ConvertFrom-Json
Write-Host "PR State: $($prStatus.state)"
Write-Host "Mergeable: $($prStatus.mergeable)"

# Verify no remaining failures
$checks = gh pr checks --json | ConvertFrom-Json
$failedCount = $checks | Where-Object {$_.conclusion -ne "success"} | Measure-Object | Select-Object -ExpandProperty Count
Write-Host "Non-success checks: $failedCount"
```

### Manual Testing
- [ ] Core functionality works as expected
- [ ] No obvious regressions introduced
- [ ] Breaking changes are intentional and documented
- [ ] Integration points function correctly

### Merge Decision
```powershell
# If everything is clean:
gh pr merge --squash  # or --merge or --rebase

# Or check status first:
gh pr status
```

---

## Execution Log

| Phase | Status | Completed | Notes |
|-------|--------|-----------|-------|
| PR Creation | ⬜ Not Started | | |
| Local Testing | ⬜ Not Started | | |
| Remote Integration | ⬜ Not Started | | |
| Final Review | ⬜ Not Started | | |

**Status Legend**: ⬜ Not Started | 🔄 In Progress | ✅ Complete | ❌ Issues Found | 🔄 Iterating

---

## Integration Loop Tracker

### Iteration 1
- [ ] CodeRabbit: [Comment count/Status]
- [ ] Poggio: [Files updated/None]
- [ ] CI Tests: [Pass count/Fail count]
- [ ] Changes Made: [Yes/No - brief description]

### Iteration 2 (if needed)
- [ ] CodeRabbit: [Comment count/Status]
- [ ] Poggio: [Files updated/None]
- [ ] CI Tests: [Pass count/Fail count]
- [ ] Changes Made: [Yes/No - brief description]

---

## Windows PowerShell Notes

**Verified Commands**:
- `ConvertFrom-Json` instead of `jq` for JSON parsing
- `Where-Object` instead of `grep` for filtering
- `Select-Object -ExpandProperty` for extracting values
- `Measure-Object` for counting
- `Start-Sleep 600` for 10-minute waits
- `Format-Table` for readable output

**Context Protection**:
- Count objects instead of displaying full content
- Use `--name-only` for git diffs
- Limit git log to recent commits only
- Focus on summaries and metrics

**Bot Context Management**:
- Branch per test file to isolate fixes
- Use iteration tracking to avoid infinite loops
- Focus on actionable summaries, not verbose output
- Wait periods prevent overwhelming automated systems
