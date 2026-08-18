import type { OPAREvent } from '../../../api/types/opar-events';
import { formatTimestamp } from '../../../utils/formatters';
import styles from './AgentFeed.module.css';

interface EventRowProps {
  event: OPAREvent;
  selected: boolean;
  onSelect: () => void;
}

const PHASE_LABELS: Record<string, string> = {
  observe: 'OBSERVE',
  plan: 'PLAN',
  act: 'ACT',
  reflect: 'REFLECT',
};

export function EventRow({ event, selected, onSelect }: EventRowProps) {
  return (
    <div
      className={`${styles.row} ${selected ? styles.selected : ''}`}
      onClick={onSelect}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onSelect()}
    >
      <span className={styles.timestamp}>{formatTimestamp(event.timestamp)}</span>
      <span className={`${styles.phase} ${styles[event.phase]}`}>
        {PHASE_LABELS[event.phase]}
      </span>
      <span className={styles.target}>{event.target}</span>
      {event.toolName && <span className={styles.tool}>{event.toolName}</span>}
      <span className={`${styles.outcome} ${styles[event.outcomeStatus]}`}>
        {event.outcomeStatus}
      </span>
    </div>
  );
}
