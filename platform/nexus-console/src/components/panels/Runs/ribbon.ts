import type { RunWindow } from './correlation';

export interface RibbonMark {
  id: string;
  /** Left offset across the run window, 0–100, clamped. */
  pct: number;
  timestamp: string;
}

/**
 * Place timestamped items across the run window as left-offset percentages.
 *
 * The window is the same padded span used for correlation, so red acts and
 * blue alerts share one axis and line up by wall-clock time. Positions are
 * clamped to [0, 100] so a buffer-edge item can't overflow the track.
 */
export function placeMarks<T extends { id: string; timestamp: string }>(
  items: T[],
  window: RunWindow | null,
): RibbonMark[] {
  if (!window) return [];
  const span = window.end - window.start;
  if (span <= 0) return [];
  return items.map((it) => {
    const t = new Date(it.timestamp).getTime();
    const pct = ((t - window.start) / span) * 100;
    return { id: it.id, pct: Math.max(0, Math.min(100, pct)), timestamp: it.timestamp };
  });
}
