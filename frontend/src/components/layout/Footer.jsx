import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Globe } from 'lucide-react';
import Logo from '../ui/Logo.jsx';
import { texts } from '../../texts/en.js';
import styles from './Footer.module.css';

// Подвал лендинга (legacy footer): описание и три колонки ссылок.
// About / Blog / Careers в legacy не были ссылками — показываем обычным текстом.
export default function Footer() {
  const t = texts.footer;
  const [year] = useState(() => new Date().getFullYear());

  return (
    <footer className={styles.footer}>
      <div className={styles.inner}>
        <div className={styles.top}>
          <div>
            <div className={styles.logo}>
              <Logo to={null} size="sm" tone="light" />
            </div>
            <p className={styles.description}>{t.description}</p>
          </div>
          <div>
            <h4 className={styles.heading}>{t.platform}</h4>
            <Link to="/register" className={styles.item}>
              {t.signUp}
            </Link>
            <Link to="/login" className={styles.item}>
              {t.logIn}
            </Link>
          </div>
          <div>
            <h4 className={styles.heading}>{t.company}</h4>
            <span className={styles.item}>{t.about}</span>
            <span className={styles.item}>{t.blog}</span>
            <span className={styles.item}>{t.careers}</span>
          </div>
          <div>
            <h4 className={styles.heading}>{t.legal}</h4>
            <Link to="/privacy" className={styles.item}>
              {t.privacy}
            </Link>
            <Link to="/terms" className={styles.item}>
              {t.terms}
            </Link>
          </div>
        </div>
        <div className={styles.bottom}>
          <p>{t.copyright(year)}</p>
          <p>
            {t.tagline} <Globe size={14} aria-hidden="true" />
          </p>
        </div>
      </div>
    </footer>
  );
}
