import { useCallback, useState } from 'react';
import { DEFAULT_ARRANGEMENT, type PanelArrangement } from '../components/Layout/types';

const STORAGE_KEY = 'nexus-console:layout';

function loadFromStorage(): PanelArrangement {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      return JSON.parse(stored) as PanelArrangement;
    }
  } catch {
    // Invalid JSON — fall back to default
  }
  return DEFAULT_ARRANGEMENT;
}

export function useLayoutPersistence() {
  const [arrangement, setArrangement] = useState<PanelArrangement>(loadFromStorage);

  const saveArrangement = useCallback((arr: PanelArrangement) => {
    setArrangement(arr);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(arr));
  }, []);

  const resetToDefault = useCallback(() => {
    setArrangement(DEFAULT_ARRANGEMENT);
    localStorage.removeItem(STORAGE_KEY);
  }, []);

  return { arrangement, saveArrangement, resetToDefault };
}
