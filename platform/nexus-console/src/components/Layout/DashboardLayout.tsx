import type { ReactNode } from 'react';
import styles from './DashboardLayout.module.css';

interface DashboardLayoutProps {
  sidebar: ReactNode;
  children: ReactNode;
}

export function DashboardLayout({ sidebar, children }: DashboardLayoutProps) {
  return (
    <div className={styles.layout}>
      {sidebar}
      <main className={styles.main} role="main">
        {children}
      </main>
    </div>
  );
}
