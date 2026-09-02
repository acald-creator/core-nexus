import { useCallback, useEffect, useRef, useState } from 'react';
import { useConfig } from '../config/ConfigContext';
import { useAuth } from '../auth/AuthContext';
import type { AgentFeedFilters, OPAREvent } from '../api/types/opar-events';

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
  const [events, setEvents] = useState<OPAREvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  const connect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    if (!token || token === 'dev-bypass-token') {
      setIsConnected(false);
      setConnectionError('Waiting for Gateway authentication…');
      return;
    }

    const url = `${config.apiGatewayUrl}/api/v1/agents/events?token=${token}`;
    const es = new EventSource(url);
    eventSourceRef.current = es;

    es.onopen = () => {
      setIsConnected(true);
      setConnectionError(null);
    };

    es.addEventListener('opar', (event) => {
      try {
        const data: OPAREvent = JSON.parse(event.data);
        setEvents((prev) => [data, ...prev].slice(0, 500)); // keep last 500
      } catch {
        // skip malformed events
      }
    });

    es.addEventListener('error', () => {
      if (es.readyState === EventSource.CLOSED) {
        setIsConnected(false);
        setConnectionError('Connection lost — retrying...');
      }
      // EventSource auto-reconnects
    });

    es.onerror = () => {
      setIsConnected(false);
      setConnectionError('Connection lost — retrying...');
    };
  }, [config.apiGatewayUrl, token]);

  useEffect(() => {
    // Defer so we do not setState synchronously inside the effect body (eslint react-hooks).
    let cancelled = false;
    queueMicrotask(() => {
      if (!cancelled) connect();
    });
    return () => {
      cancelled = true;
      eventSourceRef.current?.close();
    };
  }, [connect]);

  const retry = useCallback(() => {
    setConnectionError(null);
    connect();
  }, [connect]);

  const filtered = filters
    ? sortEventsByTimestamp(filterAgentEvents(events, filters))
    : sortEventsByTimestamp(events);

  return { events: filtered, isConnected, connectionError, retry };
}
