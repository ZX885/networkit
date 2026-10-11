import { useId } from 'react';
import styles from './FieldGroup.module.css';

// Группа связанных элементов (чипы, дата из трёх полей): fieldset + legend, подсказка и ошибка.
// legendHidden — подпись есть для скринридера, но не видна (когда её заменяет заголовок шага).
export default function FieldGroup({
  legend,
  legendHidden = false,
  required = false,
  optionalText,
  hint,
  error,
  children,
}) {
  const baseId = useId();
  const hintId = `${baseId}-hint`;
  const errorId = `${baseId}-error`;
  const describedBy = [error && errorId, hint && hintId].filter(Boolean).join(' ');

  return (
    <fieldset className={styles.group} aria-describedby={describedBy || undefined}>
      <legend
        className={[styles.legend, legendHidden && 'visually-hidden'].filter(Boolean).join(' ')}
      >
        {legend}
        {required && <span aria-hidden="true"> *</span>}
        {optionalText && <span className={styles.optional}> {optionalText}</span>}
      </legend>
      {children}
      {hint && (
        <p id={hintId} className={styles.hint}>
          {hint}
        </p>
      )}
      {error && (
        <p id={errorId} className={styles.error} role="alert">
          {error}
        </p>
      )}
    </fieldset>
  );
}
