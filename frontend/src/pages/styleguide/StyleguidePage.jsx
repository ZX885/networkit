import { Link } from 'react-router-dom';
import useTheme from '../../app/providers/useTheme.js';
import ChipSelect from '../../components/ui/ChipSelect.jsx';
import ButtonsSection from './ButtonsSection.jsx';
import DataSection from './DataSection.jsx';
import FeedbackSection from './FeedbackSection.jsx';
import FormsSection from './FormsSection.jsx';
import styles from './StyleguidePage.module.css';

const THEME_OPTIONS = [
  { code: 'system', label: 'System' },
  { code: 'light', label: 'Light' },
  { code: 'dark', label: 'Dark' },
];

// Страница для разработчика: все ui-компоненты и их варианты. Доступна только в dev-режиме.
export default function StyleguidePage() {
  const { mode, resolved, setMode } = useTheme();

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>Styleguide</h1>
          <p className={styles.subtitle}>
            Theme: {mode} (applied: {resolved}) · <Link to="/">Home</Link>
          </p>
        </div>
        <ChipSelect
          label="Theme"
          variant="pill"
          multiple={false}
          options={THEME_OPTIONS}
          value={[mode]}
          onChange={([next]) => setMode(next)}
        />
      </header>
      <ButtonsSection />
      <FormsSection />
      <FeedbackSection />
      <DataSection />
    </main>
  );
}
