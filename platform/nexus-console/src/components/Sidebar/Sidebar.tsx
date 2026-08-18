import { useState } from 'react';
import { SidebarNavItem } from './NavItem';
import type { NavItem } from './types';
import styles from './Sidebar.module.css';

interface SidebarProps {
  alertsBadge?: number;
  approvalsBadge?: number;
}

export function Sidebar({ alertsBadge = 0, approvalsBadge = 0 }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);

  const navItems: NavItem[] = [
    { id: 'overview', label: 'Overview', icon: '⚡', path: '/' },
    { id: 'agent-feed', label: 'Agent Feed', icon: '🤖', path: '/agent-feed' },
    { id: 'alerts', label: 'Alerts', icon: '🔔', path: '/alerts', badge: alertsBadge },
    { id: 'approvals', label: 'Approvals', icon: '✋', path: '/approvals', badge: approvalsBadge },
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
