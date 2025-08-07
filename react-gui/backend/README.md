# Bot GUI Backend

FastAPI backend for the React GUI interface to the bots framework.

## Features

- **WebSocket Support**: Real-time communication with React frontend
- **REST API**: Bot management and state retrieval
- **Defensive Programming**: Comprehensive input/output validation
- **Bot Management**: Create, manage, and interact with bot instances
- **Conversation Trees**: Full conversation history and navigation
- **Tool Integration**: Support for all bots framework tools

## Architecture

```
FastAPI Backend
├── main.py              # FastAPI app and REST endpoints
├── models.py            # Pydantic models with validation
├── bot_manager.py       # Bot instance management
├── websocket_handler.py # WebSocket event handling
└── test_backend.py      # Comprehensive tests
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure the bots framework is available:
```bash
# From the main bots directory
pip install -e .
```

## Running the Server

### Development
```bash
# From the backend directory
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### Production
```bash
python main.py
```

The server will be available at:
- API: http://127.0.0.1:8000
- Docs: http://127.0.0.1:8000/docs
- WebSocket: ws://127.0.0.1:8000/ws/{connection_id}

## API Endpoints

### REST Endpoints
- `GET /api/health` - Health check
- `POST /api/bots/create` - Create a new bot
- `GET /api/bots/{bot_id}` - Get bot state
- `DELETE /api/bots/{bot_id}` - Delete a bot
- `GET /api/bots` - List all bots

### WebSocket Events

#### Client → Server
- `send_message` - Send a chat message to a bot
- `get_bot_state` - Request current bot state

#### Server → Client
- `bot_response` - Bot's response to a message
- `tool_update` - Tool execution progress
- `error` - Error notifications

## Testing

Run the comprehensive test suite:
```bash
python test_backend.py
```

Or use pytest directly:
```bash
pytest test_backend.py -v
```

## Defensive Programming

All functions include:
- Input type and value validation
- Output validation
- Comprehensive error handling
- Detailed logging

This ensures robust operation and clear error messages for debugging.
