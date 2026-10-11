import styles from './Tag.module.css';

// Небольшая «таблетка» с текстом (интересы, цели, языки).
export default function Tag({ children }) {
  return <span className={styles.tag}>{children}</span>;
}
