# CI/CD Pipeline Commands Reference for Claude
This document provides essential commands for accessing information from GitHub Actions CI/CD pipeline runs.
## Essential Commands
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
