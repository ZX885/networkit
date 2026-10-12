import { Link } from 'react-router-dom';
import styles from './Button.module.css';

// Ссылка (react-router) с внешним видом кнопки: те же variant / size, что у Button.
export default function ButtonLink({
  to,
  variant = 'primary',
  size = 'md',
  fullWidth = false,
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
    <Link to={to} className={classes} {...rest}>
      {children}
    </Link>
  );
}
