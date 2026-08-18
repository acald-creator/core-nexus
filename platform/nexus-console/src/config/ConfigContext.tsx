import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { NexusConfig } from './types';
import { defaultConfig } from './defaults';
import { loadConfig } from './loader';

const ConfigContext = createContext<NexusConfig>(defaultConfig);

export function ConfigProvider({ children }: { children: ReactNode }) {
  const [config, setConfig] = useState<NexusConfig>(defaultConfig);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    loadConfig().then((cfg) => {
      setConfig(cfg);
      setLoaded(true);
    });
  }, []);

  if (!loaded) {
    return null; // or a loading spinner
  }

  return (
    <ConfigContext.Provider value={config}>
      {children}
    </ConfigContext.Provider>
  );
}

export function useConfig(): NexusConfig {
  return useContext(ConfigContext);
}
