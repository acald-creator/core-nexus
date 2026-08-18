import { useState, type FormEvent } from 'react';
import { useAuth } from './AuthContext';

export function LoginView() {
  const { login } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await login({ username, password });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100vh',
      background: 'var(--color-bg-primary)',
    }}>
      <form onSubmit={handleSubmit} style={{
        background: 'var(--color-bg-secondary)',
        padding: 'var(--space-8)',
        borderRadius: 'var(--border-radius)',
        border: '1px solid var(--color-border)',
        width: '360px',
      }}>
        <h1 style={{ marginBottom: 'var(--space-6)', color: 'var(--color-accent)' }}>
          ⚡ Nexus Console
        </h1>

        {error && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid var(--color-critical)',
            borderRadius: 'var(--border-radius-sm)',
            padding: 'var(--space-3)',
            marginBottom: 'var(--space-4)',
            color: 'var(--color-critical)',
            fontSize: 'var(--font-size-sm)',
          }}>
            {error}
          </div>
        )}

        <div style={{ marginBottom: 'var(--space-4)' }}>
          <label htmlFor="username" style={{ display: 'block', marginBottom: 'var(--space-1)', fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
            Username
          </label>
          <input
            id="username"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            autoFocus
            style={{ width: '100%' }}
          />
        </div>

        <div style={{ marginBottom: 'var(--space-6)' }}>
          <label htmlFor="password" style={{ display: 'block', marginBottom: 'var(--space-1)', fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
            Password
          </label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            style={{ width: '100%' }}
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          style={{
            width: '100%',
            padding: 'var(--space-3)',
            background: 'var(--color-accent)',
            color: 'var(--color-text-inverse)',
            borderRadius: 'var(--border-radius-sm)',
            fontWeight: 600,
            opacity: loading ? 0.7 : 1,
          }}
        >
          {loading ? 'Signing in...' : 'Sign In'}
        </button>
      </form>
    </div>
  );
}
