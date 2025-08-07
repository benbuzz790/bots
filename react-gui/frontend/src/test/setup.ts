import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock ResizeObserver for ReactFlow components
global.ResizeObserver = class ResizeObserver {
  constructor(callback: ResizeObserverCallback) {
    // Store callback for potential future use
    this.callback = callback;
  }
  
  private callback: ResizeObserverCallback;
  
  observe() {
    // Mock implementation - do nothing
  }
  
  unobserve() {
    // Mock implementation - do nothing
  }
  
  disconnect() {
    // Mock implementation - do nothing
  }
};
// Mock getBoundingClientRect for ReactFlow
Element.prototype.getBoundingClientRect = vi.fn(() => ({
  width: 800,
  height: 600,
  top: 0,
  left: 0,
  bottom: 600,
  right: 800,
  x: 0,
  y: 0,
  toJSON: () => {}
}));

// Mock getComputedStyle for ReactFlow
global.getComputedStyle = vi.fn(() => ({
  getPropertyValue: vi.fn(() => ''),
  width: '800px',
  height: '600px'
})) as any;


// Mock WebSocket for testing
global.WebSocket = class MockWebSocket {
  constructor(url: string) {
    console.log('Mock WebSocket created for:', url);
  }
  send(data: string) {
    console.log('Mock WebSocket send:', data);
  }
  close() {
    console.log('Mock WebSocket closed');
  }
} as any;

// Mock socket.io-client for testing
vi.mock('socket.io-client', () => ({
  io: vi.fn(() => ({
    on: vi.fn(),
    emit: vi.fn(),
    disconnect: vi.fn(),
    connected: false
  }))
}));

// Mock ReactFlow's useReactFlow hook for testing
vi.mock('reactflow', async () => {
  const actual = await vi.importActual('reactflow');
  return {
    ...actual,
    useReactFlow: () => ({
      fitView: vi.fn(),
      zoomIn: vi.fn(),
      zoomOut: vi.fn(),
      zoomTo: vi.fn(),
    }),
  };
});
