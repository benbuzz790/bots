# Contributing to bots

We welcome contributions to the bots project! Here are some guidelines to help you get started.

## Reporting Issues

If you find a bug or have a suggestion for improving the project, please open an issue on the GitHub repository.

## Pull Request Workflow

All changes to the `main` branch must go through a pull request (PR) process with automated checks and code review. This ensures code quality and prevents regressions.

### Quick Start

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make your changes** (keep them small and focused - follow YAGNI and KISS principles)

3. **Test locally:**
   ```bash
   pytest tests/ -v
   black .
   isort .
   flake8 .
   ```

4. **Commit and push:**
   ```bash
   git add .
   git commit -m "Add feature X"
   git push origin feature/my-feature
   ```

5. **Create Pull Request on GitHub** - Fill out the PR template

6. **Wait for automated checks:**
   - Tests must pass
   - Code coverage must meet threshold (80%)
   - Linting must pass (black, isort, flake8)
   - Security scan must pass
   - CodeRabbit AI will review your code

7. **Address feedback:**
   - Fix any failing checks
   - Respond to CodeRabbit suggestions
   - Make requested changes from human reviewers

8. **Get approval and merge:**
   - At least one approval required
   - All checks must be green ✅
   - All conversations must be resolved

### Required Checks

Your PR must pass these automated checks before it can be merged:

- **Tests**: All unit and integration tests must pass
- **Code Coverage**: Must maintain at least 80% coverage
- **Linting**: Code must pass black, isort, and flake8 checks
- **Type Checking**: MyPy type checking (currently advisory)
- **Security Scan**: Bandit security analysis must pass
- **CodeRabbit Review**: AI-powered code review provides feedback

### What to Expect

**Automated Reviews:**
- CodeRabbit will automatically review your PR within 1-2 minutes
- It will check for code quality, potential bugs, security issues, and adherence to project principles
- Address its suggestions or explain why you disagree

**Human Review:**
- A maintainer will review your PR for architecture and design
- They may request changes or ask questions
- Be responsive and collaborative

**Merge Criteria:**
- ✅ All automated checks passing
- ✅ At least one approval from a maintainer
- ✅ All conversations resolved
- ✅ Branch up to date with main

### Branch Protection

The `main` branch is protected with the following rules:
- No direct pushes allowed
- Pull requests required for all changes
- Status checks must pass before merging
- At least one approval required
- Conversations must be resolved before merging
- Branch must be up to date with main

For detailed setup instructions, see [Branch Protection Setup Guide](docs/BRANCH_PROTECTION_SETUP.md).

## Submitting Pull Requests

1. Fork the repository and create your branch from main.
2. If you've added code that should be tested, add tests.
3. Ensure the test suite passes.
4. Make sure your code lints.
5. Fill out the pull request template completely.
6. Wait for automated checks and code review.
7. Address any feedback promptly.
8. Once approved and all checks pass, your PR will be merged!

## Coding Style

- Use 4 spaces for indentation
- Follow PEP 8 style guide
- Use type hints for function arguments and return values
- Write docstrings for all functions, classes, and modules
- Line length: 127 characters (configured in pyproject.toml)
- Use black for formatting: `black .`
- Use isort for import sorting: `isort .`

### Project Principles

When contributing, please follow these principles:

- **YAGNI** (You Aren't Gonna Need It): Don't add functionality until it's needed
- **KISS** (Keep It Simple, Stupid): Prefer simple solutions over complex ones
- **Defensive Programming**: Handle errors gracefully, validate inputs, return helpful error messages
- **Small, Incremental Changes**: Break large changes into smaller, reviewable PRs
- **Test Coverage**: Add tests for new functionality and bug fixes

## Running Tests Locally

Our test suite is organized into unit, integration, and e2e tests. See [TESTING.md](TESTING.md) for detailed information about test organization and best practices.

### Quick Test Commands

```bash
# Run all tests
pytest tests/ -v

# Run only fast unit tests (recommended for local development)
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v

# Run e2e tests
pytest tests/e2e/ -v

# Run with coverage
pytest --cov=bots --cov-report=term-missing

# Run specific test file
pytest tests/test_specific.py -v

# Run linting
black --check .
isort --check-only .
flake8 .
mypy bots/ --ignore-missing-imports
```

For more information on test categories, fixtures, and best practices, see [TESTING.md](TESTING.md).

## Troubleshooting

### My PR checks are failing

See the [Branch Protection Setup Guide](docs/BRANCH_PROTECTION_SETUP.md#what-to-do-if-checks-fail) for detailed troubleshooting steps.

### I can't push to main

This is expected! Create a feature branch instead:
```bash
git checkout -b feature/my-fix
git push origin feature/my-fix
```
Then create a pull request on GitHub.

### I need to update my branch

```bash
git checkout main
git pull origin main
git checkout feature/my-feature
git merge main
git push origin feature/my-feature
```

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License.
