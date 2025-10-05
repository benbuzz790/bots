# CI/CD Pipeline Commands Reference for Claude
This document provides essential commands for accessing information from GitHub Actions CI/CD pipeline runs.
## Essential Commands

### 0. Running linters
Run all linters to match CI checks:
```powershell
black --check --diff .
isort --check-only --diff .
flake8 . --count --statistics --show-source
```

To auto-fix formatting issues:
```powershell
black .
isort .
python -m bots.dev.remove_boms
```

### 1. View PR Check Status
Get a quick overview of all checks for a PR:
```powershell
gh pr checks <PR_NUMBER>
```
### 2. View Detailed Run Logs
Get the full logs from a specific workflow run:
```powershell
gh run view <RUN_ID> --log
```
**Tip:** Get the RUN_ID from the URL in gh pr checks output.

---
### 3. View Only Failed Logs
Get just the failed job logs:
```powershell
gh run view <RUN_ID> --log-failed
```

---
### 4. Search Logs for Specific Patterns
Filter logs to find specific errors or patterns:
```powershell
gh run view <RUN_ID> --log | Select-String -Pattern "error|FAILED|would reformat" -Context 0,2
```
**Example - Find formatting issues:**
```powershell
gh run view 18234577748 --log | Select-String -Pattern "would reformat" -Context 1,3
```
**Example - Find test failures:**
```powershell
gh run view 18234577748 --log-failed | Select-String -Pattern "FAILED|AssertionError" -Context 0,2
```

---
### 5. View PR Comments (including CodeRabbit)
View all comments on a PR:
```powershell
gh pr view <PR_NUMBER> --comments
```

---
## Common Patterns
### Check if PR is ready to merge
```powershell
gh pr checks <PR_NUMBER> | Select-String -Pattern "pass|fail"
```
### Get summary of test failures
```powershell
gh run view <RUN_ID> --log | Select-String -Pattern "FAILED tests/" -Context 0,1
```
### Check Black formatting issues
```powershell
gh run view <RUN_ID> --log | Select-String -Pattern "would reformat" -Context 2,5
```
### Check flake8 linting issues
```powershell
gh run view <RUN_ID> --log | Select-String -Pattern "E[0-9]{3}|F[0-9]{3}" -Context 0,1
```

---

### 6. Extract CodeRabbit AI Prompts
Extract actionable AI prompts from CodeRabbit review comments:
```powershell
python -m bots.dev.pr_comment_parser <REPO> <PR_NUMBER>
```
**Example:**
```powershell
python -m bots.dev.pr_comment_parser owner/repo 123
```
**Save to file:**
```powershell
python -m bots.dev.pr_comment_parser owner/repo 123 output.txt
```
This tool extracts the "🤖 Prompt for AI Agents" sections from CodeRabbit comments, filtering out outdated comments and including both regular and inline review comments.

---
