import { useState } from 'react';

interface ErrorBannerProps {
  message: string;
  onRetry?: () => void;
  dismissable?: boolean;
}

export function ErrorBanner({ message, onRetry, dismissable = true }: ErrorBannerProps) {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  return (
    <div className="ds-banner" data-tone="critical" role="alert">
      <span className="ds-banner-body">{message}</span>
      <div className="ds-cluster" style={{ '--gap': 'var(--space-2)' } as React.CSSProperties}>
        {onRetry && (
          <button type="button" className="ds-btn" data-tone="danger" data-size="sm" onClick={onRetry}>
            Retry
          </button>
        )}
        {dismissable && (
          <button
            type="button"
            className="ds-btn"
            data-tone="ghost"
            data-size="sm"
            onClick={() => setDismissed(true)}
            aria-label="Dismiss"
          >
            ×
          </button>
        )}
      </div>
    </div>
  );
}
