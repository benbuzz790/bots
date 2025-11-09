.PHONY: help install install-dev format check lint test test-fast clean
help:
	@echo "Bots Development Commands"
	@echo "========================="
	@echo "make install      - Install production dependencies"
	@echo "make install-dev  - Install development dependencies"
	@echo "make format       - Format code with black and isort"
	@echo "make check        - Check formatting (what CI runs)"
	@echo "make lint         - Run all linters (black, isort, flake8, markdownlint)"
	@echo "make test         - Run all tests with coverage"
	@echo "make test-fast    - Run tests in parallel (faster)"
	@echo "make clean        - Remove temporary files and caches"
install:
	pip install -r requirements.txt
	pip install -e .
install-dev:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pip install -e .[dev]
format:
	black .
	isort .
	python -m bots.dev.remove_boms
	markdownlint --fix **/*.md --ignore node_modules --ignore __pycache__ --ignore .mypy_cache --ignore .pytest_cache
check:
	black --check --diff .
	isort --check-only --diff .
	flake8 . --count --statistics --show-source
	markdownlint **/*.md --ignore node_modules --ignore __pycache__ --ignore .mypy_cache --ignore .pytest_cache
lint: check
test:
	pytest tests/ -v --cov=bots --cov-report=term-missing --cov-report=xml
test-fast:
	pytest tests/ -n auto -v --maxfail=10
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	rm -rf coverage.xml test_results.xml 2>/dev/null || true
