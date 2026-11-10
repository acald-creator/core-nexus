type Status = 'healthy' | 'degraded' | 'offline' | 'unknown';

interface StatusDotProps {
  status: Status;
  label?: string;
  /** Pulse to show a live feed. Honours prefers-reduced-motion. */
  live?: boolean;
}

/**
 * Health indicator. Each status has its own colour AND shape (● ▲ ◆ ◌) so the
 * state survives red-green colour-vision deficiency; the label is the word.
 */
export function StatusDot({ status, label, live }: StatusDotProps) {
  return (
    <span
      className="ds-dot"
      data-status={status}
      data-live={live || undefined}
      role="img"
      aria-label={label || status}
      title={label || status}
    />
  );
}
