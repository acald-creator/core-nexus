import { NavLink } from 'react-router';
import { Badge } from '../common/Badge';
import styles from './Sidebar.module.css';
import type { NavItem as NavItemType } from './types';

interface NavItemProps {
  item: NavItemType;
}

export function SidebarNavItem({ item }: NavItemProps) {
  return (
    <NavLink
      to={item.path}
      className={({ isActive }) =>
        `${styles.navItem} ${isActive ? styles.active : ''}`
      }
      aria-label={item.label}
    >
      <span className={styles.icon}>{item.icon}</span>
      <span className={styles.label}>{item.label}</span>
      {item.badge !== undefined && item.badge > 0 && (
        <Badge
          count={item.badge}
          variant="critical"
          label={`${item.badge} ${item.id === 'alerts' ? 'unacknowledged high-severity alerts' : item.id === 'approvals' ? 'pending approvals' : 'items'}`}
        />
      )}
    </NavLink>
  );
}
