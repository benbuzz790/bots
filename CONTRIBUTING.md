# Contributing to bots
We welcome contributions to the bots project! Here are some guidelines to help you get started.
## Development Setup
### 1. Install Dependencies
```bash
# Install production dependencies
pip install -r requirements.txt
# Install development dependencies (formatters, linters, test tools)
pip install -r requirements-dev.txt
# Install the package in editable mode
pip install -e .[dev]
```
Or use the Makefile:
```bash
make install-dev
```
### 2. Set Up Pre-commit Hooks (Recommended)
Pre-commit hooks automatically format and check your code before each commit:
```bash
# Install pre-commit hooks
pre-commit install
# Test the hooks (optional)
pre-commit run --all-files
```
This ensures your code matches CI requirements before you push.
## Development Commands
We provide a `Makefile` with common development tasks:
```bash
make help         # Show all available commands
make format       # Format code (black, isort, remove BOMs)
make check        # Check formatting (what CI runs)
make lint         # Run all linters
make test         # Run tests with coverage
make test-fast    # Run tests in parallel
make clean        # Remove temporary files
```
**Before pushing, always run:**
```bash
make format
make check
make test
```
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
3. **Format and test locally:**
   ```bash
   make format
   make check
   make test
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
   - Code coverage must meet threshold (50%)
   - Linting must pass (black, isort, flake8)
   - Security scan must pass
   - CodeRabbit AI will review your code
7. **Address feedback:**
   - Fix any failing checks
   - Respond to CodeRabbit suggestions
   - Make requested changes from human reviewers
8. **Merge:** Once approved and all checks pass, a maintainer will merge your PR
