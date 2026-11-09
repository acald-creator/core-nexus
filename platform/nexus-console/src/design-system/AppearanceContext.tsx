import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react';
import {
  applyAppearance,
  loadAppearance,
  saveAppearance,
  type Appearance,
} from './appearance';

interface AppearanceContextValue {
  appearance: Appearance;
  setAppearance: <K extends keyof Appearance>(key: K, value: Appearance[K]) => void;
}

const AppearanceContext = createContext<AppearanceContextValue | null>(null);

export function AppearanceProvider({ children }: { children: ReactNode }) {
  const [appearance, setState] = useState<Appearance>(loadAppearance);

  useEffect(() => {
    applyAppearance(appearance);
    saveAppearance(appearance);
  }, [appearance]);

  const setAppearance = useCallback<AppearanceContextValue['setAppearance']>((key, value) => {
    setState((prev) => (prev[key] === value ? prev : { ...prev, [key]: value }));
  }, []);

  return (
    <AppearanceContext.Provider value={{ appearance, setAppearance }}>
      {children}
    </AppearanceContext.Provider>
  );
}

export function useAppearance(): AppearanceContextValue {
  const ctx = useContext(AppearanceContext);
  if (!ctx) throw new Error('useAppearance must be used inside <AppearanceProvider>');
  return ctx;
}
