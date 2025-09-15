import { useEffect, useRef } from 'react';

// Mock WebSocket service for real-time updates
// In a real implementation, this would connect to:
// /api/v1/ws/router/{session_id}
// /api/v1/ws/merge/{session_id}

export interface WebSocketMessage {
  type: 'router_plan' | 'router_execution' | 'router_completion' | 'router_error' | 'merge_proposed' | 'merge_applied' | 'node_update' | 'node_stale';
  payload: any;
  timestamp: number;
}

export class WebSocketService {
  private static instance: WebSocketService;
  private ws: WebSocket | null = null;
  private listeners: Array<(message: WebSocketMessage) => void> = [];
  private sessionId: string | null = null;
  
  private constructor() {}
  
  public static getInstance(): WebSocketService {
    if (!WebSocketService.instance) {
      WebSocketService.instance = new WebSocketService();
    }
    return WebSocketService.instance;
  }
  
  public connect(sessionId: string): void {
    if (this.sessionId === sessionId && this.ws?.readyState === WebSocket.OPEN) {
      return;
    }
    
    this.sessionId = sessionId;
    
    // Close existing connection
    if (this.ws) {
      this.ws.close();
    }
    
    // In a real implementation, this would connect to the actual WebSocket endpoint
    // const wsUrl = `${import.meta.env.VITE_WS_BASE_URL}/ws/router/${sessionId}`;
    // this.ws = new WebSocket(wsUrl);
    
    // Mock implementation for now
    console.log(`Connecting to WebSocket for session: ${sessionId}`);
    
    // Simulate connection
    setTimeout(() => {
      this.simulateMessages();
    }, 1000);
  }
  
  public disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.sessionId = null;
  }
  
  public addListener(listener: (message: WebSocketMessage) => void): void {
    this.listeners.push(listener);
  }
  
  public removeListener(listener: (message: WebSocketMessage) => void): void {
    this.listeners = this.listeners.filter(l => l !== listener);
  }
  
  private simulateMessages(): void {
    if (!this.sessionId) return;
    
    // Simulate periodic updates
    const messages: WebSocketMessage[] = [
      {
        type: 'router_plan',
        payload: {
          planId: 'plan-123',
          steps: [
            { type: 'retrieve_nodes', count: 3 },
            { type: 'execute_pipeline', pipeline: 'summarize_and_translate' }
          ]
        },
        timestamp: Date.now()
      },
      {
        type: 'router_execution',
        payload: {
          planId: 'plan-123',
          step: 'retrieve_nodes',
          status: 'completed'
        },
        timestamp: Date.now() + 2000
      },
      {
        type: 'router_completion',
        payload: {
          planId: 'plan-123',
          result: 'Successfully retrieved 3 relevant nodes and executed pipeline'
        },
        timestamp: Date.now() + 5000
      }
    ];
    
    messages.forEach((message, index) => {
      setTimeout(() => {
        this.listeners.forEach(listener => listener(message));
      }, message.timestamp - Date.now() + (index * 1000));
    });
  }
  
  // In a real implementation, this would handle actual WebSocket events
  /*
  private setupWebSocket(): void {
    if (!this.ws) return;
    
    this.ws.onopen = () => {
      console.log('WebSocket connected');
    };
    
    this.ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        this.listeners.forEach(listener => listener(message));
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };
    
    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      // Attempt to reconnect
      if (this.sessionId) {
        setTimeout(() => this.connect(this.sessionId!), 5000);
      }
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }
  */
}

// React hook for using WebSocket
export function useWebSocket(sessionId: string, onMessage: (message: WebSocketMessage) => void) {
  const onMessageRef = useRef(onMessage);
  
  // Keep the callback reference updated
  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);
  
  useEffect(() => {
    if (!sessionId) return;
    
    const wsService = WebSocketService.getInstance();
    
    // Connect to WebSocket
    wsService.connect(sessionId);
    
    // Add listener
    const listener = (message: WebSocketMessage) => {
      onMessageRef.current(message);
    };
    
    wsService.addListener(listener);
    
    // Cleanup
    return () => {
      wsService.removeListener(listener);
      // Don't disconnect here as other components might still need the connection
    };
  }, [sessionId]);
}
