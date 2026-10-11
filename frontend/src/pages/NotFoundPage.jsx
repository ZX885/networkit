import { Link } from 'react-router-dom';
import styles from './StubPage.module.css';

// Страница 404
export default function NotFoundPage() {
  return (
    <main className={styles.page}>
      <h1 className={styles.title}>404</h1>
      <p className={styles.text}>Page not found.</p>
      <Link to="/">Back to home</Link>
    </main>
  );
}
