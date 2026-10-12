import { Monitor, Moon, Sun } from 'lucide-react';
import useTheme from '../../app/providers/useTheme.js';
import { texts } from '../../texts/en.js';
import styles from './ThemeSwitch.module.css';

const t = texts.app.nav;
const MODES = [
  { mode: 'system', icon: Monitor, label: t.themeSystem },
  { mode: 'light', icon: Sun, label: t.themeLight },
  { mode: 'dark', icon: Moon, label: t.themeDark },
];

// Переключатель темы system / light / dark (три кнопки с aria-pressed)
export default function ThemeSwitch() {
  const { mode, setMode } = useTheme();

  return (
    <div className={styles.switch} role="group" aria-label={t.themeLabel}>
      {MODES.map((item) => (
        <button
          key={item.mode}
          type="button"
          className={[styles.option, mode === item.mode && styles.selected]
            .filter(Boolean)
            .join(' ')}
          aria-pressed={mode === item.mode}
          aria-label={item.label}
          title={item.label}
          onClick={() => setMode(item.mode)}
        >
          <item.icon size={16} aria-hidden="true" />
        </button>
      ))}
    </div>
  );
}
