import { Link } from 'react-router-dom';
import { BRAND_NAME, LOGO_MARK_SRC } from '../../constants/brand.js';
import styles from './Logo.module.css';

// Логотип: знак + название (Sora, как в legacy). Единственное место, где рисуется логотип.
// size: sm | md | lg. to — ссылка (по умолчанию на главную); to={null} — без ссылки.
// tone="light" — для тёмного фона (футер): белый текст и светлый знак.
export default function Logo({ to = '/', size = 'md', tone = 'brand' }) {
  const classes = [styles.logo, styles[size], tone === 'light' && styles.light]
    .filter(Boolean)
    .join(' ');
  const content = (
    <>
      {/* Знак декоративный: рядом написано название */}
      <img className={styles.mark} src={LOGO_MARK_SRC} alt="" draggable={false} />
      {BRAND_NAME}
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
