export class WebSocketService {
  private ws: WebSocket | null = null;
  private eventHandlers: Map<string, (data: any) => void> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // Start with 1 second
  private reconnectTimer: NodeJS.Timeout | null = null;

  constructor(private url: string) {
    // Input validation
    if (typeof url !== 'string' || !url.trim()) {
      throw new Error('WebSocket URL must be a non-empty string');
    }
    
    // Validate URL format
    try {
      new URL(url);
    } catch {
      throw new Error('WebSocket URL must be a valid URL');
    }
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        // Clear any existing reconnect timer
        if (this.reconnectTimer) {
          clearTimeout(this.reconnectTimer);
          this.reconnectTimer = null;
        }

        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          this.reconnectDelay = 1000;
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            if (typeof event.data !== 'string') {
              console.error('WebSocket message data must be string:', typeof event.data);
              return;
            }

            const message = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(new Error('WebSocket connection failed'));
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason);
          this.ws = null;
          
          // Attempt reconnection if not a clean close
          if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect();
          }
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  disconnect(): void {
    // Clear reconnect timer
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    // Close WebSocket connection
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }

    // Reset reconnection state
    this.reconnectAttempts = 0;
    this.reconnectDelay = 1000;
  }

  sendMessage(type: string, data: any): void {
    // Input validation
    if (typeof type !== 'string' || !type.trim()) {
      throw new Error('Message type must be a non-empty string');
    }
    if (!data || typeof data !== 'object') {
      throw new Error('Message data must be an object');
    }
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket is not connected');
    }

    try {
      const message = { type: type.trim(), data };
      this.ws.send(JSON.stringify(message));
    } catch (error) {
      console.error('Failed to send WebSocket message:', error);
      throw new Error('Failed to send message');
    }
  }

  on(eventType: string, handler: (data: any) => void): void {
    // Input validation
    if (typeof eventType !== 'string' || !eventType.trim()) {
      throw new Error('Event type must be a non-empty string');
    }
    if (typeof handler !== 'function') {
      throw new Error('Handler must be a function');
    }

    this.eventHandlers.set(eventType.trim(), handler);
  }

  off(eventType: string): void {
    // Input validation
    if (typeof eventType !== 'string' || !eventType.trim()) {
      throw new Error('Event type must be a non-empty string');
    }

    this.eventHandlers.delete(eventType.trim());
  }

  private handleMessage(message: any): void {
    // Input validation
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
    } else {
      console.warn(`No handler for message type: ${message.type}`);
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) {
      return; // Already scheduled
    }

    this.reconnectAttempts++;
    console.log(`Scheduling reconnect attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${this.reconnectDelay}ms`);

    this.reconnectTimer = setTimeout(async () => {
      this.reconnectTimer = null;
      
      try {
        await this.connect();
        console.log('WebSocket reconnected successfully');
      } catch (error) {
        console.error('Reconnection failed:', error);
        
        // Exponential backoff with jitter
        this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000);
        
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect();
        } else {
          console.error('Max reconnection attempts reached');
        }
      }
    }, this.reconnectDelay);
  }

  get isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  get connectionState(): string {
    if (!this.ws) return 'CLOSED';
    
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING: return 'CONNECTING';
      case WebSocket.OPEN: return 'OPEN';
      case WebSocket.CLOSING: return 'CLOSING';
      case WebSocket.CLOSED: return 'CLOSED';
      default: return 'UNKNOWN';
    }
  }
}
