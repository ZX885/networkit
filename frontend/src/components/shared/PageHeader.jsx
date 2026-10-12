import styles from './PageHeader.module.css';

// Шапка страницы приложения (legacy .ah): заголовок h1 и действия справа/рядом (children)
export default function PageHeader({ title, children }) {
  return (
    <div className={styles.header}>
      <h1 className={`${styles.title} user-text`}>{title}</h1>
      {children}
    </div>
  );
}
