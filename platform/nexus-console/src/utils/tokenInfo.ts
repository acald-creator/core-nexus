export const DEV_PLACEHOLDER_TOKEN = 'dev-bypass-token';

export type TokenKind = 'missing' | 'placeholder' | 'jwt' | 'opaque';

export interface JwtClaims {
  sub?: string;
  role?: string;
  iat?: number;
  exp?: number;
}

export interface TokenInfo {
  kind: TokenKind;
  present: boolean;
  subject?: string;
  role?: string;
  issuedAt?: number;
  expiresAt?: number;
  expired?: boolean;
}

function base64UrlDecode(segment: string): string {
  const normalized = segment.replace(/-/g, '+').replace(/_/g, '/');
  const pad = normalized.length % 4 === 0 ? '' : '='.repeat(4 - (normalized.length % 4));
  return atob(normalized + pad);
}

export function decodeJwtClaims(token: string): JwtClaims | null {
  const parts = token.split('.');
  if (parts.length !== 3 || !parts[1]) return null;
  try {
    const parsed: unknown = JSON.parse(base64UrlDecode(parts[1]));
    if (!parsed || typeof parsed !== 'object') return null;
    const raw = parsed as Record<string, unknown>;
    const claims: JwtClaims = {};
    if (typeof raw.sub === 'string') claims.sub = raw.sub;
    if (typeof raw.role === 'string') claims.role = raw.role;
    if (typeof raw.iat === 'number' && Number.isFinite(raw.iat)) claims.iat = raw.iat;
    if (typeof raw.exp === 'number' && Number.isFinite(raw.exp)) claims.exp = raw.exp;
    return claims;
  } catch {
    return null;
  }
}

export function summarizeToken(token: string | null | undefined, nowMs: number = Date.now()): TokenInfo {
  if (!token) {
    return { kind: 'missing', present: false };
  }
  if (token === DEV_PLACEHOLDER_TOKEN) {
    return { kind: 'placeholder', present: true };
  }

  const claims = decodeJwtClaims(token);
  if (!claims) {
    return { kind: 'opaque', present: true };
  }

  const info: TokenInfo = {
    kind: 'jwt',
    present: true,
    subject: claims.sub,
    role: claims.role,
    issuedAt: claims.iat,
    expiresAt: claims.exp,
  };
  if (claims.exp !== undefined) {
    info.expired = claims.exp * 1000 <= nowMs;
  }
  return info;
}

export function formatUnixSeconds(seconds?: number): string {
  if (seconds === undefined) return '—';
  return new Date(seconds * 1000).toISOString();
}
