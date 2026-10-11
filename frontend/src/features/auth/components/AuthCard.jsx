import Logo from '../../../components/shared/Logo.jsx';
import styles from './AuthCard.module.css';

// Центрированная карточка для входа и экрана «Check your email» (legacy .auth-wrap / .auth-card).
export default function AuthCard({ title, subtitle, children }) {
  return (
    <div className={styles.wrap}>
      <div className={styles.card}>
        <div className={styles.logo}>
          <Logo size="sm" />
        </div>
        <h1 className={styles.title}>{title}</h1>
        {subtitle && <p className={styles.subtitle}>{subtitle}</p>}
        {children}
      </div>
    </div>
  );
}
