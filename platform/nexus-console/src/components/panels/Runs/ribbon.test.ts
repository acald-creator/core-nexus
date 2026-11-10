import { describe, expect, it } from 'vitest';
import { placeMarks } from './ribbon';

const win = { start: 0, end: 100_000 };

describe('placeMarks', () => {
  it('positions items by their offset into the window', () => {
    const marks = placeMarks(
      [
        { id: 'a', timestamp: new Date(0).toISOString() },
        { id: 'b', timestamp: new Date(50_000).toISOString() },
        { id: 'c', timestamp: new Date(100_000).toISOString() },
      ],
      win,
    );
    expect(marks.map((m) => m.pct)).toEqual([0, 50, 100]);
  });

  it('clamps items outside the window to the track edges', () => {
    const marks = placeMarks(
      [
        { id: 'early', timestamp: new Date(-50_000).toISOString() },
        { id: 'late', timestamp: new Date(200_000).toISOString() },
      ],
      win,
    );
    expect(marks.map((m) => m.pct)).toEqual([0, 100]);
  });

  it('returns nothing for a null or zero-span window', () => {
    expect(placeMarks([{ id: 'a', timestamp: new Date(0).toISOString() }], null)).toEqual([]);
    expect(
      placeMarks([{ id: 'a', timestamp: new Date(0).toISOString() }], { start: 5, end: 5 }),
    ).toEqual([]);
  });
});
