import styles from './EmptyState.module.css';

// Заглушка пустого списка: иконка (необязательно), заголовок, пояснение, кнопка действия.
// Тексты и иконку передаёт вызывающий код.
export default function EmptyState({ icon, title, description, action }) {
  return (
    <div className={styles.empty}>
      {icon && (
        <div className={styles.icon} aria-hidden="true">
          {icon}
        </div>
      )}
      <h3 className={styles.title}>{title}</h3>
      {description && <p className={styles.description}>{description}</p>}
      {action && <div className={styles.action}>{action}</div>}
    </div>
  );
}
