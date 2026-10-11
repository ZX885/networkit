import styles from './Section.module.css';

// Обёртка секции на странице styleguide (только для разработки)
export default function Section({ title, children }) {
  return (
    <section className={styles.section}>
      <h2 className={styles.title}>{title}</h2>
      {children}
    </section>
  );
}
