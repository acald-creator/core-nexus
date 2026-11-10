import type { ReactNode } from 'react';
import { ApprovalDock } from './ApprovalDock';
import styles from './DashboardLayout.module.css';

interface DashboardLayoutProps {
  sidebar: ReactNode;
  children: ReactNode;
}

/**
 * App shell. The grid reacts to <html data-layout="sidebar|rail|topbar"> and
 * data-width="fluid|contained" through the design-system tokens; the panel
 * area goes two-up once its own container is wide enough (not the viewport).
 */
export function DashboardLayout({ sidebar, children }: DashboardLayoutProps) {
  return (
    <div className={`ds-shell ${styles.layout}`}>
      {sidebar}
      <main className={`ds-main ${styles.main}`}>
        <div className={`ds-panels ${styles.content}`}>{children}</div>
        <ApprovalDock />
      </main>
    </div>
  );
}
