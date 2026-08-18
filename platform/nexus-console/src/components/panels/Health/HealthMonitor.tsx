import { useHealthMonitor } from '../../../hooks/useHealthMonitor';
import { HealthSummaryBar } from './HealthSummaryBar';
import { StatusDot } from '../../common/StatusDot';
import { useConfig } from '../../../config/ConfigContext';
import styles from './Health.module.css';

export function HealthMonitor() {
  const config = useConfig();
  const { summary, statusMap } = useHealthMonitor();

  return (
    <div className={styles.monitor}>
      <h2 className={styles.title}>System Health</h2>
      <HealthSummaryBar summary={summary} />

      <div className={styles.serviceList}>
        {config.services.map((service) => {
          const health = statusMap.get(service.id);
          const status = health?.status || 'unknown';
          const time = health?.responseTimeMs;
          return (
            <div key={service.id} className={`${styles.serviceRow} ${status !== 'healthy' && status !== 'unknown' ? styles.highlighted : ''}`}>
              <StatusDot status={status} />
              <span className={styles.serviceName}>{service.name}</span>
              {time !== undefined && (
                <span className={styles.responseTime}>{time.toFixed(0)}ms</span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
