import type { NexusConfig } from './types';

const host = import.meta.env.VITE_NEXUS_HOST || 'localhost';
const apiGatewayUrl =
  import.meta.env.VITE_API_GATEWAY_URL || `http://${host}:3100`;

export const defaultConfig: NexusConfig = {
  apiGatewayUrl,
  healthPollIntervalMs: 30000,
  // Login is always gateway JWT (local). Vault :8200 is a service tile only.
  authProvider: 'local',
  authEndpoint:
    import.meta.env.VITE_AUTH_ENDPOINT || `${apiGatewayUrl}/api/v1/auth/login`,
  services: [
    {
      id: 'wazuh-dash',
      name: 'Wazuh Dashboard',
      description: 'Security events (run SOC baseline stack separately)',
      category: 'security',
      url: `https://${host}:5601`,
      iconId: 'shield',
      healthEndpoint: '/api/status',
    },
    {
      id: 'grafana',
      name: 'Grafana',
      description: 'Platform observability and metrics (not in dev stack)',
      category: 'security',
      url: `http://${host}:3002`,
      iconId: 'chart',
      healthEndpoint: '/api/health',
    },
    {
      id: 'minio',
      name: 'MinIO Console',
      description: 'Artifact storage — PCAPs, SBOMs, skills, sessions',
      category: 'storage',
      url: `http://${host}:9001`,
      iconId: 'bucket',
      healthEndpoint: '/minio/health/live',
    },
    {
      id: 'jupyter',
      name: 'Jupyter Workbench',
      description: 'Analyst agentic workspace (not in dev stack)',
      category: 'workbenches',
      url: `http://${host}:8888`,
      iconId: 'notebook',
      healthEndpoint: '/api/status',
    },
    {
      id: 'portainer',
      name: 'Portainer',
      description: 'Container management (not in dev stack)',
      category: 'infrastructure',
      url: `https://${host}:9443`,
      iconId: 'container',
      healthEndpoint: '/api/status',
    },
    {
      id: 'pihole',
      name: 'Pi-Hole',
      description: 'Lab DNS filtering (not in dev stack)',
      category: 'infrastructure',
      url: `http://${host}:8081/admin`,
      iconId: 'dns',
    },
    {
      id: 'vault',
      name: 'Vault UI',
      description: 'Secrets (nexus-hashistack sidecar — not in this compose)',
      category: 'infrastructure',
      url: `http://${host}:8200`,
      iconId: 'lock',
      healthEndpoint: '/v1/sys/health',
    },
    {
      id: 'ai-inference',
      name: 'AI Inference API',
      description: 'AI triage enrichment and hardware detection',
      category: 'agents',
      url: `http://${host}:8000`,
      iconId: 'brain',
      healthEndpoint: '/health',
    },
  ],
};
