export const ENDPOINTS = {
  auth: {
    login: '/api/v1/auth/login',
    refresh: '/api/v1/auth/refresh',
  },
  services: '/api/v1/services',
  health: (serviceId: string) => `/api/v1/health/${serviceId}`,
  agents: {
    events: '/api/v1/agents/events',
    eventsWs: '/api/v1/agents/events/ws',
    sessions: '/api/v1/agents/sessions',
  },
  alerts: '/api/v1/alerts',
  alertTriage: (id: string) => `/api/v1/alerts/${id}/triage`,
  approvals: '/api/v1/approvals',
  approvalDecision: (id: string) => `/api/v1/approvals/${id}/decision`,
  skills: '/api/v1/skills',
  skillContent: (id: string) => `/api/v1/skills/${id}/content`,
  artifacts: '/api/v1/artifacts',
  artifactDownload: (key: string) => `/api/v1/artifacts/${encodeURIComponent(key)}/download-url`,
} as const;
