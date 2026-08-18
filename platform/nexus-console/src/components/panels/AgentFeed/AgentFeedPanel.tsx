import { useState } from 'react';
import { useAgentFeed } from '../../../hooks/useAgentFeed';
import { ErrorBanner } from '../../common/ErrorBanner';
import { EventRow } from './EventRow';
import { EventDetail } from './EventDetail';
import type { AgentFeedFilters, OPARPhase, OutcomeStatus } from '../../../api/types/opar-events';
import styles from './AgentFeed.module.css';

export function AgentFeedPanel() {
  const [filters, setFilters] = useState<AgentFeedFilters>({});
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const { events, isConnected, connectionError, retry } = useAgentFeed(filters);

  const selectedEvent = events.find((e) => e.id === selectedId);

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <h2>Agent Feed</h2>
        <span className={`${styles.connectionStatus} ${isConnected ? styles.connected : styles.disconnected}`}>
          {isConnected ? '● Connected' : '○ Disconnected'}
        </span>
      </div>

      {connectionError && (
        <ErrorBanner message={connectionError} onRetry={retry} />
      )}

      <div className={styles.filters}>
        <select
          value={filters.phase || ''}
          onChange={(e) => setFilters({ ...filters, phase: (e.target.value || undefined) as OPARPhase | undefined })}
          aria-label="Filter by phase"
        >
          <option value="">All phases</option>
          <option value="observe">Observe</option>
          <option value="plan">Plan</option>
          <option value="act">Act</option>
          <option value="reflect">Reflect</option>
        </select>

        <select
          value={filters.outcomeStatus || ''}
          onChange={(e) => setFilters({ ...filters, outcomeStatus: (e.target.value || undefined) as OutcomeStatus | undefined })}
          aria-label="Filter by outcome"
        >
          <option value="">All outcomes</option>
          <option value="success">Success</option>
          <option value="failure">Failure</option>
          <option value="pending">Pending</option>
          <option value="blocked">Blocked</option>
        </select>
      </div>

      {events.length === 0 ? (
        <div className={styles.empty}>
          <p>No active agent sessions</p>
          <p className={styles.emptyHint}>Events will appear here when an OPAR agent is running.</p>
        </div>
      ) : (
        <div className={styles.eventList}>
          {events.map((event) => (
            <div key={event.id}>
              <EventRow
                event={event}
                selected={selectedId === event.id}
                onSelect={() => setSelectedId(selectedId === event.id ? null : event.id)}
              />
              {selectedId === event.id && selectedEvent && (
                <EventDetail event={selectedEvent} />
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
