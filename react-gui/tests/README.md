# React GUI Foundation Test Suite

## Overview

This comprehensive test suite validates the React GUI foundation for the bots framework, ensuring robust end-to-end functionality with defensive programming principles.

## Test Structure

```
tests/
├── backend/                    # Backend Python tests
│   ├── test_models.py         # Pydantic model validation
│   ├── test_websocket_handler.py  # WebSocket event handling
│   └── test_bot_manager.py    # Bot instance management
├── frontend/                   # Frontend React tests
│   └── test_components.test.tsx   # React component testing
├── integration/                # End-to-end integration tests
│   └── test_end_to_end.py     # Complete chat flow testing
├── conftest.py                # Shared fixtures and utilities
├── run_tests.py               # Comprehensive test runner
├── requirements.txt           # Test dependencies
└── README.md                  # This file
```

## Test Categories

### 1. Backend Tests (`backend/`)

**Models Testing (`test_models.py`)**
- Pydantic model validation (Message, ToolCall, ConversationNode, BotState)
- Enum validation (MessageRole, ToolCallStatus)
- Defensive programming assertions
- JSON serialization/deserialization
- Field type and value validation

**WebSocket Handler Testing (`test_websocket_handler.py`)**
- WebSocket connection lifecycle
- Event routing and handling
- Message validation and sanitization
- Error handling and propagation
- Security input validation
- Connection resilience

**Bot Manager Testing (`test_bot_manager.py`)**
- Bot instance creation and management
- Conversation tree handling
- Integration with bots framework
- Concurrent operations
- Memory management
- Security validation

### 2. Frontend Tests (`frontend/`)

**Component Testing (`test_components.test.tsx`)**
- React component rendering
- Props validation with runtime checks
- User interaction handling
- State management
- Error boundaries
- Accessibility compliance
- Keyboard navigation

### 3. Integration Tests (`integration/`)

**End-to-End Testing (`test_end_to_end.py`)**
- Complete chat flow (React → FastAPI → Bots Framework)
- WebSocket communication
- REST API endpoints
- Tool execution flow
- Error handling across stack
- Performance under load
- Data flow validation

## Defensive Programming Features

All tests implement comprehensive defensive programming:

### Input Validation
```python
def test_function(input_data):
    assert isinstance(input_data, expected_type), f"Expected {expected_type}, got {type(input_data)}"
    assert input_data is not None, "Input cannot be None"
    assert len(input_data) > 0, "Input cannot be empty"
```

### Output Validation
```python
result = function_under_test(input_data)
assert isinstance(result, expected_type), f"Expected {expected_type}, got {type(result)}"
assert hasattr(result, 'required_field'), "Result missing required field"
```

### Error Handling
```python
with pytest.raises(ExpectedError):
    function_that_should_fail(invalid_input)
```

## Running Tests

### Prerequisites

1. Install test dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure bots framework is installed:
```bash
pip install -e ../..  # Install bots framework
```

### Run All Tests
```bash
python run_tests.py
```

### Run Specific Test Categories
```bash
# Python tests only
python run_tests.py --python-only

# TypeScript tests only
python run_tests.py --typescript-only

# Integration tests only
python run_tests.py --integration-only

# Defensive programming tests only
python run_tests.py --defensive-only
```

### Run Individual Test Files
```bash
# Backend tests
pytest backend/test_models.py -v
pytest backend/test_websocket_handler.py -v
pytest backend/test_bot_manager.py -v

# Integration tests
pytest integration/test_end_to_end.py -v

# With coverage
pytest backend/ --cov=backend --cov-report=html
```

## Test Configuration

### Pytest Configuration
Tests use the following pytest configuration:
- Async support with `pytest-asyncio`
- Coverage reporting with `pytest-cov`
- JSON reporting with `pytest-json-report`
- Parallel execution with `pytest-xdist`

### Custom Markers
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.defensive` - Defensive programming tests
- `@pytest.mark.performance` - Performance tests

### Fixtures
Comprehensive fixtures provided in `conftest.py`:
- `mock_bot_instance` - Mock bot for testing
- `mock_websocket` - Mock WebSocket connection
- `sample_message` - Sample message data
- `sample_conversation_node` - Sample conversation node
- `sample_bot_state` - Sample bot state
- `data_validator` - Defensive validation utilities

## Success Criteria

The foundation is verified when:

- ✅ All backend models validate correctly with defensive assertions
- ✅ WebSocket communication handles all event types and errors
- ✅ Bot management works with concurrent operations
- ✅ React components render and handle user interactions
- ✅ End-to-end chat flow works from frontend to backend
- ✅ Error handling is comprehensive across the stack
- ✅ Performance meets benchmarks under load
- ✅ Security validation prevents malicious input
- ✅ Coverage meets minimum requirements (90%+)
- ✅ All defensive programming assertions are tested

## Coverage Requirements

- **Minimum Coverage**: 90% for all backend code
- **Critical Paths**: 100% coverage for defensive assertions
- **Integration**: 80% coverage for end-to-end flows

## Performance Benchmarks

Integration tests include performance validation:
- Message throughput: >100 messages/second
- WebSocket latency: <100ms response time
- Memory usage: Stable under load
- Connection resilience: Automatic reconnection

## Security Testing

Tests include security validation:
- Input sanitization (XSS, SQL injection attempts)
- WebSocket message validation
- Bot ID format validation
- Content length limits
- Error message sanitization
