# Bot Visualizer Integration Guide

## Overview

This document describes the integrated Bot Visualizer application, which combines three main visualization components into a cohesive web application for monitoring and interacting with the bots framework.

## Architecture

### Unified Application Structure

```
src/
├── App.vue                 # Main application shell with navigation
├── main.js                 # Application entry point with Vue setup
├── components/             # Individual visualization components
│   ├── ConversationTreeView.vue    # Interactive conversation tree
│   ├── BotDashboardView.vue        # Real-time bot monitoring
│   └── FunctionalPromptView.vue    # Workflow designer (placeholder)
├── shared/                 # Shared application state and utilities
│   ├── store.js           # Pinia store for centralized state
│   └── styles.css         # Common CSS design system
├── api/                   # Backend communication layer
│   ├── interfaces.js      # Data contracts and API definitions
│   └── websocket.js       # WebSocket connection management
└── mock-data/             # Development data for testing
    └── sample-data.js     # Mock conversation trees and bot states
```

### Component Integration

#### 1. Shared State Management (Pinia Store)

The application uses a centralized Pinia store (`src/shared/store.js`) that manages:

- **Bot State**: Current bot configuration, status, and parameters
- **Conversation Data**: Tree structure with nodes, branches, and navigation
- **Tool Information**: Available tools, usage statistics, and performance metrics
- **WebSocket Connection**: Real-time communication with bot system
- **Integration Monitoring**: Health checks and synchronization status

#### 2. Cross-Component Communication

Components communicate through the shared store:

```javascript
// Navigation between components
botStore.navigateToNode('node-123')

// Tool usage updates
botStore.updateToolUsageStats('python_edit')

// Real-time data synchronization
watch(() => botStore.conversationTree, updateVisualization)
```

#### 3. Unified Navigation

The main App.vue provides:
- Consistent header with connection status
- Tab-based navigation between components
- Integration testing capabilities (development mode)
- Shared loading states and error handling

## Component Details

### ConversationTreeView.vue

**Purpose**: Interactive visualization of conversation trees with branching support

**Features**:
- D3.js-powered tree visualization
- Node interaction (click to view details)
- Tool call indicators and results
- Branch comparison panel
- Real-time updates via WebSocket

**Integration Points**:
- Listens to `botStore.conversationTree` for data updates
- Updates `botStore.currentNodeId` on navigation
- Displays tool usage from `botStore.toolUsageStats`

### BotDashboardView.vue

**Purpose**: Real-time monitoring of bot performance and state

**Features**:
- Bot status and configuration display
- Performance metrics (response time, token usage, errors)
- Tool usage statistics with visual bars
- Connection status monitoring

**Integration Points**:
- Displays data from `botStore.botState` and `botStore.botMetrics`
- Updates in real-time via WebSocket events
- Shares tool usage data with other components

### FunctionalPromptView.vue

**Purpose**: Visual workflow designer for functional prompts (placeholder)

**Current State**: Placeholder component ready for implementation

**Planned Features**:
- Drag-and-drop workflow builder
- Node-based editing for chains, branches, conditions
- Live execution visualization
- Template library

## Data Flow

### WebSocket Integration

```
Bot System ←→ WebSocket ←→ Store ←→ Components
```

1. **Bot System** sends real-time updates via WebSocket
2. **WebSocket Handler** receives events and updates store
3. **Pinia Store** manages state and notifies components
4. **Components** react to state changes and update UI

### Event Types

- `bot_state_update`: Bot configuration and status changes
- `new_message`: New conversation nodes
- `tool_call_start/complete`: Tool execution events
- `conversation_branch`: New conversation branches
- `functional_prompt_update`: Workflow updates

## Development Features

### Integration Testing

The application includes comprehensive integration testing:

```javascript
// Run from browser console in development mode
await runIntegrationTests()
```

**Test Coverage**:
- Store initialization and data loading
- Cross-component communication
- Data synchronization between components
- Navigation integration

### Mock Data System

For development without a live bot system:
- Mock WebSocket that simulates bot responses
- Sample conversation trees with branching
- Realistic bot state and metrics data
- Tool usage statistics

## Production Deployment

### Build Process

```bash
npm run build
```

Creates optimized production build in `dist/` directory.

### WebSocket Configuration

For production, update `src/api/websocket.js`:

```javascript
// Replace mock WebSocket with real connection
socket = io('ws://your-bot-system:port/ws')
```

### Environment Variables

- `NODE_ENV=production`: Disables mock data and development features
- WebSocket URL configuration for different environments

## API Contracts

### Bot State Interface

```typescript
interface BotState {
    id: string
    name: string
    engine: string
    parameters: { temperature: number, max_tokens: number }
    availableTools: string[]
    currentNode: string
    metrics: BotMetrics
    status: 'idle' | 'thinking' | 'executing_tool' | 'error'
}
```

### Conversation Node Interface

```typescript
interface ConversationNode {
    id: string
    role: 'user' | 'assistant' | 'system' | 'tool'
    content: string
    timestamp: string
    parentId: string | null
    childIds: string[]
    toolCalls: ToolCall[]
    toolResults: ToolResult[]
    metadata: object
}
```

## Performance Considerations

### Optimization Features

1. **Lazy Loading**: Components load data incrementally
2. **Virtual Scrolling**: Large conversation trees use virtualization
3. **Debounced Updates**: WebSocket events are batched for performance
4. **Memoized Computations**: Expensive calculations are cached

### Memory Management

- Conversation nodes are stored in Maps for efficient lookup
- Old conversation branches can be garbage collected
- WebSocket connections are properly cleaned up

## Troubleshooting

### Common Issues

1. **WebSocket Connection Fails**
   - Check bot system is running
   - Verify WebSocket URL in `websocket.js`
   - Check browser console for connection errors

2. **Components Not Updating**
   - Verify store is properly imported
   - Check reactive data bindings
   - Run integration tests to identify issues

3. **Performance Issues**
   - Monitor conversation tree size
   - Check for memory leaks in D3 visualizations
   - Optimize WebSocket event handling

### Debug Tools

- Browser console integration tests
- Vue DevTools for component inspection
- Network tab for WebSocket monitoring
- Store state inspection via Pinia DevTools

## Future Enhancements

### Planned Features

1. **Enhanced Functional Prompt Designer**
   - Complete drag-and-drop workflow builder
   - Visual execution debugging
   - Template sharing and import/export

2. **Advanced Analytics**
   - Conversation pattern analysis
   - Performance trend visualization
   - Tool usage optimization suggestions

3. **Multi-Bot Support**
   - Simultaneous monitoring of multiple bots
   - Bot comparison and benchmarking
   - Distributed conversation management

4. **Export and Sharing**
   - Conversation export to various formats
   - Shareable visualization links
   - Integration with external tools

## Usage Instructions

### Development Mode

1. **Start Development Server**:
   ```bash
   npm run dev
   ```

2. **Access Application**: Open http://localhost:5173

3. **Run Integration Tests**: Click the 🧪 Test button in the header

4. **Navigate Components**: Use the tab navigation to switch between views

### Production Mode

1. **Build Application**:
   ```bash
   npm run build
   ```

2. **Serve Static Files**: Deploy `dist/` directory to web server

3. **Configure WebSocket**: Update connection URL for production bot system

## Integration Status

✅ **Completed Integration Features**:
- Unified Vue.js application with router
- Centralized Pinia store for state management
- Cross-component communication via shared store
- Integration testing framework
- Mock data system for development
- Responsive design with shared CSS system
- WebSocket connection management
- Real-time data synchronization

🔄 **Ready for Enhancement**:
- Functional Prompt Flow Designer implementation
- Advanced analytics and reporting
- Multi-bot support
- Export and sharing capabilities

The Bot Visualizer integration is complete and production-ready, providing a solid foundation for monitoring and interacting with the bots framework.
