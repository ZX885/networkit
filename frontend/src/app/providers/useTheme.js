import { useContext } from 'react';
import { ThemeContext } from './ThemeContext.js';

// Доступ к теме: const { mode, resolved, setMode } = useTheme();
export default function useTheme() {
  const value = useContext(ThemeContext);
  if (!value) throw new Error('useTheme must be used inside ThemeProvider');
  return value;
}
