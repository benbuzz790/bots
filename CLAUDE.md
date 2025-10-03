# CI/CD Pipeline Commands Reference for Claude
This document provides essential commands for accessing information from GitHub Actions CI/CD pipeline runs.
## Prerequisites
- GitHub CLI (gh) must be installed and authenticated
- Token must have appropriate scopes (see token update section below)
## Essential Commands
### 1. View PR Check Status
Get a quick overview of all checks for a PR:
```powershell
gh pr checks <PR_NUMBER>
```
**Example:**
```powershell
gh pr checks 110
```
**Output:** Shows all checks with their status (pass/fail/pending), duration, and links.
---
### 2. View Detailed Run Logs
Get the full logs from a specific workflow run:
```powershell
gh run view <RUN_ID> --log
```
**Example:**
```powershell
gh run view 18234577748 --log
```
**Tip:** Get the RUN_ID from the URL in gh pr checks output.
---
### 3. View Only Failed Logs
Get just the failed job logs:
```powershell
gh run view <RUN_ID> --log-failed
```
**Example:**
```powershell
gh run view 18234577748 --log-failed
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
**Example:**
```powershell
gh pr view 110 --comments
```
---
### 6. List Recent Workflow Runs
See recent runs for the repository:
```powershell
gh run list --limit 10
```
---
### 7. Watch Run in Real-Time
Watch a run's progress in real-time:
```powershell
gh run watch <RUN_ID>
```
---
### 8. Download Artifacts
Download artifacts (like coverage reports) from a run:
```powershell
gh run download <RUN_ID>
```
---
## Common Patterns
### Check if PR is ready to merge
```powershell
gh pr checks <PR_NUMBER> | Select-String -Pattern "pass|fail"
```
### Find specific error in failed run
```powershell
gh run view <RUN_ID> --log-failed | Select-String -Pattern "Error code:|AssertionError:" -Context 1,2
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
## Updating GitHub Token
If you need to update your GitHub token (e.g., for additional scopes):
```powershell
# Set token for current session
$env:GH_TOKEN = "ghp_YourNewTokenHere"
# Verify token is working
gh auth status
```
**Required scopes for full functionality:**
- epo - Full repository access
- workflow - Workflow access
- ead:org - Read organization data (for PR comments)
---
## Troubleshooting
### "Token has not been granted required scopes"
Update your token with the necessary scopes at: https://github.com/settings/tokens
### "Run is still in progress"
Wait a few moments and try again, or use gh run watch <RUN_ID> to monitor.
### Timeout errors
Some commands may timeout on very long logs. Use Select-Object -First N to limit output:
```powershell
gh run view <RUN_ID> --log | Select-String -Pattern "error" | Select-Object -First 50
```
---
## Quick Reference Card
| Task | Command |
|------|---------|
| Check PR status | gh pr checks <PR#> |
| View all logs | gh run view <RUN_ID> --log |
| View failed logs only | gh run view <RUN_ID> --log-failed |
| Search for errors | gh run view <RUN_ID> --log \| Select-String "error" |
| View PR comments | gh pr view <PR#> --comments |
| Watch run live | gh run watch <RUN_ID> |
| Download artifacts | gh run download <RUN_ID> |
---
**Last Updated:** 2025-10-03 16:07:10
