import { Link } from 'react-router-dom';
import { texts } from '../texts/en.js';
import styles from './StubPage.module.css';

// Заглушка для страниц, которых ещё нет (Terms, Privacy). title — заголовок страницы.
export default function ComingSoonPage({ title }) {
  const t = texts.legal;

  return (
    <main className={styles.page}>
      <h1 className={styles.title}>{title}</h1>
      <p className={styles.text}>
        {t.comingSoon}. {t.text}
      </p>
      <Link to="/">{t.back}</Link>
    </main>
  );
}
