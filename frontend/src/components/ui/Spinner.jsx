import styles from './Spinner.module.css';

// Индикатор загрузки. Цвет берёт у родителя (currentColor); tone="primary" — фирменный цвет.
// label — текст для скринридера (например "Loading"); внутри Button передаётся пустым.
export default function Spinner({ size = 'md', tone = 'inherit', label = '' }) {
  const className = [styles.spinner, styles[size], tone === 'primary' && styles.primary]
    .filter(Boolean)
    .join(' ');

  return (
    <span className={className} role={label ? 'status' : undefined} aria-hidden={!label}>
      {label && <span className="visually-hidden">{label}</span>}
    </span>
  );
}
