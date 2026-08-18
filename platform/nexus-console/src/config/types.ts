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
  authProvider: 'vault' | 'oidc';
  authEndpoint: string;
}
