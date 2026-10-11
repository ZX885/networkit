import styles from './SectionHeader.module.css';

// Заголовок секции лендинга: надпись-eyebrow, заголовок, подзаголовок (необязательно).
// align="center" — по центру (секции How it works и FAQ).
export default function SectionHeader({ eyebrow, title, subtitle, align = 'left', titleId }) {
  return (
    <div className={align === 'center' ? styles.center : undefined}>
      <p className={styles.eyebrow}>{eyebrow}</p>
      <h2 className={styles.title} id={titleId}>
        {title}
      </h2>
      {subtitle && <p className={styles.subtitle}>{subtitle}</p>}
    </div>
  );
}
