import { useAppearance } from '../../design-system/AppearanceContext';
import { APPEARANCE_OPTIONS, type Appearance } from '../../design-system/appearance';

interface GroupMeta {
  title: string;
  hint: string;
  options: Record<string, string>;
}

const LABELS: Record<keyof Appearance, GroupMeta> = {
  theme: {
    title: 'Theme',
    hint: 'Dark is the SOC default. System follows the OS setting.',
    options: { dark: 'Dark', light: 'Light', system: 'System' },
  },
  layout: {
    title: 'Navigation',
    hint: 'Where the main navigation lives. Narrow screens use the rail.',
    options: { sidebar: 'Sidebar', rail: 'Rail', topbar: 'Top bar' },
  },
  density: {
    title: 'Density',
    hint: 'Compact tightens spacing for wall displays and long tables.',
    options: { comfortable: 'Comfortable', compact: 'Compact' },
  },
  width: {
    title: 'Content width',
    hint: 'Contained caps the content at 80rem on wide monitors.',
    options: { fluid: 'Fluid', contained: 'Contained' },
  },
};

function Segmented({ name }: { name: keyof Appearance }) {
  const { appearance, setAppearance } = useAppearance();
  const meta = LABELS[name];
  const options: readonly string[] = APPEARANCE_OPTIONS[name];
  return (
    <fieldset className="ds-field" style={{ border: 0 }}>
      <legend className="ds-secondary" style={{ fontSize: 'var(--text-sm)' }}>{meta.title}</legend>
      <div className="ds-segmented" role="radiogroup" aria-label={meta.title}>
        {options.map((value) => (
          <label key={value}>
            <input
              type="radio"
              name={`appearance-${name}`}
              value={value}
              checked={appearance[name] === value}
              onChange={() => setAppearance(name, value as Appearance[typeof name])}
            />
            {meta.options[value]}
          </label>
        ))}
      </div>
      <span className="ds-hint">{meta.hint}</span>
    </fieldset>
  );
}

export function AppearanceSettings() {
  return (
    <div className="ds-grid" style={{ '--min': '16rem' } as React.CSSProperties}>
      <Segmented name="theme" />
      <Segmented name="layout" />
      <Segmented name="density" />
      <Segmented name="width" />
    </div>
  );
}
