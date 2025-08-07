# Bots Framework React GUI - Frontend

Modern React frontend for the Bots Framework with TypeScript, Zustand state management, and WebSocket communication.

## Features

- **Real-time Chat**: WebSocket-based communication with bot backend
- **TypeScript**: Full type safety and defensive programming
- **Zustand State Management**: Lightweight and efficient state management
- **Responsive Design**: Works on desktop and mobile devices
- **Error Handling**: Comprehensive error handling and recovery
- **Auto-reconnection**: Automatic WebSocket reconnection on connection loss

## Architecture

```
src/
├── components/          # React components
│   ├── App.tsx         # Main application component
│   ├── ChatInterface.tsx # Chat interface container
│   ├── MessageList.tsx  # Message display component
│   └── MessageInput.tsx # Message input component
├── store/              # State management
│   └── botStore.ts     # Zustand store for bot state
├── types/              # TypeScript type definitions
│   └── index.ts        # All type definitions
├── utils/              # Utility functions
│   └── websocket.ts    # WebSocket management
├── test/               # Test setup
│   └── setup.ts        # Test configuration
└── main.tsx           # Application entry point
```

## Getting Started

### Prerequisites

- Node.js 16+ 
- npm or yarn
- Running backend server (see ../backend/README.md)

### Installation

```bash
cd react-gui/frontend
npm install
```

### Development

```bash
# Start development server
npm run dev

# Run linting
npm run lint

# Run tests
npm run test

# Build for production
npm run build
```

The development server will start on http://localhost:3000 and automatically proxy API requests to the backend server on http://localhost:8000.

## Configuration

### Environment Variables

Create a `.env` file in the frontend directory:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

### Proxy Configuration

The Vite configuration includes automatic proxying of API requests and WebSocket connections to the backend server. See `vite.config.ts` for details.

## Defensive Programming

This frontend follows strict defensive programming principles:

- **Input Validation**: All function inputs are validated with type checks and assertions
- **Error Handling**: Comprehensive try-catch blocks with meaningful error messages
- **Type Safety**: Full TypeScript coverage with strict type checking
- **State Validation**: All state updates are validated before application
- **WebSocket Resilience**: Automatic reconnection and error recovery

## Testing

The test suite includes:

- Component rendering tests
- WebSocket communication tests  
- State management tests
- User interaction tests
- Error handling tests

Run tests with:

```bash
npm run test
```

## Production Build

Build the application for production:

```bash
npm run build
```

The built files will be in the `dist/` directory and can be served by any static file server.

## Browser Support

- Chrome 88+
- Firefox 78+
- Safari 14+
- Edge 88+

## Performance

- Code splitting for optimal loading
- Lazy loading of components
- Efficient state updates with Zustand
- WebSocket connection pooling
- Automatic message virtualization for large conversations
