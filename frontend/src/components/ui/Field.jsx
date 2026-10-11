import { useId } from 'react';
import { ChevronDown } from 'lucide-react';
import styles from './Field.module.css';

// Поле формы: подпись + input / select / textarea + подсказка и ошибка.
// as: 'input' | 'select' | 'textarea'. Для select опции передаются как children.
// Подпись связана с полем через id, ошибка и подсказка — через aria-describedby.
export default function Field({
  label,
  as = 'input',
  id,
  hint,
  error,
  invalid = false, // подсветить поле красным без текста ошибки (ошибка показана рядом)
  required = false,
  optionalText,
  labelHidden = false, // подпись есть для скринридера, но не видна (например, День/Месяц/Год)
  className = '',
  children,
  ...rest
}) {
  const autoId = useId();
  const fieldId = id || autoId;
  const hintId = `${fieldId}-hint`;
  const errorId = `${fieldId}-error`;
  const describedBy = [error && errorId, hint && hintId].filter(Boolean).join(' ');
  const Control = as;

  const control = (
    <Control
      id={fieldId}
      className={[styles.control, styles[as], (error || invalid) && styles.invalid]
        .filter(Boolean)
        .join(' ')}
      required={required}
      aria-invalid={error || invalid ? true : undefined}
      aria-describedby={describedBy || undefined}
      {...rest}
    >
      {children}
    </Control>
  );

  return (
    <div className={[styles.field, className].filter(Boolean).join(' ')}>
      <label
        className={[styles.label, labelHidden && 'visually-hidden'].filter(Boolean).join(' ')}
        htmlFor={fieldId}
      >
        {label}
        {required && <span aria-hidden="true"> *</span>}
        {optionalText && <span className={styles.optional}> {optionalText}</span>}
      </label>
      {as === 'select' ? (
        <div className={styles.selectWrap}>
          {control}
          <ChevronDown className={styles.chevron} size={16} aria-hidden="true" />
        </div>
      ) : (
        control
      )}
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
    </div>
  );
}
