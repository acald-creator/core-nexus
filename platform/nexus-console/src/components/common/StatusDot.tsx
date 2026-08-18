import styles from './StatusDot.module.css';

type Status = 'healthy' | 'degraded' | 'offline' | 'unknown';

interface StatusDotProps {
  status: Status;
  label?: string;
}

export function StatusDot({ status, label }: StatusDotProps) {
  return (
    <span
      className={`${styles.dot} ${styles[status]}`}
      aria-label={label || status}
      title={label || status}
    />
  );
}
