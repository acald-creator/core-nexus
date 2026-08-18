import type { OPAREvent } from '../../../api/types/opar-events';
import styles from './AgentFeed.module.css';

interface EventDetailProps {
  event: OPAREvent;
}

export function EventDetail({ event }: EventDetailProps) {
  return (
    <div className={styles.detail}>
      <pre className={styles.payload}>
        {JSON.stringify(event.payload, null, 2)}
      </pre>
    </div>
  );
}
