/**
 * Appearance preferences: theme, shell layout, density, content width.
 * Applied as data attributes on <html>; the CSS tokens react to them.
 * Persisted in localStorage. Framework-free so main.tsx can apply the saved
 * choice before React mounts (no flash of the wrong theme).
 */
export type Theme = 'dark' | 'light' | 'system';
export type Layout = 'sidebar' | 'rail' | 'topbar';
export type Density = 'comfortable' | 'compact';
export type Width = 'fluid' | 'contained';

export interface Appearance {
  theme: Theme;
  layout: Layout;
  density: Density;
  width: Width;
}

export const DEFAULT_APPEARANCE: Appearance = {
  theme: 'dark',
  layout: 'sidebar',
  density: 'comfortable',
  width: 'fluid',
};

export const APPEARANCE_OPTIONS = {
  theme: ['dark', 'light', 'system'],
  layout: ['sidebar', 'rail', 'topbar'],
  density: ['comfortable', 'compact'],
  width: ['fluid', 'contained'],
} as const satisfies { [K in keyof Appearance]: readonly Appearance[K][] };

export const STORAGE_KEY = 'nexus-console:appearance';

function isOption<K extends keyof Appearance>(key: K, value: unknown): value is Appearance[K] {
  return (APPEARANCE_OPTIONS[key] as readonly string[]).includes(value as string);
}

/** Parse a stored value, dropping unknown keys and invalid options. */
export function sanitizeAppearance(raw: unknown): Appearance {
  const out: Appearance = { ...DEFAULT_APPEARANCE };
  if (typeof raw !== 'object' || raw === null) return out;
  const r = raw as Record<string, unknown>;
  if (isOption('theme', r.theme)) out.theme = r.theme;
  if (isOption('layout', r.layout)) out.layout = r.layout;
  if (isOption('density', r.density)) out.density = r.density;
  if (isOption('width', r.width)) out.width = r.width;
  return out;
}

export function loadAppearance(): Appearance {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? sanitizeAppearance(JSON.parse(stored)) : DEFAULT_APPEARANCE;
  } catch {
    return DEFAULT_APPEARANCE;
  }
}

export function saveAppearance(a: Appearance): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(a));
  } catch {
    // Storage unavailable (private mode, quota). The in-memory state still applies.
  }
}

export function applyAppearance(a: Appearance, root: HTMLElement = document.documentElement): void {
  root.dataset.theme = a.theme;
  root.dataset.layout = a.layout;
  root.dataset.density = a.density;
  root.dataset.width = a.width;
}
