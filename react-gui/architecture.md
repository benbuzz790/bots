# React GUI Foundation Architecture - Detailed Interface Specifications

## Overview

This document defines the interface contracts, data structures, and component architecture for the React GUI foundation that enables basic chat functionality with the bots framework.

## Architecture Layers

```
┌─────────────────────────────────────────┐
│           React Frontend                │
│  ┌─────────────────┐ ┌─────────────────┐│
│  │   Chat UI       │ │  State Manager  ││
│  │  Components     │ │   (Zustand)     ││
│  └─────────────────┘ └─────────────────┘│
└─────────────────────────────────────────┘
                    │
              WebSocket + REST
                    │
┌─────────────────────────────────────────┐
│           FastAPI Backend               │
│  ┌─────────────────┐ ┌─────────────────┐│
│  │  WebSocket      │ │   Bot Manager   ││
│  │   Handler       │ │                 ││
│  └─────────────────┘ └─────────────────┘│
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│           Bots Framework                │
│           (Existing Code)               │
└─────────────────────────────────────────┘
```

## Data Structures

### Core Types

```typescript
// Frontend Types
interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  toolCalls?: ToolCall[];
}

interface ToolCall {
  id: string;
  name: string;
  status: 'running' | 'completed' | 'error';
  result?: string;
  error?: string;
}

interface ConversationNode {
  id: string;
  message: Message;
  parent?: string;
  children: string[];
  isCurrent: boolean;
}

interface BotState {
  id: string;
  name: string;
  conversationTree: Record<string, ConversationNode>;
  currentNodeId: string;
  isConnected: boolean;
  isThinking: boolean;
}
```

```python
# Backend Types
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ToolCallStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"

class ToolCall(BaseModel):
    id: str
    name: str
    status: ToolCallStatus
    result: Optional[str] = None
    error: Optional[str] = None

class Message(BaseModel):
    id: str
    role: MessageRole
    content: str
    timestamp: str
    tool_calls: List[ToolCall] = []

class ConversationNode(BaseModel):
    id: str
    message: Message
    parent: Optional[str] = None
    children: List[str] = []
    is_current: bool = False

class BotState(BaseModel):
    id: str
    name: str
    conversation_tree: Dict[str, ConversationNode]
    current_node_id: str
    is_connected: bool
    is_thinking: bool
```

## API Contracts

### WebSocket Events

#### Client → Server

```typescript
// Send a chat message
interface SendMessageEvent {
  type: 'send_message';
  data: {
    botId: string;
    content: string;
  };
}

// Request bot state
interface GetBotStateEvent {
  type: 'get_bot_state';
  data: {
    botId: string;
  };
}
```

#### Server → Client

```typescript
// Bot response received
interface BotResponseEvent {
  type: 'bot_response';
  data: {
    botId: string;
    message: Message;
    conversationTree: Record<string, ConversationNode>;
    currentNodeId: string;
  };
}

// Tool execution update
interface ToolUpdateEvent {
  type: 'tool_update';
  data: {
    botId: string;
    toolCall: ToolCall;
  };
}

// Error occurred
interface ErrorEvent {
  type: 'error';
  data: {
    message: string;
    code?: string;
  };
}
```

### REST Endpoints

```python
# Bot management
POST /api/bots/create
GET /api/bots/{bot_id}
DELETE /api/bots/{bot_id}

# Health check
GET /api/health
```

## Component Architecture

### Frontend Components

```typescript
// Main application component
interface AppProps {}
const App: React.FC<AppProps> = () => { ... }

// Chat interface
interface ChatInterfaceProps {
  botId: string;
}
const ChatInterface: React.FC<ChatInterfaceProps> = ({ botId }) => { ... }

// Message display
interface MessageListProps {
  messages: Message[];
  isThinking: boolean;
}
const MessageList: React.FC<MessageListProps> = ({ messages, isThinking }) => { ... }

// Message input
interface MessageInputProps {
  onSendMessage: (content: string) => void;
  disabled: boolean;
}
const MessageInput: React.FC<MessageInputProps> = ({ onSendMessage, disabled }) => { ... }
```

### State Management

```typescript
// Zustand store
interface BotStore {
  // State
  bots: Record<string, BotState>;
  currentBotId: string | null;
  connected: boolean;
  
  // Actions
  sendMessage: (botId: string, content: string) => void;
  setBotState: (botState: BotState) => void;
  setConnected: (connected: boolean) => void;
  
  // WebSocket management
  connect: () => void;
  disconnect: () => void;
}
```

## File Structure

```
react-gui/
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── models.py              # Pydantic models
│   ├── websocket_handler.py   # WebSocket event handling
│   ├── bot_manager.py         # Bot instance management
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── App.tsx
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── MessageList.tsx
│   │   │   └── MessageInput.tsx
│   │   ├── store/
│   │   │   └── botStore.ts
│   │   ├── types/
│   │   │   └── index.ts
│   │   ├── utils/
│   │   │   └── websocket.ts
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

## Defensive Programming Requirements

All functions must include:

1. **Input Validation**: Type checking and property validation
2. **Output Validation**: Ensure return values match expected types
3. **Error Handling**: Graceful error handling with meaningful messages
4. **Logging**: Comprehensive logging for debugging

### Example Defensive Function

```python
def create_message(
    content: str, 
    role: MessageRole, 
    tool_calls: Optional[List[ToolCall]] = None
) -> Message:
    """Create a new message with defensive validation."""
    
    # Input validation
    assert isinstance(content, str), f"content must be str, got {type(content)}"
    assert isinstance(role, MessageRole), f"role must be MessageRole, got {type(role)}"
    assert content.strip(), "content cannot be empty"
    
    if tool_calls is not None:
        assert isinstance(tool_calls, list), f"tool_calls must be list, got {type(tool_calls)}"
        for call in tool_calls:
            assert isinstance(call, ToolCall), f"tool_call must be ToolCall, got {type(call)}"
    
    # Create message
    message = Message(
        id=str(uuid.uuid4()),
        role=role,
        content=content.strip(),
        timestamp=datetime.utcnow().isoformat(),
        tool_calls=tool_calls or []
    )
    
    # Output validation
    assert isinstance(message, Message), f"Expected Message, got {type(message)}"
    assert message.id, "Message ID must not be empty"
    assert message.content, "Message content must not be empty"
    
    return message
```

## Success Criteria

The foundation is complete when:

1. ✅ React frontend can connect to FastAPI backend via WebSocket
2. ✅ User can send a message and receive a bot response
3. ✅ All data structures are properly typed and validated
4. ✅ Error handling works gracefully
5. ✅ Basic tests pass for core functionality
6. ✅ Code follows defensive programming principles

## Detailed Implementation Specifications

### Backend Service Layer

#### BotManager Class

```python
class BotManager:
    """Manages bot instances with defensive validation."""
    
    def __init__(self):
        self._bots: Dict[str, Any] = {}
        self._conversation_trees: Dict[str, Dict[str, ConversationNode]] = {}
    
    async def create_bot(self, name: str) -> str:
        """Create new bot instance."""
        assert isinstance(name, str), f"name must be str, got {type(name)}"
        assert name.strip(), "name cannot be empty"
        
        from bots.foundation.anthropic_bots import AnthropicBot
        import bots.tools.code_tools as code_tools
        
        bot = AnthropicBot()
        bot.add_tools(code_tools)
        
        bot_id = str(uuid.uuid4())
        self._bots[bot_id] = bot
        self._conversation_trees[bot_id] = {}
        
        assert bot_id in self._bots, "Bot creation failed"
        return bot_id
    
    async def send_message(self, bot_id: str, content: str) -> BotState:
        """Send message to bot and return updated state."""
        assert isinstance(bot_id, str), f"bot_id must be str, got {type(bot_id)}"
        assert isinstance(content, str), f"content must be str, got {type(content)}"
        assert bot_id in self._bots, f"Bot {bot_id} not found"
        assert content.strip(), "content cannot be empty"
        
        bot = self._bots[bot_id]
        
        # Send message to bot
        response = bot.respond(content)
        
        # Convert bot conversation to our format
        conversation_tree = self._convert_bot_conversation(bot)
        self._conversation_trees[bot_id] = conversation_tree
        
        # Find current node
        current_node_id = self._find_current_node(bot)
        
        bot_state = BotState(
            id=bot_id,
            name=f"Bot {bot_id[:8]}",
            conversation_tree=conversation_tree,
            current_node_id=current_node_id,
            is_connected=True,
            is_thinking=False
        )
        
        assert isinstance(bot_state, BotState), f"Expected BotState, got {type(bot_state)}"
        return bot_state
```

#### WebSocketHandler Class

```python
class WebSocketHandler:
    """Handles WebSocket connections and message routing."""
    
    def __init__(self, bot_manager: BotManager):
        assert isinstance(bot_manager, BotManager), f"Expected BotManager, got {type(bot_manager)}"
        self.bot_manager = bot_manager
        self.connections: Dict[str, WebSocket] = {}
    
    async def handle_connection(self, websocket: WebSocket):
        """Handle new WebSocket connection."""
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        self.connections[connection_id] = websocket
        
        try:
            while True:
                data = await websocket.receive_json()
                await self.handle_message(websocket, data)
        except WebSocketDisconnect:
            del self.connections[connection_id]
    
    async def handle_message(self, websocket: WebSocket, data: dict):
        """Process incoming WebSocket message."""
        assert isinstance(data, dict), f"data must be dict, got {type(data)}"
        assert 'type' in data, "data must have 'type' field"
        assert 'data' in data, "data must have 'data' field"
        
        message_type = data['type']
        message_data = data['data']
        
        try:
            if message_type == 'send_message':
                await self._handle_send_message(websocket, message_data)
            elif message_type == 'get_bot_state':
                await self._handle_get_bot_state(websocket, message_data)
            else:
                await self._send_error(websocket, f"Unknown message type: {message_type}")
        except Exception as e:
            await self._send_error(websocket, str(e))
    
    async def _handle_send_message(self, websocket: WebSocket, data: dict):
        """Handle send_message event."""
        assert 'botId' in data, "data must have 'botId' field"
        assert 'content' in data, "data must have 'content' field"
        
        bot_id = data['botId']
        content = data['content']
        
        # Send thinking indicator
        await websocket.send_json({
            'type': 'bot_thinking',
            'data': {'botId': bot_id, 'thinking': True}
        })
        
        # Get bot response
        bot_state = await self.bot_manager.send_message(bot_id, content)
        
        # Send response
        await websocket.send_json({
            'type': 'bot_response',
            'data': {
                'botId': bot_id,
                'botState': bot_state.dict()
            }
        })
```

### Frontend Service Layer

#### WebSocket Service

```typescript
export class WebSocketService {
    private ws: WebSocket | null = null;
    private eventHandlers: Map<string, (data: any) => void> = new Map();
    
    constructor(private url: string) {
        if (typeof url !== 'string' || !url) {
            throw new Error('WebSocket URL must be a non-empty string');
        }
    }
    
    connect(): Promise<void> {
        return new Promise((resolve, reject) => {
            try {
                this.ws = new WebSocket(this.url);
                
                this.ws.onopen = () => {
                    console.log('WebSocket connected');
                    resolve();
                };
                
                this.ws.onmessage = (event) => {
                    try {
                        const message = JSON.parse(event.data);
                        this.handleMessage(message);
                    } catch (error) {
                        console.error('Failed to parse WebSocket message:', error);
                    }
                };
                
                this.ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                    reject(error);
                };
                
                this.ws.onclose = () => {
                    console.log('WebSocket disconnected');
                    this.ws = null;
                };
            } catch (error) {
                reject(error);
            }
        });
    }
    
    sendMessage(type: string, data: any): void {
        if (typeof type !== 'string' || !type) {
            throw new Error('Message type must be a non-empty string');
        }
        if (!data || typeof data !== 'object') {
            throw new Error('Message data must be an object');
        }
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            throw new Error('WebSocket is not connected');
        }
        
        this.ws.send(JSON.stringify({ type, data }));
    }
    
    on(eventType: string, handler: (data: any) => void): void {
        if (typeof eventType !== 'string' || !eventType) {
            throw new Error('Event type must be a non-empty string');
        }
        if (typeof handler !== 'function') {
            throw new Error('Handler must be a function');
        }
        
        this.eventHandlers.set(eventType, handler);
    }
    
    private handleMessage(message: any): void {
        if (!message || typeof message !== 'object') {
            console.error('Invalid message format:', message);
            return;
        }
        if (!message.type || typeof message.type !== 'string') {
            console.error('Message missing type field:', message);
            return;
        }
        
        const handler = this.eventHandlers.get(message.type);
        if (handler) {
            try {
                handler(message.data);
            } catch (error) {
                console.error(`Error handling ${message.type}:`, error);
            }
        }
    }
}
```

### Frontend Store Implementation

```typescript
import { create } from 'zustand';
import { WebSocketService } from '../services/websocket';

interface BotStore {
    // State
    bots: Record<string, BotState>;
    currentBotId: string | null;
    connected: boolean;
    thinking: boolean;
    error: string | null;
    
    // WebSocket service
    wsService: WebSocketService | null;
    
    // Actions
    connect: () => Promise<void>;
    disconnect: () => void;
    createBot: (name: string) => Promise<string>;
    sendMessage: (botId: string, content: string) => Promise<void>;
    setBotState: (botState: BotState) => void;
    setError: (error: string | null) => void;
}

export const useBotStore = create<BotStore>((set, get) => ({
    // Initial state
    bots: {},
    currentBotId: null,
    connected: false,
    thinking: false,
    error: null,
    wsService: null,
    
    // Actions
    connect: async () => {
        const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';
        const wsService = new WebSocketService(wsUrl);
        
        // Set up event handlers
        wsService.on('bot_response', (data) => {
            const { botState } = data;
            get().setBotState(botState);
            set({ thinking: false });
        });
        
        wsService.on('bot_thinking', (data) => {
            set({ thinking: data.thinking });
        });
        
        wsService.on('error', (data) => {
            get().setError(data.message);
            set({ thinking: false });
        });
        
        try {
            await wsService.connect();
            set({ wsService, connected: true, error: null });
        } catch (error) {
            set({ error: error instanceof Error ? error.message : 'Connection failed' });
            throw error;
        }
    },
    
    sendMessage: async (botId: string, content: string) => {
        if (typeof botId !== 'string' || !botId) {
            throw new Error('Bot ID must be a non-empty string');
        }
        if (typeof content !== 'string' || !content.trim()) {
            throw new Error('Message content must be a non-empty string');
        }
        
        const { wsService } = get();
        if (!wsService) {
            throw new Error('WebSocket not connected');
        }
        
        set({ thinking: true, error: null });
        wsService.sendMessage('send_message', { botId, content: content.trim() });
    },
    
    setBotState: (botState: BotState) => {
        if (!botState || typeof botState !== 'object') {
            throw new Error('Bot state must be an object');
        }
        if (!botState.id || typeof botState.id !== 'string') {
            throw new Error('Bot state must have a valid ID');
        }
        
        set((state) => ({
            bots: {
                ...state.bots,
                [botState.id]: botState
            }
        }));
    },
    
    setError: (error: string | null) => {
        set({ error });
    },
    
    disconnect: () => {
        const { wsService } = get();
        if (wsService) {
            // WebSocket will auto-close, cleanup handled in onclose
        }
        set({ wsService: null, connected: false, thinking: false });
    }
}));
```

This detailed architecture provides comprehensive interface specifications with defensive programming principles throughout. All functions include proper input validation, type checking, and error handling as required.


## Known Issues and Debugging Notes

### camelCase/snake_case Field Name Mismatches

**Issue**: Recurring problem where frontend expects camelCase field names but backend sends snake_case field names, causing "conversationTree must be an object" and similar errors.

**Root Cause**: 
- Python backend uses snake_case conventions (conversation_tree, current_node_id, is_thinking)
- TypeScript frontend uses camelCase conventions (conversationTree, currentNodeId, isThinking)
- Conversion functions exist in WebSocketHandler but may not be applied consistently across all endpoints

**Affected Fields**:
- conversation_tree ? conversationTree`n- current_node_id ? currentNodeId`n- is_connected ? isConnected`n- is_thinking ? isThinking`n- 
eact_flow_data ? 
eactFlowData`n
**Solution**: Ensure all API responses (both REST and WebSocket) apply field name conversion before sending to frontend.


## Status Update - Field Conversion Issue

**✅ RESOLVED (August 2025)**: The camelCase/snake_case field name mismatch issue has been fixed.

- BotState creation now uses camelCase aliases correctly
- WebSocket responses properly convert all field names
- The "conversationTree must be an object" error is resolved

See `FIELD_CONVERSION_FIX_SUMMARY.md` for complete details of the fix.
**Debugging**: When encountering "X must be an object" errors, first check if the issue is field name casing rather than data structure problems.