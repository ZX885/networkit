import { Link } from 'react-router-dom';
import styles from './Logo.module.css';

// Логотип: буква «N» на синем квадрате + название (legacy .nav-logo).
// to — ссылка (по умолчанию на главную); to={null} — без ссылки.
// tone="light" — белый текст (для тёмного футера).
export default function Logo({ to = '/', size = 'md', tone = 'brand' }) {
  const classes = [styles.logo, styles[size], tone === 'light' && styles.light]
    .filter(Boolean)
    .join(' ');
  const content = (
    <>
      <span className={styles.icon} aria-hidden="true">
        N
      </span>
      NetworkIt
    </>
  );

  return to ? (
    <Link to={to} className={classes}>
      {content}
    </Link>
  ) : (
    <span className={classes}>{content}</span>
  );
}
