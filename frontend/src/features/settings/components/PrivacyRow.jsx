import { useId } from 'react';
import Toggle from '../../../components/ui/Toggle.jsx';
import styles from './PrivacyRow.module.css';

// Строка настройки приватности (legacy .trow): название, пояснение и переключатель
export default function PrivacyRow({ title, hint, checked, onChange, disabled = false }) {
  const titleId = useId();
  const hintId = useId();

  return (
    <div className={styles.row}>
      <div>
        <h3 id={titleId} className={styles.title}>
          {title}
        </h3>
        <p id={hintId} className={styles.hint}>
          {hint}
        </p>
      </div>
      <Toggle
        checked={checked}
        onChange={onChange}
        disabled={disabled}
        aria-labelledby={titleId}
        aria-describedby={hintId}
      />
    </div>
  );
}
