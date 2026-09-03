import type { AgentFeedTransport } from '../api/agentFeedUrl';

export type { AgentFeedTransport };

export type ServiceCategory = 'security' | 'workbenches' | 'storage' | 'infrastructure' | 'agents';

export interface ServiceEntry {
  id: string;
  name: string;
  description: string;
  category: ServiceCategory;
  url: string;
  iconId: string;
  healthEndpoint?: string;
}

export interface NexusConfig {
  apiGatewayUrl: string;
  services: ServiceEntry[];
  healthPollIntervalMs: number;
  /** Console login target. Lab uses gateway local JWT; OIDC later. Not Vault user auth. */
  authProvider: 'local' | 'oidc';
  /** Login URL — gateway `/api/v1/auth/login` for local provider. */
  authEndpoint: string;
  /** Agent Feed transport. SSE is default; websocket uses `/api/v1/agents/events/ws`. */
  agentFeedTransport: AgentFeedTransport;
}
