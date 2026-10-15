import { ShieldAlert } from 'lucide-react';
import { texts } from '../../../texts/en.js';
import styles from './SafetyNotice.module.css';

// Предупреждение безопасности (модалка запроса и окно чата). Кнопки Report пока нет — будет в B9.
export default function SafetyNotice() {
  return (
    <p className={styles.notice}>
      <ShieldAlert size={16} aria-hidden="true" />
      <span>{texts.messages.safety}</span>
    </p>
  );
}
