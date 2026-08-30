import { Link } from 'react-router';
import { StatusDot } from '../../common/StatusDot';
import type { ServiceEntry } from '../../../config/types';
import styles from './Navigation.module.css';

interface ServiceCardProps {
  service: ServiceEntry;
  healthStatus?: 'healthy' | 'degraded' | 'offline' | 'unknown';
}

function isInternalPath(url: string): boolean {
  return url.startsWith('/');
}

export function ServiceCard({ service, healthStatus = 'unknown' }: ServiceCardProps) {
  const body = (
    <>
      <div className={styles.cardHeader}>
        <span className={styles.icon}>{getIcon(service.iconId)}</span>
        <StatusDot status={healthStatus} label={`${service.name}: ${healthStatus}`} />
      </div>
      <h3 className={styles.cardTitle}>{service.name}</h3>
      <p className={styles.cardDesc}>{service.description}</p>
    </>
  );

  if (isInternalPath(service.url)) {
    return (
      <Link
        to={service.url}
        className={styles.card}
        aria-label={`Open ${service.name}`}
      >
        {body}
      </Link>
    );
  }

  return (
    <a
      href={service.url}
      target="_blank"
      rel="noopener noreferrer"
      className={styles.card}
      aria-label={`Open ${service.name}`}
    >
      {body}
    </a>
  );
}

function getIcon(iconId: string): string {
  const icons: Record<string, string> = {
    shield: '🛡️',
    chart: '📊',
    bucket: '🪣',
    notebook: '📓',
    container: '📦',
    dns: '🌐',
    lock: '🔐',
    brain: '🧠',
    docs: '📖',
  };
  return icons[iconId] || '🔧';
}
