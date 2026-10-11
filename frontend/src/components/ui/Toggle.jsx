import styles from './Toggle.module.css';

// Переключатель (role=switch). Название для скринридера — через label
// (или aria-labelledby, если подпись есть на странице).
export default function Toggle({ checked, onChange, label, disabled = false, ...rest }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      disabled={disabled}
      className={[styles.toggle, checked && styles.on].filter(Boolean).join(' ')}
      onClick={() => onChange(!checked)}
      {...rest}
    />
  );
}
