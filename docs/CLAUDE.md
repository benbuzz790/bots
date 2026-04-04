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

**Best Practices for Linting**

- Run linters without output truncation and exactly as shown above

### 1. Running PRs

```powershell
gh pr checks <PR_NUMBER>
gh run view <RUN_ID> --log-failed
gh run view <RUN_ID> --log | Select-String -Pattern "error|FAILED|would reformat|AssertionError|E[0-9]{3}|F[0-9]{3}" -Context x,y
gh pr comment <PR_NUMBER> --body "## Update:..."

```

**Tip:** Get the RUN_ID from the URL in gh pr checks output.
**Please:** Always submit an update comment.

---

### 2. Extract CodeRabbit AI Prompts

Extract actionable AI prompts from CodeRabbit review comments:

```powershell
python -m bots.dev.pr_comment_parser <REPO> <PR_NUMBER>
python -m bots.dev.pr_comment_parser "owner/repo" 123
```

This tool extracts the "🤖 Prompt for AI Agents" sections from the most recent CodeRabbit comments.

---

### Issue: Version Mismatch

The CI workflow (`.github/workflows/pr-checks.yml` line 117) installs linters without version pinning:

```yaml
pip install black isort flake8 mypy
```

This can cause CI to detect issues that local linters miss due to version differences.
Regularly update local linters to match CI: `pip install --upgrade black isort flake8`

---
