import { useEffect, useMemo, useState } from 'react';
import { readStorage, writeStorage } from '../../lib/storage.js';
import { ThemeContext } from './ThemeContext.js';

// Тот же ключ использует inline-скрипт в index.html
const STORAGE_KEY = 'nk_theme';
const MODES = ['system', 'light', 'dark'];

function getSavedMode() {
  const saved = readStorage(STORAGE_KEY);
  return MODES.includes(saved) ? saved : 'system';
}

function systemPrefersDark() {
  return window.matchMedia('(prefers-color-scheme: dark)').matches;
}

// Хранит выбор темы и всегда выставляет на <html> конкретный data-theme (light или dark).
export default function ThemeProvider({ children }) {
  const [mode, setMode] = useState(getSavedMode);
  const [systemDark, setSystemDark] = useState(systemPrefersDark);

  // Следим за сменой системной темы (важно для режима system)
  useEffect(() => {
    const query = window.matchMedia('(prefers-color-scheme: dark)');
    const onChange = (event) => setSystemDark(event.matches);
    query.addEventListener('change', onChange);
    return () => query.removeEventListener('change', onChange);
  }, []);

  const resolved = mode === 'system' ? (systemDark ? 'dark' : 'light') : mode;

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', resolved);
  }, [resolved]);

  const value = useMemo(
    () => ({
      mode,
      resolved,
      setMode: (next) => {
        setMode(next);
        writeStorage(STORAGE_KEY, next);
      },
    }),
    [mode, resolved],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}
