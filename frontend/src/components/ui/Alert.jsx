import styles from './Alert.module.css';

// Сообщение внутри формы (legacy .amsg). tone: error | success.
// role="alert" — скринридер зачитывает текст сразу при появлении.
export default function Alert({ tone = 'error', children }) {
  return (
    <div className={[styles.alert, styles[tone]].join(' ')} role="alert">
      {children}
    </div>
  );
}
