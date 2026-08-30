import { useConfig } from '../../../config/ConfigContext';
import { useHealthMonitor } from '../../../hooks/useHealthMonitor';
import { groupBy } from '../../../utils/filters';
import { ServiceCard } from './ServiceCard';
import type { ServiceCategory } from '../../../config/types';
import styles from './Navigation.module.css';

const CATEGORY_LABELS: Record<ServiceCategory, string> = {
  security: 'Security',
  workbenches: 'Workbenches',
  storage: 'Storage',
  infrastructure: 'Infrastructure',
  agents: 'Agents',
};

const CATEGORY_ORDER: ServiceCategory[] = ['security', 'agents', 'workbenches', 'storage', 'infrastructure'];

export function NavigationHub() {
  const config = useConfig();
  const { statusMap } = useHealthMonitor();
  const grouped = groupBy(config.services, (s) => s.category);

  return (
    <div className={styles.hub}>
      <h2 className={styles.title}>Services</h2>
      {CATEGORY_ORDER.map((category) => {
        const services = grouped.get(category);
        if (!services || services.length === 0) return null;
        return (
          <section key={category} className={styles.section}>
            <h3 className={styles.categoryHeader}>{CATEGORY_LABELS[category]}</h3>
            <div className={styles.grid}>
              {services.map((service) => (
                <ServiceCard
                  key={service.id}
                  service={service}
                  healthStatus={statusMap.get(service.id)?.status ?? 'unknown'}
                />
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}
