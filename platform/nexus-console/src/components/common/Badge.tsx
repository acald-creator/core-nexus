import styles from './Badge.module.css';

interface BadgeProps {
  count: number;
  variant?: 'default' | 'critical' | 'warning';
  label?: string;
}

export function Badge({ count, variant = 'default', label }: BadgeProps) {
  if (count <= 0) return null;

  return (
    <span className={`${styles.badge} ${styles[variant]}`} aria-label={label ?? `${count} items`}>
      {count > 99 ? '99+' : count}
    </span>
  );
}
