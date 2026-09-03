import { resolveAgentFeedTransport } from '../api/agentFeedUrl';
import type { NexusConfig } from './types';

const host = import.meta.env.VITE_NEXUS_HOST || 'localhost';
const apiGatewayUrl =
  import.meta.env.VITE_API_GATEWAY_URL || `http://${host}:3100`;

/**
 * Launchpad deep-links for the GitOps lab spine.
 * Browser URLs use localhost port-forwards; in-app paths stay on the Console origin.
 * Gateway health probes use platform/api-gateway/config/services.json (cluster DNS).
 */
export const defaultConfig: NexusConfig = {
  apiGatewayUrl,
  healthPollIntervalMs: 30000,
  // Login is always gateway JWT (local). Vault :8200 is a service tile only.
  authProvider: 'local',
  authEndpoint:
    import.meta.env.VITE_AUTH_ENDPOINT || `${apiGatewayUrl}/api/v1/auth/login`,
  agentFeedTransport: resolveAgentFeedTransport('sse'),
  services: [
    {
      id: 'soc-alerts',
      name: 'Security Alerts',
      description:
        'SOC alerts via gateway — hybrid sensors (Suricata/Zeek/Falco/Tetragon) or Wazuh full-SIEM',
      category: 'security',
      url: '/alerts',
      iconId: 'shield',
    },
    {
      id: 'jupyter',
      name: 'Jupyter Workbench',
      description:
        'Purple analyst workspace — kubectl -n soc port-forward svc/nexus-workbench 8888:8888',
      category: 'workbenches',
      url: `http://${host}:8888`,
      iconId: 'notebook',
      healthEndpoint: '/api/status',
    },
    {
      id: 'artifacts',
      name: 'Artifacts',
      description: 'Object store via gateway (MinIO lab / R2 + D1 prod)',
      category: 'storage',
      url: '/artifacts',
      iconId: 'bucket',
    },
    {
      id: 'approvals',
      name: 'Approvals',
      description: 'Human gate for Athena OPAR actions and factory reviews',
      category: 'security',
      url: '/approvals',
      iconId: 'approvals',
    },
    {
      id: 'agent-feed',
      name: 'Agent Feed',
      description: 'Live Athena OPAR events (stimulation / emulation)',
      category: 'agents',
      url: '/agent-feed',
      iconId: 'feed',
    },
    {
      id: 'gateway-docs',
      name: 'API Gateway Docs',
      description:
        'OpenAPI — kubectl -n soc port-forward svc/nexus-api-gateway 3100:3100',
      category: 'infrastructure',
      url: `http://${host}:3100/docs`,
      iconId: 'docs',
    },
    {
      id: 'vault',
      name: 'Vault UI',
      description: 'Secrets — nexus-hashistack sidecar (localhost:8200)',
      category: 'infrastructure',
      url: `http://${host}:8200`,
      iconId: 'lock',
      healthEndpoint: '/v1/sys/health',
    },
  ],
};
