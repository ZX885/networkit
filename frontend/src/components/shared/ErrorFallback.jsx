import { texts } from '../../texts/en.js';
import Button from '../ui/Button.jsx';
import styles from './ErrorFallback.module.css';

const t = texts.app;

// Страница ошибки рендера. repeated — ошибка повторилась меньше чем через минуту: добавляем подсказку.
export default function ErrorFallback({ repeated, inLayout }) {
  return (
    <div className={[styles.box, !inLayout && styles.full].filter(Boolean).join(' ')} role="alert">
      <h1 className={styles.title}>{t.errorTitle}</h1>
      <p className={styles.text}>{t.errorText}</p>
      {repeated && <p className={styles.text}>{t.supportHint}</p>}
      <Button onClick={() => window.location.reload()}>{t.reload}</Button>
    </div>
  );
}
