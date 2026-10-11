import { createContext } from 'react';

// Значение: { mode: 'system' | 'light' | 'dark', resolved: 'light' | 'dark', setMode }
export const ThemeContext = createContext(null);
