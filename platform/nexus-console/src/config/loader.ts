import { NexusConfig } from './types';
import { defaultConfig } from './defaults';

export async function loadConfig(): Promise<NexusConfig> {
  try {
    const response = await fetch('/config.json');
    if (!response.ok) {
      return defaultConfig;
    }
    const runtimeConfig: Partial<NexusConfig> = await response.json();
    return mergeConfig(defaultConfig, runtimeConfig);
  } catch {
    // config.json not found or parse error — use defaults silently
    return defaultConfig;
  }
}

export function mergeConfig(
  base: NexusConfig,
  override: Partial<NexusConfig>
): NexusConfig {
  return {
    ...base,
    ...override,
    services: override.services ?? base.services,
  };
}
