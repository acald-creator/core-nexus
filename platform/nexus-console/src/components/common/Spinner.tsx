interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
}

export function Spinner({ size = 'md' }: SpinnerProps) {
  return (
    <span
      className="ds-spinner"
      data-size={size === 'md' ? undefined : size}
      role="status"
      aria-label="Loading"
    />
  );
}
