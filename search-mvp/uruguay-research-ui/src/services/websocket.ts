import { WebSocketMessage } from '../types/research.types';

export class ResearchWebSocket {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private callbacks: {
    onMessage?: (message: WebSocketMessage) => void;
    onError?: (error: Event) => void;
    onConnect?: () => void;
    onDisconnect?: () => void;
  } = {};

  constructor(private jobId: string) {}

  connect(callbacks: {
    onMessage?: (message: WebSocketMessage) => void;
    onError?: (error: Event) => void;
    onConnect?: () => void;
    onDisconnect?: () => void;
  }) {
    this.callbacks = callbacks;
    this.establishConnection();
  }

  private establishConnection() {
    const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';
    const fullUrl = `${wsUrl}/research/${this.jobId}/stream`;
    console.log('🔗 Connecting to WebSocket:', fullUrl);
    console.log('📊 WebSocket URL components:', { wsUrl, jobId: this.jobId, fullUrl });
    
    try {
      this.ws = new WebSocket(fullUrl);
      console.log('📊 WebSocket created, readyState:', this.ws.readyState);
    } catch (error) {
      console.error('❌ Failed to create WebSocket:', error);
      return;
    }

    this.ws.onopen = () => {
      console.log('✅ WebSocket connected successfully');
      console.log('📊 WebSocket readyState:', this.ws?.readyState);
      console.log('📊 WebSocket URL:', this.ws?.url);
      this.reconnectAttempts = 0;
      this.callbacks.onConnect?.();
    };

    this.ws.onmessage = (event) => {
      console.log('📥 RAW WebSocket data received:', event.data);
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        console.log('✅ Parsed WebSocket message:', message);
        this.callbacks.onMessage?.(message);
      } catch (error) {
        console.error('❌ Failed to parse WebSocket message:', error);
        console.error('Raw data was:', event.data);
      }
    };

    this.ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
      this.callbacks.onError?.(error);
    };

    this.ws.onclose = (event) => {
      console.log('🔌 WebSocket disconnected:', {
        code: event.code,
        reason: event.reason,
        wasClean: event.wasClean
      });
      this.callbacks.onDisconnect?.();
      this.attemptReconnect();
    };
  }

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      setTimeout(() => {
        this.establishConnection();
      }, this.reconnectDelay * this.reconnectAttempts);
    }
  }

  send(message: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.error('WebSocket is not connected');
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}