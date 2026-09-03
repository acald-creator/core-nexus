import { describe, expect, it } from 'vitest';
import { resolveAgentFeedTransport, toGatewayWebSocketUrl } from '../agentFeedUrl';

describe('toGatewayWebSocketUrl', () => {
  it('maps http gateway origin to ws and attaches token', () => {
    expect(
      toGatewayWebSocketUrl('http://localhost:3100', '/api/v1/agents/events/ws', 'abc'),
    ).toBe('ws://localhost:3100/api/v1/agents/events/ws?token=abc');
  });

  it('maps https to wss', () => {
    expect(
      toGatewayWebSocketUrl('https://console.example', '/api/v1/agents/events/ws', 't'),
    ).toBe('wss://console.example/api/v1/agents/events/ws?token=t');
  });
});

describe('resolveAgentFeedTransport', () => {
  it('prefers env websocket over config sse', () => {
    expect(resolveAgentFeedTransport('sse', 'websocket')).toBe('websocket');
  });

  it('defaults to sse', () => {
    expect(resolveAgentFeedTransport(undefined, undefined)).toBe('sse');
  });
});
