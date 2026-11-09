interface BadgeProps {
  count: number;
  variant?: 'default' | 'critical' | 'warning' | 'neutral';
  label?: string;
}

export function Badge({ count, variant = 'default', label }: BadgeProps) {
  if (count <= 0) return null;

  return (
    <span
      className="ds-badge"
      data-tone={variant === 'default' ? undefined : variant}
      aria-label={label ?? `${count} items`}
    >
      {count > 99 ? '99+' : count}
    </span>
  );
}
