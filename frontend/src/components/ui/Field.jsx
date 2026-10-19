import { useId, useState } from 'react';
import { ChevronDown, Eye, EyeOff } from 'lucide-react';
import { texts } from '../../texts/en.js';
import styles from './Field.module.css';

// Поле формы: подпись + input / select / textarea + подсказка и ошибка.
// as: 'input' | 'select' | 'textarea'. Для select опции передаются как children.
// Подпись связана с полем через id, ошибка и подсказка — через aria-describedby.
// revealable (только type="password"): справа в поле кнопка «Show/Hide password» (aria-pressed).
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
  revealable = false,
  type,
  describedBy: extraDescribedBy, // дополнительные id для aria-describedby (например, индикатор силы пароля)
  className = '',
  children,
  ...rest
}) {
  const autoId = useId();
  const fieldId = id || autoId;
  const hintId = `${fieldId}-hint`;
  const errorId = `${fieldId}-error`;
  const describedBy = [error && errorId, hint && hintId, extraDescribedBy]
    .filter(Boolean)
    .join(' ');
  const Control = as;
  const [revealed, setRevealed] = useState(false);
  const canReveal = revealable && as === 'input' && type === 'password';

  const control = (
    <Control
      id={fieldId}
      className={[
        styles.control,
        styles[as],
        (error || invalid) && styles.invalid,
        canReveal && styles.withReveal,
      ]
        .filter(Boolean)
        .join(' ')}
      required={required}
      type={canReveal && revealed ? 'text' : type}
      aria-invalid={error || invalid ? true : undefined}
      aria-describedby={describedBy || undefined}
      {...rest}
    >
      {children}
    </Control>
  );

  let body = control;
  if (as === 'select') {
    body = (
      <div className={styles.selectWrap}>
        {control}
        <ChevronDown className={styles.chevron} size={16} aria-hidden="true" />
      </div>
    );
  } else if (canReveal) {
    body = (
      <div className={styles.revealWrap}>
        {control}
        <button
          type="button"
          className={styles.reveal}
          aria-pressed={revealed}
          aria-label={revealed ? texts.common.hidePassword : texts.common.showPassword}
          onClick={() => setRevealed((value) => !value)}
        >
          {revealed ? (
            <EyeOff size={18} aria-hidden="true" />
          ) : (
            <Eye size={18} aria-hidden="true" />
          )}
        </button>
      </div>
    );
  }

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
      {body}
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
