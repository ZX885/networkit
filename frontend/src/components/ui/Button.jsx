import Spinner from './Spinner.jsx';
import styles from './Button.module.css';

// Кнопка. variant: primary | ghost | danger | inverse (белая на синем фоне); size: sm | md | lg.
// loading — показывает спиннер и блокирует клики (защита от двойной отправки).
export default function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  fullWidth = false,
  type = 'button',
  disabled = false,
  className = '',
  children,
  ...rest
}) {
  const classes = [
    styles.button,
    styles[variant],
    styles[size],
    fullWidth && styles.full,
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <button
      type={type}
      className={classes}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...rest}
    >
      {loading && <Spinner size="sm" />}
      {children}
    </button>
  );
}
