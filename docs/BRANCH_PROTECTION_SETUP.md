# Branch Protection Setup Guide

## Overview

Branch protection rules are essential safeguards that ensure code quality and prevent accidental or unauthorized changes to critical branches. This guide walks you through setting up comprehensive branch protection for the `main` branch of the bots repository.

### What Branch Protection Provides

**Quality Assurance:**
- Prevents broken code from reaching main branch
- Ensures all changes are tested before merge
- Maintains consistent code quality standards
- Catches issues early through automated checks

**Safety:**
- No accidental direct pushes to main
- All changes reviewed before merge
- Easy rollback with clean git history
- Protects against force pushes

**Collaboration:**
- Clear pull request workflow
- Structured code review process
- Discussion and knowledge sharing
- Automated AI-assisted reviews

## Prerequisites

Before setting up branch protection, ensure you have:

1. **Repository Admin Access**: You must be a repository owner or have admin permissions
2. **Working CI/CD Pipeline**: The `.github/workflows/pr-checks.yml` workflow should be in place
3. **API Keys Configured**: GitHub repository secrets for `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY` (for tests)
4. **CodeRabbit Account**: Free for open source projects (we'll set this up in Step 2)

## Step 1: Configure Branch Protection Rules

### Access Branch Protection Settings

1. Navigate to your repository on GitHub: `https://github.com/benbuzz790/bots`
2. Click **Settings** (top navigation bar)
3. In the left sidebar, click **Branches** (under "Code and automation")
4. Click **Add branch protection rule** (or **Add rule**)

### Configure Protection Rules

**Branch name pattern:**
```
main
```

**Enable the following protections:**

#### Protect matching branches
- ☑ **Require a pull request before merging**
  - Require approvals: **1**
  - ☑ Dismiss stale pull request approvals when new commits are pushed
  - ☑ Require review from Code Owners (optional, if you have a CODEOWNERS file)

#### Status checks
- ☑ **Require status checks to pass before merging**
  - ☑ Require branches to be up to date before merging
  - **Note:** Status checks to require will be configured in Step 3 (after first PR runs)

#### Additional protections
- ☑ **Require conversation resolution before merging**
- ☑ **Require signed commits** (optional, recommended for security)
- ☑ **Require linear history** (optional, keeps git history clean)
- ☑ **Do not allow bypassing the above settings**
  - ☑ Include administrators (recommended - even admins must follow the rules)

#### Rules applied to everyone
- ☑ **Allow force pushes**: **Disabled** (default)
- ☑ **Allow deletions**: **Disabled** (default)

### Save the Rule

Click **Create** (or **Save changes**) at the bottom of the page.

## Step 2: Install and Configure CodeRabbit

CodeRabbit is an AI-powered code review assistant that automatically reviews pull requests.

### Install CodeRabbit GitHub App

1. Go to: https://github.com/apps/coderabbitai
2. Click **Install** (or **Configure** if already installed)
3. Select **Only select repositories**
4. Choose: `benbuzz790/bots`
5. Click **Install** (or **Save**)
6. Grant the requested permissions

### Verify CodeRabbit Configuration

CodeRabbit will automatically use the `.coderabbit.yaml` configuration file in your repository root. This file should already be created with appropriate settings for the project.

**Key configuration points:**
- Review profile: "chill" (balanced, not overly strict)
- Focuses on: code quality, bugs, security, performance, test coverage
- Follows project principles: YAGNI, KISS, defensive programming
- Auto-reviews PRs to main branch

### Test CodeRabbit

After installation, CodeRabbit will automatically review new pull requests. You can test it by:
1. Creating a test branch
2. Making a small change
3. Opening a pull request
4. CodeRabbit should comment within 1-2 minutes

## Step 3: Configure Required Status Checks

**Important:** Status checks must run at least once before they can be added as required checks.

### After Your First PR Runs

1. Go back to **Settings → Branches → Edit** your branch protection rule
2. Scroll to **Require status checks to pass before merging**
3. In the search box, you should now see available checks. Add these as required:
   - `Test on Python 3.12` (or the exact name from your test job)
   - `Code Quality & Style Check`
   - `Security Scan`
   - `coderabbit` (if it appears as a status check)

4. Click **Save changes**

### Verify Status Checks

Create a test PR and verify that:
- All required checks appear in the PR
- PR cannot be merged until all checks pass
- Checks automatically run when you push new commits

## Step 4: Create Pull Request Template

The PR template (`.github/pull_request_template.md`) should already be in place. This template:
- Guides contributors through the PR process
- Ensures all necessary information is provided
- Includes checklists for code quality and testing
- Aligns with project principles (YAGNI, KISS, defensive programming)

## Developer Workflow After Setup

### Creating a Pull Request

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make your changes** (keep them small and focused)

3. **Commit and push:**
   ```bash
   git add .
   git commit -m "Add feature X"
   git push origin feature/my-feature
   ```

4. **Create Pull Request on GitHub:**
   - Fill out the PR template
   - Wait for CI/CD checks to run
   - Address any failures

5. **CodeRabbit Review:**
   - CodeRabbit will automatically review your PR
   - Address any suggestions or concerns
   - Reply to CodeRabbit comments if you disagree

6. **Request Human Review:**
   - Once checks pass and CodeRabbit feedback is addressed
   - Request review from a maintainer

7. **Merge:**
   - Once approved and all checks green → Merge!

### What Blocks a Merge

Your PR **cannot be merged** if:
- ❌ Any required CI/CD checks fail
- ❌ Code coverage is below threshold (80%)
- ❌ Linting errors exist
- ❌ No approval from a reviewer
- ❌ Unresolved conversations remain
- ❌ Branch is not up to date with main

### What Allows a Merge

Your PR **can be merged** when:
- ✅ All tests passing (green checkmark)
- ✅ Code coverage meets threshold
- ✅ All linting checks pass
- ✅ Security scan passes
- ✅ At least one approval received
- ✅ All conversations resolved
- ✅ Branch is up to date with main

## Troubleshooting

### Problem: Status checks not appearing as options

**Solution:** Status checks must run at least once before they can be required. Create a test PR, let the checks run, then add them as required checks.

### Problem: Cannot push to main branch

**Solution:** This is expected! Branch protection is working. Create a feature branch and open a PR instead:
```bash
git checkout -b feature/my-fix
git push origin feature/my-fix
# Then create PR on GitHub
```

### Problem: PR checks failing

**Solution:** Click on the failing check to see details. Common issues:
- **Tests failing:** Fix the test failures locally, commit, and push
- **Linting errors:** Run `black .` and `isort .` locally, commit, and push
- **Coverage too low:** Add tests to increase coverage
- **Security issues:** Review bandit report and fix vulnerabilities

### Problem: CodeRabbit not reviewing PR

**Solution:** 
- Verify CodeRabbit is installed on the repository
- Check that PR is not a draft (CodeRabbit skips drafts by default)
- Wait a few minutes - reviews can take 1-2 minutes
- Check `.coderabbit.yaml` configuration

### Problem: Need to bypass branch protection (emergency)

**Solution:** 
- If you're an admin and "Include administrators" is unchecked, you can bypass
- Otherwise, you'll need to temporarily disable the rule (Settings → Branches → Edit rule)
- **Important:** Re-enable protection immediately after emergency fix

### Problem: Merge conflicts

**Solution:**
```bash
# Update your branch with latest main
git checkout main
git pull origin main
git checkout feature/my-feature
git merge main
# Resolve conflicts
git add .
git commit -m "Resolve merge conflicts"
git push origin feature/my-feature
```

## What to Do If Checks Fail

### Test Failures

1. **View the failure:**
   - Click on the failing check in the PR
   - Click "Details" to see the full log
   - Identify which test(s) failed

2. **Reproduce locally:**
   ```bash
   pytest tests/ -v
   ```

3. **Fix and push:**
   ```bash
   # Fix the issue
   git add .
   git commit -m "Fix test failure"
   git push origin feature/my-feature
   ```

### Linting Failures

1. **Run linters locally:**
   ```bash
   black --check .
   isort --check-only .
   flake8 .
   ```

2. **Auto-fix formatting:**
   ```bash
   black .
   isort .
   ```

3. **Commit and push:**
   ```bash
   git add .
   git commit -m "Fix linting issues"
   git push origin feature/my-feature
   ```

### Coverage Failures

1. **Check current coverage:**
   ```bash
   pytest tests/ --cov=bots --cov-report=term-missing
   ```

2. **Add tests for uncovered code:**
   - Look at the coverage report to see what's not covered
   - Write tests for those areas

3. **Verify and push:**
   ```bash
   pytest tests/ --cov=bots --cov-report=term-missing
   git add .
   git commit -m "Add tests to improve coverage"
   git push origin feature/my-feature
   ```

### Security Scan Failures

1. **Review the security report:**
   - Click on the security check details
   - Review bandit findings

2. **Address issues:**
   - Fix genuine security vulnerabilities
   - Add `# nosec` comments for false positives (with justification)

3. **Push fix:**
   ```bash
   git add .
   git commit -m "Address security concerns"
   git push origin feature/my-feature
   ```

## Additional Resources

- **GitHub Branch Protection Documentation:** https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches
- **CodeRabbit Documentation:** https://docs.coderabbit.ai/
- **Project Contributing Guide:** [CONTRIBUTING.md](../CONTRIBUTING.md)
- **Project Roadmap:** [ROADMAP.md](../ROADMAP.md)

## Summary

Branch protection is now active! All changes to `main` must:
1. Go through a pull request
2. Pass all automated checks (tests, linting, security)
3. Receive CodeRabbit AI review
4. Get at least one human approval
5. Have all conversations resolved

This ensures high code quality and prevents regressions while maintaining a smooth development workflow.
