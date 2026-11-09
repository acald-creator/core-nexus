import { describe, expect, it } from 'vitest';
import { DEFAULT_APPEARANCE, applyAppearance, sanitizeAppearance } from '../appearance';

describe('sanitizeAppearance', () => {
  it('returns defaults for garbage', () => {
    expect(sanitizeAppearance(null)).toEqual(DEFAULT_APPEARANCE);
    expect(sanitizeAppearance('x')).toEqual(DEFAULT_APPEARANCE);
    expect(sanitizeAppearance({ theme: 'neon', layout: 42 })).toEqual(DEFAULT_APPEARANCE);
  });

  it('keeps valid options and drops unknown keys', () => {
    const out = sanitizeAppearance({ theme: 'light', layout: 'topbar', bogus: true });
    expect(out).toEqual({ ...DEFAULT_APPEARANCE, theme: 'light', layout: 'topbar' });
    expect('bogus' in out).toBe(false);
  });
});

describe('applyAppearance', () => {
  it('writes every preference as a data attribute', () => {
    const el = document.createElement('div');
    applyAppearance({ theme: 'system', layout: 'rail', density: 'compact', width: 'contained' }, el);
    expect(el.dataset).toMatchObject({ theme: 'system', layout: 'rail', density: 'compact', width: 'contained' });
  });
});
