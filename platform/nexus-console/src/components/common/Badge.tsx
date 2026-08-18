import styles from './Badge.module.css';

interface BadgeProps {
  count: number;
  variant?: 'default' | 'critical' | 'warning';
}

export function Badge({ count, variant = 'default' }: BadgeProps) {
  if (count <= 0) return null;

  return (
    <span className={`${styles.badge} ${styles[variant]}`} aria-label={`${count} items`}>
      {count > 99 ? '99+' : count}
    </span>
  );
}
