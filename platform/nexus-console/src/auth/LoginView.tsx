import { useState, type FormEvent } from 'react';
import { useAuth } from './AuthContext';
import styles from './LoginView.module.css';

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
    <div className="ds-cover">
      <form onSubmit={handleSubmit} className={`ds-card ds-stack ${styles.card}`}>
        <h1 className={styles.title}>⚡ Nexus Console</h1>

        {error && (
          <div className="ds-banner" data-tone="critical" role="alert">
            <span className="ds-banner-body">{error}</span>
          </div>
        )}

        <div className="ds-field">
          <label htmlFor="username">Username</label>
          <input
            id="username"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            autoFocus
            autoComplete="username"
          />
        </div>

        <div className="ds-field">
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
          />
        </div>

        <button type="submit" className="ds-btn" data-tone="primary" disabled={loading}>
          {loading ? 'Signing in…' : 'Sign in'}
        </button>
      </form>
    </div>
  );
}
