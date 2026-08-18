import { useState } from 'react';
import styles from './ErrorBanner.module.css';

interface ErrorBannerProps {
  message: string;
  onRetry?: () => void;
  dismissable?: boolean;
}

export function ErrorBanner({ message, onRetry, dismissable = true }: ErrorBannerProps) {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  return (
    <div className={styles.banner} role="alert">
      <span className={styles.message}>{message}</span>
      <div className={styles.actions}>
        {onRetry && (
          <button className={styles.retryBtn} onClick={onRetry}>Retry</button>
        )}
        {dismissable && (
          <button className={styles.dismissBtn} onClick={() => setDismissed(true)} aria-label="Dismiss">×</button>
        )}
      </div>
    </div>
  );
}
