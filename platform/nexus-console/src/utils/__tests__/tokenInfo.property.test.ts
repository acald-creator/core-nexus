import { describe, expect, it } from 'vitest';
import fc from 'fast-check';
import {
  DEV_PLACEHOLDER_TOKEN,
  decodeJwtClaims,
  summarizeToken,
} from '../tokenInfo';

function base64UrlEncode(value: string): string {
  return btoa(value).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
}

function jwtFromClaims(claims: Record<string, unknown>): string {
  const header = base64UrlEncode(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const payload = base64UrlEncode(JSON.stringify(claims));
  return `${header}.${payload}.signature`;
}

describe('Property 17: Settings token summary never leaks the raw token', () => {
  it('summarizeToken JSON never contains the raw token string', () => {
    fc.assert(
      fc.property(
        fc.oneof(
          fc.constant(null),
          fc.constant(DEV_PLACEHOLDER_TOKEN),
          fc.string({ minLength: 8, maxLength: 80 }),
          fc.record({
            sub: fc.string({ minLength: 1, maxLength: 24 }),
            role: fc.constantFrom('analyst', 'admin', 'viewer'),
            iat: fc.integer({ min: 1_700_000_000, max: 1_900_000_000 }),
            exp: fc.integer({ min: 1_700_000_000, max: 1_900_000_000 }),
          }).map(jwtFromClaims),
        ),
        (token) => {
          const summary = JSON.stringify(summarizeToken(token));
          if (token && token.length >= 8 && token !== DEV_PLACEHOLDER_TOKEN) {
            expect(summary).not.toContain(token);
          }
          expect(summary).not.toMatch(/eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]+\./);
        },
      ),
    );
  });

  it('JWT claims round-trip into the summary fields', () => {
    fc.assert(
      fc.property(
        fc.record({
          sub: fc.stringMatching(/^[A-Za-z0-9_-]{1,24}$/),
          role: fc.constantFrom('analyst', 'admin', 'viewer'),
          iat: fc.integer({ min: 1_700_000_000, max: 1_800_000_000 }),
          exp: fc.integer({ min: 1_800_000_001, max: 1_900_000_000 }),
        }),
        (claims) => {
          const token = jwtFromClaims(claims);
          expect(decodeJwtClaims(token)).toEqual(claims);
          const info = summarizeToken(token, claims.iat * 1000);
          expect(info.kind).toBe('jwt');
          expect(info.subject).toBe(claims.sub);
          expect(info.role).toBe(claims.role);
          expect(info.issuedAt).toBe(claims.iat);
          expect(info.expiresAt).toBe(claims.exp);
          expect(info.expired).toBe(false);
        },
      ),
    );
  });

  it('decodeJwtClaims never throws on arbitrary strings', () => {
    fc.assert(
      fc.property(fc.string(), (token) => {
        expect(() => decodeJwtClaims(token)).not.toThrow();
      }),
    );
  });
});
