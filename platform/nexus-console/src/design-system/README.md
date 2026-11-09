# Nexus Console design system

Tokens, layout primitives and component classes for the console. Plain CSS, no
build step beyond Vite. Live style guide: run `npm run dev` and open
`/design-system.html`.

## Files

| File | Layer | What it holds |
|---|---|---|
| `tokens/primitives.css` | `ds.tokens` | Seven OKLCH tonal scales on one lightness ladder |
| `tokens/semantic.css` | `ds.tokens` | Role tokens (`--bg-*`, `--ink*`, `--accent*`, `--status-*`, `--health-*`, `--phase-*`), themed with `light-dark()`; legacy `--color-*` aliases |
| `tokens/scale.css` | `ds.tokens` | Space, radius, type, motion, sizing; density and layout switches |
| `base.css` | `ds.base` | Reset and element defaults |
| `layout.css` | `ds.layout` | `.ds-stack`, `.ds-cluster`, `.ds-grid`, `.ds-split`, `.ds-center`, `.ds-cover`, `.ds-panels`, `.ds-shell` |
| `components.css` | `ds.components`, `ds.utilities` | `.ds-card`, `.ds-btn`, `.ds-badge`, `.ds-tag`, `.ds-dot`, `.ds-severity`, `.ds-banner`, `.ds-field`, `.ds-tabs`, `.ds-table`, `.ds-detail`, `.ds-kv`, `.ds-empty`, `.ds-spinner`, `.ds-segmented` |
| `index.css` | | Declares layer order, imports the rest. The only file to import |
| `appearance.ts`, `AppearanceContext.tsx` | | Theme / layout / density / width preference, persisted, applied as `data-*` on `<html>` |
| `pairs.json` | | The accessibility contract: every text/ground pair, per theme |

Cascade: `ds.tokens → ds.base → ds.layout → ds.components → ds.utilities`.
CSS modules are unlayered, so a module always wins over the system. Compose
first, override second.

## Colour

Authored in `oklch()`. Lightness carries contrast, so each role has a fixed
lightness in each theme and the hue is a variable (`--hue-brand`, `--hue-neutral`
…). Neutrals are tinted toward the brand ground's cool slate (hue 250, chroma
0.018) so grey never looks dead beside the green.

| Role | Dark L | Light L | Notes |
|---|---|---|---|
| `--bg-inset / ground / surface / raised / overlay` | 0.14 / 0.17 / 0.21 / 0.26 / 0.30 | 0.935 / 0.965 / 0.99 / 0.995 / 0.995 | Dark elevates by lightness; light by shadow |
| `--ink / ink-2 / ink-muted / ink-faint` | 0.95 / 0.78 / 0.68 / 0.54 | 0.21 / 0.40 / 0.52 / 0.64 | `ink-faint` is placeholder-only (non-text 3:1) |
| `--accent` | 0.78, C 0.155 | 0.50, C 0.115 | Dark accent carries `--ink-on-accent` (dark); light accent carries near-white |
| `--status-critical / high / medium / low` | 0.68 / 0.78 / 0.88 / 0.66 | 0.44 / 0.555 / 0.54 / 0.47 | All pass 4.5:1 as text on every ground |
| `--phase-plan` | 0.82, violet 309 | 0.52 | Violet is the split-complement of the brand hue |

Derived values come from the base token, never a second literal:
`--accent-wash: color-mix(in oklch, var(--accent) 14%, transparent)`.
A `(color-gamut: p3)` block adds chroma to the accent where the screen allows.

### Themes

`<html data-theme="dark|light|system">`. Dark is the default (`color-scheme: dark`
on `:root`), so nothing changes for existing users. `system` sets
`color-scheme: light dark` and `light-dark()` does the rest. Forced-colours mode
swaps edges to `CanvasText` and the focus ring to `Highlight`.

### Accessibility contract

```bash
node ~/.claude/skills/color-accessibility/scripts/audit-pairs.mjs src/design-system/pairs.json
```

Both themes pass WCAG 2.2 AA for every declared pair. Colour-vision-deficiency
checks flag green/orange and blue/violet as confusable, so those states carry a
second cue: health dots differ in **shape** (● healthy, ▲ degraded, ◆ offline,
◌ unknown) and severities and OPAR phases are always printed as words.
`pairs.json` lists these under `knownConfusable`.

## Layout options

Set on `<html>` by the Appearance section of Settings (or by hand).

| Attribute | Values | Effect |
|---|---|---|
| `data-layout` | `sidebar` (default), `rail`, `topbar` | `.ds-shell` grid and the Sidebar's shape. Under 48rem the sidebar becomes a rail on its own |
| `data-width` | `fluid` (default), `contained` | `.ds-panels` caps at `--content-max` (80rem) and centres |
| `data-density` | `comfortable` (default), `compact` | `--space-unit` 4px → 3.2px, shorter controls, tighter leading |

`.ds-panels` goes two-up when **its container** is ≥ 64rem (`@container`), so
the rail/sidebar choice and the contained width both affect it correctly.
A panel spans both columns with `.ds-span` or its own `grid-column: 1 / -1`.

## Conventions

- Logical properties (`margin-inline-start`, `inset-block-start`), `dvh` not `vh`,
  range media queries (`(width < 48rem)`), listed transitions never `all`.
- Variants are data attributes: `<button class="ds-btn" data-tone="danger" data-size="sm">`.
- Primitives take knobs as custom properties: `<div class="ds-grid" style="--min: 18rem">`.
- Motion durations collapse to 0 under `prefers-reduced-motion`.
- New colour literal in a module? Stop. Add a role token or derive with `color-mix()`.

## Audits

```bash
node ~/.claude/skills/modern-css/scripts/audit-css.mjs src
node ~/.claude/skills/color-theory/scripts/audit-colors.mjs src
node ~/.claude/skills/color-accessibility/scripts/audit-pairs.mjs src/design-system/pairs.json
```

## Migration

The legacy `--color-*`, `--space-*`, `--font-size-*`, `--border-radius*` and
`--transition-*` names still resolve (aliases at the bottom of `semantic.css` and
`scale.css`). Existing CSS modules keep working; when you touch one, move it to
the role tokens and delete the alias once nothing reads it.
