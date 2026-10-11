import styles from './Toast.module.css';

// Визуальный тост. type: info | success | error. Показывается и скрывается через visible.
// Сам себя не скрывает — этим управляет ToastProvider.
export default function Toast({ message, type = 'info', visible }) {
  const classes = [styles.toast, styles[type], visible && styles.visible].filter(Boolean).join(' ');
  return <div className={classes}>{message}</div>;
}
