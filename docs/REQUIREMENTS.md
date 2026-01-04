# Requirements Files Organization

This document explains the organization of the requirements files in this project.

## Files

### requirements.txt

Contains all **core dependencies** required for the bots framework to function. These are the minimum packages needed to use the framework in production.

**Categories:**

- **LLM Provider SDKs**: anthropic, openai, google-genai
- **Type hints**: typing_extensions
- **Code manipulation**: libcst
- **Serialization**: dill
- **System utilities**: psutil
- **Audio generation**: numpy (for piano tool)
- **Observability**: opentelemetry-api, opentelemetry-sdk

**Installation:**

```bash
pip install -r requirements.txt
```

### requirements-dev.txt

Contains all **development dependencies** needed for contributing to the project, running tests, formatting code, and building documentation.

**Categories:**

- **Testing**: pytest and plugins (pytest-asyncio, pytest-cov, pytest-timeout, etc.)
- **Code formatting**: black, isort
- **Linting**: flake8, mypy
- **Security**: bandit
- **Documentation**: sphinx, sphinx-rtd-theme
- **Pre-commit hooks**: pre-commit
- **Optional observability exporters**: opentelemetry exporters for OTLP and Jaeger

**Installation:**

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

### setup.py

Defines the package installation configuration. It includes:

- Core dependencies (mirrors requirements.txt)
- Optional extras:
  - [dev]: All development dependencies
  - [observability]: Production observability exporters

**Installation:**

```bash
# Basic installation
pip install .
# Development installation (editable mode with dev dependencies)
pip install -e .[dev]
# With observability exporters
pip install .[observability]
```

## Testing Requirements Completeness

To verify that all requirements files are comprehensive and complete, run:

```bash
pytest tests/test_install_in_fresh_environment.py -v
```

This test suite:

1. Creates fresh virtual environments
2. Installs dependencies from requirements files
3. Verifies all packages are present
4. Tests that the package can be imported
5. Ensures pytest and development tools work correctly

## Maintenance

When adding new dependencies:

1. Add to requirements.txt if it's a core dependency
2. Add to requirements-dev.txt if it's only needed for development
3. Update setup.py to match
4. Run the installation test to verify completeness
5. Use version constraints (>=) to allow flexibility while ensuring minimum versions

## Version Constraints

We use minimum version constraints (>=) rather than pinned versions to:

- Allow users to get security updates
- Avoid dependency conflicts with other packages
- Maintain compatibility with newer versions

For reproducible builds in CI/CD, consider using pip freeze to generate a lock file.
