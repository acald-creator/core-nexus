/**
 * Style guide page (design-system.html). Renders swatches and scales from the
 * live custom properties and wires the appearance controls.
 */
import '../index.css';
import './preview.css';
import {
  APPEARANCE_OPTIONS,
  applyAppearance,
  loadAppearance,
  saveAppearance,
  type Appearance,
} from '../appearance';

let appearance: Appearance = loadAppearance();
applyAppearance(appearance);

// ---- controls ----
for (const group of document.querySelectorAll<HTMLElement>('.ds-segmented[data-pref]')) {
  const key = group.dataset.pref as keyof Appearance;
  for (const input of group.querySelectorAll<HTMLInputElement>('input')) {
    input.checked = appearance[key] === input.value;
    input.addEventListener('change', () => {
      if (!(APPEARANCE_OPTIONS[key] as readonly string[]).includes(input.value)) return;
      appearance = { ...appearance, [key]: input.value };
      applyAppearance(appearance);
      saveAppearance(appearance);
      requestAnimationFrame(renderSwatches);
    });
  }
}

// ---- swatches: read the computed value so light/dark is reflected ----
const probe = document.createElement('span');
probe.style.display = 'none';
document.body.append(probe);

function resolve(token: string): string {
  probe.style.color = `var(--${token})`;
  return getComputedStyle(probe).color;
}

function swatch(token: string): HTMLElement {
  const el = document.createElement('div');
  el.className = 'sg-swatch';
  el.innerHTML = `<div class="sg-chip" style="background: var(--${token})"></div>
    <div class="sg-swatch-name">--${token}</div>
    <div class="sg-swatch-value ds-mono"></div>`;
  return el;
}

function renderSwatches() {
  for (const grid of document.querySelectorAll<HTMLElement>('.sg-swatches')) {
    const tokens = (grid.dataset.swatches ?? '').split(/\s+/).filter(Boolean);
    if (grid.childElementCount !== tokens.length) {
      grid.replaceChildren(...tokens.map(swatch));
    }
    grid.querySelectorAll<HTMLElement>('.sg-swatch').forEach((el, i) => {
      const v = el.querySelector('.sg-swatch-value');
      if (v) v.textContent = resolve(tokens[i]);
    });
  }
}
renderSwatches();
matchMedia('(prefers-color-scheme: dark)').addEventListener('change', renderSwatches);

// ---- primitive scales ----
const STEPS = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950];
const scales = document.getElementById('scales');
if (scales) {
  for (const hue of ['neutral', 'green', 'red', 'orange', 'amber', 'blue', 'brand']) {
    const row = document.createElement('div');
    row.className = 'sg-scale';
    row.innerHTML = `<span class="sg-scale-name ds-mono">${hue}</span>` +
      STEPS.map((s) => `<i style="background: var(--${hue}-${s})" title="--${hue}-${s}"></i>`).join('');
    scales.append(row);
  }
}

// ---- space ramp ----
const ramp = document.getElementById('space-ramp');
if (ramp) {
  ramp.innerHTML = '<h3 class="ds-eyebrow">Space · scales with density</h3>' +
    ['1', '2', '3', '4', '6', '8', '12', '16']
      .map((n) => `<div class="sg-space"><span class="ds-mono">--space-${n}</span><i style="inline-size: var(--space-${n})"></i></div>`)
      .join('');
}
