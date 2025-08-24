// WebSocket hook
import { useState, useEffect, useCallback, useRef } from 'react';
import type { UseWebSocketReturn } from './types';
import type { WebSocketConfig } from '../types/api';
import { config } from '../config';

type WebSocketReadyState = 0 | 1 | 2 | 3; // CONNECTING | OPEN | CLOSING | CLOSED

interface UseWebSocketOptions {
  url?: string;
  protocols?: string | string[];
  reconnect?: boolean;
  reconnectAttempts?: number;
  reconnectInterval?: number;
  heartbeat?: boolean;
  heartbeatInterval?: number;
  onOpen?: (event: Event) => void;
  onClose?: (event: CloseEvent) => void;
  onError?: (event: Event) => void;
  onMessage?: (message: unknown) => void;
  shouldReconnect?: (closeEvent: CloseEvent) => boolean;
}

const useWebSocket = (options: UseWebSocketOptions = {}): UseWebSocketReturn => {
  const {
    url = config.ws.URL,
    protocols,
    reconnect = true,
    reconnectAttempts = config.ws.MAX_RECONNECT_ATTEMPTS,
    reconnectInterval = config.ws.RECONNECT_INTERVAL,
    heartbeat = true,
    heartbeatInterval = config.ws.HEARTBEAT_INTERVAL,
    onOpen,
    onClose,
    onError,
    onMessage,
    shouldReconnect,
  } = options;

  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reconnectCount, setReconnectCount] = useState(0);

  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const messageQueueRef = useRef<unknown[]>([]);
  const eventListenersRef = useRef<Map<string, Set<(data: unknown) => void>>>(new Map());

  // Clear timeouts
  const clearTimeouts = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (heartbeatTimeoutRef.current) {
      clearTimeout(heartbeatTimeoutRef.current);
      heartbeatTimeoutRef.current = null;
    }
  }, []);

  // Start heartbeat
  const startHeartbeat = useCallback(() => {
    if (!heartbeat || !socket || socket.readyState !== WebSocket.OPEN) return;

    const sendHeartbeat = () => {
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: 'ping', timestamp: Date.now() }));
        heartbeatTimeoutRef.current = setTimeout(sendHeartbeat, heartbeatInterval);
      }
    };

    heartbeatTimeoutRef.current = setTimeout(sendHeartbeat, heartbeatInterval);
  }, [heartbeat, heartbeatInterval, socket]);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    if (isConnecting) {
      return; // Already connecting
    }

    setIsConnecting(true);
    setError(null);
    clearTimeouts();

    try {
      const ws = new WebSocket(url, protocols);
      setSocket(ws);

      ws.onopen = (event) => {
        setIsConnected(true);
        setIsConnecting(false);
        setReconnectCount(0);
        setError(null);

        // Send queued messages
        while (messageQueueRef.current.length > 0) {
          const message = messageQueueRef.current.shift();
          ws.send(JSON.stringify(message));
        }

        // Start heartbeat
        startHeartbeat();

        onOpen?.(event);
      };

      ws.onclose = (event) => {
        setIsConnected(false);
        setIsConnecting(false);
        clearTimeouts();

        const shouldAttemptReconnect = shouldReconnect ? shouldReconnect(event) : reconnect;
        
        if (shouldAttemptReconnect && reconnectCount < reconnectAttempts && !event.wasClean) {
          const timeout = reconnectInterval * Math.pow(2, reconnectCount); // Exponential backoff
          reconnectTimeoutRef.current = setTimeout(() => {
            setReconnectCount(prev => prev + 1);
            connect();
          }, timeout);
        }

        onClose?.(event);
      };

      ws.onerror = (event) => {
        setError('WebSocket connection error');
        setIsConnecting(false);
        onError?.(event);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const message = {
            data,
            timestamp: Date.now(),
            type: data.type || 'message',
          };

          // Handle heartbeat response
          if (data.type === 'pong') {
            return;
          }

          // Emit to event listeners
          const listeners = eventListenersRef.current.get(message.type);
          if (listeners) {
            listeners.forEach(listener => listener(data));
          }

          // Emit to generic message listeners
          const messageListeners = eventListenersRef.current.get('message');
          if (messageListeners) {
            messageListeners.forEach(listener => listener(message));
          }

          onMessage?.(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };
    } catch {
      setError('Failed to create WebSocket connection');
      setIsConnecting(false);
    }
  }, [url, protocols, socket, isConnecting, reconnect, reconnectAttempts, reconnectInterval, reconnectCount, shouldReconnect, startHeartbeat, onOpen, onClose, onError, onMessage, clearTimeouts]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    clearTimeouts();
    setReconnectCount(0);
    
    if (socket) {
      socket.close(1000, 'Manual disconnect');
      setSocket(null);
    }
    
    setIsConnected(false);
    setIsConnecting(false);
  }, [socket, clearTimeouts]);

  // Send message
  const sendMessage = useCallback((message: unknown) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(message));
    } else {
      // Queue message for when connection is established
      messageQueueRef.current.push(message);
      
      // Try to connect if not already connecting
      if (!isConnecting && !isConnected) {
        connect();
      }
    }
  }, [socket, isConnecting, isConnected, connect]);



  // Auto-connect on mount
  useEffect(() => {
    if (url) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps



  return {
    socket,
    isConnected,
    isConnecting,
    error,
    send: sendMessage,
    connect,
    disconnect,
    subscribe: () => () => {},
    unsubscribe: () => {},
  };
};

// WebSocket utilities
export const webSocketUtils = {
  // Create WebSocket URL with authentication
  createAuthenticatedUrl: (baseUrl: string, token?: string): string => {
    if (!token) return baseUrl;
    
    const url = new URL(baseUrl);
    url.searchParams.set('token', token);
    return url.toString();
  },

  // Get ready state name
  getReadyStateName: (readyState: WebSocketReadyState): string => {
    switch (readyState) {
      case WebSocket.CONNECTING:
        return 'CONNECTING';
      case WebSocket.OPEN:
        return 'OPEN';
      case WebSocket.CLOSING:
        return 'CLOSING';
      case WebSocket.CLOSED:
        return 'CLOSED';
      default:
        return 'UNKNOWN';
    }
  },

  // Check if close event indicates a reconnectable error
  isReconnectableClose: (event: CloseEvent): boolean => {
    // Don't reconnect on normal closure or policy violations
    return ![1000, 1001, 1005, 1006, 1015].includes(event.code);
  },

  // Create message with metadata
  createMessage: (type: string, data: unknown, metadata?: Record<string, unknown>) => {
    return {
      type,
      data,
      timestamp: Date.now(),
      id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      ...metadata,
    };
  },

  // Parse WebSocket URL
  parseWebSocketUrl: (url: string) => {
    try {
      const parsed = new URL(url);
      return {
        protocol: parsed.protocol,
        host: parsed.host,
        port: parsed.port,
        pathname: parsed.pathname,
        search: parsed.search,
        isSecure: parsed.protocol === 'wss:',
      };
    } catch {
      return null;
    }
  },

  // Validate WebSocket URL
  isValidWebSocketUrl: (url: string): boolean => {
    try {
      const parsed = new URL(url);
      return ['ws:', 'wss:'].includes(parsed.protocol);
    } catch {
      return false;
    }
  },

  // Calculate reconnect delay with exponential backoff
  calculateReconnectDelay: (attempt: number, baseDelay = 1000, maxDelay = 30000): number => {
    const delay = baseDelay * Math.pow(2, attempt);
    return Math.min(delay, maxDelay);
  },

  // Create WebSocket configuration
  createConfig: (overrides: Partial<WebSocketConfig> = {}): WebSocketConfig => {
      return {
        url: config.ws.URL,
        reconnect: true,
        maxReconnectAttempts: config.ws.MAX_RECONNECT_ATTEMPTS,
        reconnectInterval: config.ws.RECONNECT_INTERVAL,
        ...overrides,
      };
    },
};

export default useWebSocket;