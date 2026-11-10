import { SidebarNavItem } from './NavItem';
import { useAlerts } from '../../hooks/useAlerts';
import { useApprovals } from '../../hooks/useApprovals';
import { useAppearance } from '../../design-system/AppearanceContext';
import type { NavItem } from './types';
import styles from './Sidebar.module.css';

export function Sidebar() {
  const { appearance, setAppearance } = useAppearance();
  const { unacknowledgedCriticalHighCount } = useAlerts();
  const { pendingCount } = useApprovals();

  const isRail = appearance.layout === 'rail';
  const isTopbar = appearance.layout === 'topbar';

  const navItems: NavItem[] = [
    { id: 'overview', label: 'Overview', icon: '⚡', path: '/' },
    { id: 'agent-feed', label: 'Agent Feed', icon: '🤖', path: '/agent-feed' },
    { id: 'runs', label: 'Runs', icon: '▸', path: '/runs' },
    { id: 'alerts', label: 'Alerts', icon: '🔔', path: '/alerts', badge: unacknowledgedCriticalHighCount },
    { id: 'approvals', label: 'Approvals', icon: '✋', path: '/approvals', badge: pendingCount },
    { id: 'skills', label: 'Skills', icon: '📚', path: '/skills' },
    { id: 'artifacts', label: 'Artifacts', icon: '📦', path: '/artifacts' },
    { id: 'settings', label: 'Settings', icon: '⚙️', path: '/settings' },
  ];

  return (
    <aside className={styles.sidebar} data-layout={appearance.layout}>
      <div className={styles.header}>
        <span className={styles.brand}>⚡ Nexus</span>
        {!isTopbar && (
          <button
            type="button"
            className={`ds-btn ${styles.collapseBtn}`}
            data-tone="ghost"
            data-size="icon"
            onClick={() => setAppearance('layout', isRail ? 'sidebar' : 'rail')}
            aria-label={isRail ? 'Expand sidebar' : 'Collapse sidebar'}
            aria-expanded={!isRail}
          >
            {isRail ? '→' : '←'}
          </button>
        )}
      </div>

      <nav className={styles.nav} aria-label="Main navigation">
        {navItems.map((item) => (
          <SidebarNavItem key={item.id} item={item} />
        ))}
      </nav>
    </aside>
  );
}
