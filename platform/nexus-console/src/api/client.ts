import type { NexusConfig } from '../config/types';

export class ApiError extends Error {
  status: number;
  statusText: string;
  body: unknown;

  constructor(status: number, statusText: string, body: unknown) {
    super(`API Error ${status}: ${statusText}`);
    this.name = 'ApiError';
    this.status = status;
    this.statusText = statusText;
    this.body = body;
  }
}

export interface ApiClient {
  get<T>(path: string, params?: Record<string, string>): Promise<T>;
  post<T>(path: string, body: unknown): Promise<T>;
  put<T>(path: string, body: unknown): Promise<T>;
  delete<T>(path: string): Promise<T>;
}

export function createApiClient(
  config: NexusConfig,
  getToken: () => string | null,
  onUnauthorized: () => void,
): ApiClient {
  async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const token = getToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const url = `${config.apiGatewayUrl}${path}`;
    const response = await fetch(url, { ...options, headers });

    if (response.status === 401 || response.status === 403) {
      onUnauthorized();
      throw new ApiError(response.status, response.statusText, null);
    }

    if (!response.ok) {
      const body = await response.json().catch(() => null);
      throw new ApiError(response.status, response.statusText, body);
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return response.json();
  }

  return {
    get<T>(path: string, params?: Record<string, string>): Promise<T> {
      const search = params ? '?' + new URLSearchParams(params).toString() : '';
      return request<T>(`${path}${search}`);
    },
    post<T>(path: string, body: unknown): Promise<T> {
      return request<T>(path, { method: 'POST', body: JSON.stringify(body) });
    },
    put<T>(path: string, body: unknown): Promise<T> {
      return request<T>(path, { method: 'PUT', body: JSON.stringify(body) });
    },
    delete<T>(path: string): Promise<T> {
      return request<T>(path, { method: 'DELETE' });
    },
  };
}
