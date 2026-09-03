import { useCallback, useEffect, useRef, useState } from 'react';
import { ENDPOINTS } from '../api/endpoints';
import {
  resolveAgentFeedTransport,
  toGatewayWebSocketUrl,
  type AgentFeedTransport,
} from '../api/agentFeedUrl';
import { useConfig } from '../config/ConfigContext';
import { useAuth } from '../auth/AuthContext';
import type { AgentFeedFilters, OPAREvent } from '../api/types/opar-events';

const WS_RETRY_MAX_MS = 30_000;

function parseOparPayload(raw: unknown): OPAREvent | null {
  try {
    const data = typeof raw === 'string' ? JSON.parse(raw) : raw;
    if (!data || typeof data !== 'object') return null;
    return data as OPAREvent;
  } catch {
    return null;
  }
}

export function filterAgentEvents(events: OPAREvent[], filters: AgentFeedFilters): OPAREvent[] {
  return events.filter((e) => {
    if (filters.phase && e.phase !== filters.phase) return false;
    if (filters.target && e.target !== filters.target) return false;
    if (filters.outcomeStatus && e.outcomeStatus !== filters.outcomeStatus) return false;
    return true;
  });
}

export function sortEventsByTimestamp(events: OPAREvent[]): OPAREvent[] {
  return [...events].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
}

export function useAgentFeed(filters?: AgentFeedFilters) {
  const config = useConfig();
  const { token } = useAuth();
  const transport: AgentFeedTransport = resolveAgentFeedTransport(config.agentFeedTransport);
  const [events, setEvents] = useState<OPAREvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const webSocketRef = useRef<WebSocket | null>(null);
  const retryTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const retryDelayRef = useRef(1000);

  const pushEvent = useCallback((payload: unknown) => {
    const data = parseOparPayload(payload);
    if (!data) return;
    setEvents((prev) => [data, ...prev].slice(0, 500));
  }, []);

  const disconnect = useCallback(() => {
    if (retryTimerRef.current) {
      clearTimeout(retryTimerRef.current);
      retryTimerRef.current = null;
    }
    const es = eventSourceRef.current;
    eventSourceRef.current = null;
    es?.close();
    const ws = webSocketRef.current;
    webSocketRef.current = null;
    ws?.close();
  }, []);

  const connect = useCallback(() => {
    disconnect();

    if (!token || token === 'dev-bypass-token') {
      setIsConnected(false);
      setConnectionError('Waiting for Gateway authentication…');
      return;
    }

    if (transport === 'websocket') {
      const url = toGatewayWebSocketUrl(config.apiGatewayUrl, ENDPOINTS.agents.eventsWs, token);
      const ws = new WebSocket(url);
      webSocketRef.current = ws;

      ws.onopen = () => {
        retryDelayRef.current = 1000;
        setIsConnected(true);
        setConnectionError(null);
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data) as { event?: string; data?: unknown };
          if (msg.event === 'heartbeat') return;
          if (msg.event === 'error') {
            setConnectionError('Upstream connection lost — retrying...');
            return;
          }
          if (msg.event === 'opar') {
            pushEvent(msg.data);
          }
        } catch {
          // skip malformed frames
        }
      };

      ws.onerror = () => {
        setIsConnected(false);
        setConnectionError('Connection lost — retrying...');
      };

      ws.onclose = () => {
        if (webSocketRef.current !== ws) return;
        setIsConnected(false);
        setConnectionError('Connection lost — retrying...');
        const delay = retryDelayRef.current;
        retryDelayRef.current = Math.min(delay * 2, WS_RETRY_MAX_MS);
        retryTimerRef.current = setTimeout(() => connect(), delay);
      };
      return;
    }

    const url = `${config.apiGatewayUrl}${ENDPOINTS.agents.events}?token=${token}`;
    const es = new EventSource(url);
    eventSourceRef.current = es;

    es.onopen = () => {
      setIsConnected(true);
      setConnectionError(null);
    };

    es.addEventListener('opar', (event) => {
      pushEvent(event.data);
    });

    es.addEventListener('error', () => {
      if (es.readyState === EventSource.CLOSED) {
        setIsConnected(false);
        setConnectionError('Connection lost — retrying...');
      }
    });

    es.onerror = () => {
      setIsConnected(false);
      setConnectionError('Connection lost — retrying...');
    };
  }, [config.apiGatewayUrl, disconnect, pushEvent, token, transport]);

  useEffect(() => {
    let cancelled = false;
    queueMicrotask(() => {
      if (!cancelled) connect();
    });
    return () => {
      cancelled = true;
      disconnect();
    };
  }, [connect, disconnect]);

  const retry = useCallback(() => {
    retryDelayRef.current = 1000;
    setConnectionError(null);
    connect();
  }, [connect]);

  const filtered = filters
    ? sortEventsByTimestamp(filterAgentEvents(events, filters))
    : sortEventsByTimestamp(events);

  return { events: filtered, isConnected, connectionError, retry, transport };
}
