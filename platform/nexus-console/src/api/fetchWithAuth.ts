/**
 * Authenticated fetch wrapper. Reads token from the auth context store
 * and injects Authorization header. Used by all hooks.
 */

let _getToken: () => string | null = () => null;

/** Called by AuthProvider to register the token getter. */
export function registerTokenGetter(getter: () => string | null) {
  _getToken = getter;
}

/** Fetch with auth header injected. */
export async function fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
  const token = _getToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  return fetch(url, { ...options, headers });
}
