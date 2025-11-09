# Development commands for bots project (Windows PowerShell version)
# This is the PowerShell equivalent of the Makefile
param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)
function Show-Help {
    Write-Host "Bots Development Commands" -ForegroundColor Cyan
    Write-Host "=========================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host ".\make.ps1 install      - Install production dependencies"
    Write-Host ".\make.ps1 install-dev  - Install development dependencies"
    Write-Host ".\make.ps1 format       - Format code with black and isort"
    Write-Host ".\make.ps1 check        - Check formatting (what CI runs)"
    Write-Host ".\make.ps1 lint         - Run all linters (black, isort, flake8)"
    Write-Host ".\make.ps1 test         - Run all tests with coverage"
    Write-Host ".\make.ps1 test-fast    - Run tests in parallel (faster)"
    Write-Host ".\make.ps1 clean        - Remove temporary files and caches"
}
function Install {
    pip install -r requirements.txt
    pip install -e .
}
function Install-Dev {
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    pip install -e .[dev]
}
function Format-Code {
    black .
    isort .
    python -m bots.dev.remove_boms
    markdownlint --fix "**/*.md" --ignore node_modules
}
function Check-Format {
    black --check --diff .
    isort --check-only --diff .
    flake8 . --count --statistics --show-source
    markdownlint "**/*.md" --ignore node_modules
}
function Run-Tests {
    pytest tests/ -v --cov=bots --cov-report=term-missing --cov-report=xml
}
function Run-Tests-Fast {
    pytest tests/ -n auto -v --maxfail=10
}
function Clean {
    Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path . -Recurse -Directory -Filter "*.egg-info" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path . -Recurse -Directory -Filter ".pytest_cache" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path . -Recurse -Directory -Filter ".mypy_cache" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path . -Recurse -File -Filter "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue
    Remove-Item -Path ".coverage" -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "coverage.xml" -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "test_results.xml" -Force -ErrorAction SilentlyContinue
    Write-Host "Cleaned temporary files" -ForegroundColor Green
}
switch ($Command.ToLower()) {
    "help" { Show-Help }
    "install" { Install }
    "install-dev" { Install-Dev }
    "format" { Format-Code }
    "check" { Check-Format }
    "lint" { Check-Format }
    "test" { Run-Tests }
    "test-fast" { Run-Tests-Fast }
    "clean" { Clean }
    default {
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Write-Host ""
        Show-Help
        exit 1
    }
}
