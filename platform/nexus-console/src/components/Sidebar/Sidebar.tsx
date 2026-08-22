import { useState } from 'react';
import { SidebarNavItem } from './NavItem';
import { useAlerts } from '../../hooks/useAlerts';
import { useApprovals } from '../../hooks/useApprovals';
import type { NavItem } from './types';
import styles from './Sidebar.module.css';

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const { unacknowledgedCriticalHighCount } = useAlerts();
  const { pendingCount } = useApprovals();

  const navItems: NavItem[] = [
    { id: 'overview', label: 'Overview', icon: '⚡', path: '/' },
    { id: 'agent-feed', label: 'Agent Feed', icon: '🤖', path: '/agent-feed' },
    { id: 'alerts', label: 'Alerts', icon: '🔔', path: '/alerts', badge: unacknowledgedCriticalHighCount },
    { id: 'approvals', label: 'Approvals', icon: '✋', path: '/approvals', badge: pendingCount },
    { id: 'skills', label: 'Skills', icon: '📚', path: '/skills' },
    { id: 'artifacts', label: 'Artifacts', icon: '📦', path: '/artifacts' },
    { id: 'settings', label: 'Settings', icon: '⚙️', path: '/settings' },
  ];

  return (
    <aside className={`${styles.sidebar} ${collapsed ? styles.collapsed : ''}`}>
      <div className={styles.header}>
        <span className={styles.brand}>⚡ Nexus</span>
        <button
          className={styles.collapseBtn}
          onClick={() => setCollapsed(!collapsed)}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? '→' : '←'}
        </button>
      </div>

      <nav className={styles.nav} aria-label="Main navigation">
        {navItems.map((item) => (
          <SidebarNavItem key={item.id} item={item} />
        ))}
      </nav>
    </aside>
  );
}
