import { useId } from 'react';
import styles from './Checkbox.module.css';

// Флажок с подписью. Подпись (children) может содержать ссылки.
// error — текст ошибки под флажком (связан через aria-describedby).
export default function Checkbox({ checked, onChange, error, children, ...rest }) {
  const errorId = useId();

  return (
    <div className={styles.wrap}>
      <label className={styles.label}>
        <input
          type="checkbox"
          className={styles.input}
          checked={checked}
          onChange={(event) => onChange(event.target.checked)}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? errorId : undefined}
          {...rest}
        />
        <span>{children}</span>
      </label>
      {error && (
        <p id={errorId} className={styles.error} role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
