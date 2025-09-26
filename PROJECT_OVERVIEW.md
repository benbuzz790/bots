# Project Overview

## Architecture

This project is a comprehensive bot framework with multiple components:

### Core Components

1. **Bot Framework** (`bots/`)
   - Foundation bots for basic functionality
   - Development bots for testing and debugging
   - Flow-based conversation management
   - Utility bots for common tasks

2. **Bot Library** (`botlib/`)
   - Core library functions
   - Bot building utilities
   - Debug and development tools

3. **Examples** (`examples/`)
   - Sample implementations
   - Best practice demonstrations
   - Tutorial code

4. **Testing Infrastructure** (`tests/`)
   - Comprehensive test suite
   - CLI testing
   - Functional prompt testing
   - PowerShell tool testing

## Key Features

- Multi-platform support (Windows, Linux, macOS)
- Docker containerization
- Comprehensive testing framework
- CLI and GUI interfaces
- Extensible bot architecture
- Work order management system

## Development Workflow

1. Use work orders in `_work_orders/` for tracking features
2. Follow the testing patterns in `tests/`
3. Reference examples in `examples/` for implementation guidance
4. Use the bot library for common functionality

## Getting Started

1. Install dependencies: `pip install -r requirements.txt`
2. Run development server: `python run_development.py`
3. Check examples in `examples/` directory
4. Review work orders for current development priorities
