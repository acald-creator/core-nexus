import { useAuth } from '../auth/AuthContext';
import { useConfig } from '../config/ConfigContext';
import { HealthSummaryBar } from '../components/panels/Health/HealthSummaryBar';
import { StatusDot } from '../components/common/StatusDot';
import { useHealthMonitor } from '../hooks/useHealthMonitor';
import { formatUnixSeconds, summarizeToken } from '../utils/tokenInfo';
import styles from './SettingsPage.module.css';

const DEV_BYPASS = import.meta.env.VITE_DEV_AUTH_BYPASS === 'true';

function formatLastChecked(ms?: number): string {
  if (!ms) return '—';
  return new Date(ms).toISOString();
}

export default function SettingsPage() {
  const config = useConfig();
  const { token, isAuthenticated, logout } = useAuth();
  const { summary, statusMap } = useHealthMonitor();
  const tokenInfo = summarizeToken(token);

  return (
    <div className={styles.page}>
      <section className={styles.section} aria-labelledby="settings-config">
        <h2 id="settings-config" className={styles.heading}>Configuration</h2>
        <p className={styles.lede}>
          Runtime Console config. Login uses the API Gateway (local JWT). Vault
          is a service tile only (nexus-hashistack). Secrets stay on the Gateway.
        </p>
        <dl className={styles.grid}>
          <dt>API Gateway</dt>
          <dd>{config.apiGatewayUrl}</dd>
          <dt>Auth provider</dt>
          <dd>{config.authProvider}</dd>
          <dt>Auth endpoint</dt>
          <dd>{config.authEndpoint}</dd>
          <dt>Health poll</dt>
          <dd>{config.healthPollIntervalMs} ms</dd>
          <dt>Agent feed transport</dt>
          <dd>{config.agentFeedTransport}</dd>
          <dt>Dev auth bypass</dt>
          <dd>{DEV_BYPASS ? 'enabled' : 'off'}</dd>
          <dt>Services in config</dt>
          <dd>{config.services.length}</dd>
        </dl>
      </section>

      <section className={styles.section} aria-labelledby="settings-token">
        <h2 id="settings-token" className={styles.heading}>Session token</h2>
        <p className={styles.lede}>
          Claims from the current session. The raw token is never printed here.
        </p>
        <dl className={styles.grid}>
          <dt>Authenticated</dt>
          <dd>{isAuthenticated ? 'yes' : 'no'}</dd>
          <dt>Token kind</dt>
          <dd><span className={styles.kind}>{tokenInfo.kind}</span></dd>
          <dt>Subject</dt>
          <dd>{tokenInfo.subject ?? '—'}</dd>
          <dt>Role</dt>
          <dd>{tokenInfo.role ?? '—'}</dd>
          <dt>Issued</dt>
          <dd>{formatUnixSeconds(tokenInfo.issuedAt)}</dd>
          <dt>Expires</dt>
          <dd className={tokenInfo.expired ? styles.expired : undefined}>
            {formatUnixSeconds(tokenInfo.expiresAt)}
            {tokenInfo.expired ? ' (expired)' : ''}
          </dd>
        </dl>
        {isAuthenticated && !DEV_BYPASS && (
          <div className={styles.actions}>
            <button type="button" className={styles.logout} onClick={logout}>
              Sign out
            </button>
          </div>
        )}
      </section>

      <section className={styles.section} aria-labelledby="settings-services">
        <h2 id="settings-services" className={styles.heading}>Service status</h2>
        <p className={styles.lede}>
          Health is probed through the Gateway <code className={styles.mono}>/api/v1/health/:id</code>.
          Offline can mean the Gateway is down, not only the upstream service.
        </p>
        <HealthSummaryBar summary={summary} />
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Service</th>
                <th>Status</th>
                <th>Latency</th>
                <th>Last checked</th>
                <th>URL</th>
              </tr>
            </thead>
            <tbody>
              {config.services.map((service) => {
                const health = statusMap.get(service.id);
                const status = health?.status ?? 'unknown';
                return (
                  <tr key={service.id}>
                    <td>
                      <div className={styles.serviceName}>
                        <span>{service.name}</span>
                        <span className={styles.serviceId}>{service.id}</span>
                      </div>
                    </td>
                    <td>
                      <span className={styles.statusCell}>
                        <StatusDot status={status} />
                        {status}
                      </span>
                    </td>
                    <td className={styles.mono}>
                      {health?.responseTimeMs !== undefined
                        ? `${health.responseTimeMs.toFixed(0)} ms`
                        : '—'}
                    </td>
                    <td className={styles.mono}>{formatLastChecked(health?.lastChecked)}</td>
                    <td className={styles.mono}>{service.url}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
