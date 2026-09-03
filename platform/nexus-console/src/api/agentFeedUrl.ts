export type AgentFeedTransport = 'sse' | 'websocket';

export function toGatewayWebSocketUrl(
  apiGatewayUrl: string,
  path: string,
  token: string,
): string {
  const origin = apiGatewayUrl.replace(/\/$/, '');
  const url = new URL(path, `${origin}/`);
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
  url.searchParams.set('token', token);
  return url.toString();
}

export function resolveAgentFeedTransport(
  configValue: AgentFeedTransport | undefined,
  envValue: string | undefined = import.meta.env.VITE_AGENT_FEED_TRANSPORT,
): AgentFeedTransport {
  if (envValue === 'websocket' || envValue === 'sse') {
    return envValue;
  }
  return configValue === 'websocket' ? 'websocket' : 'sse';
}
