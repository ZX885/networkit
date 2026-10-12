import styles from './ProfileSection.module.css';

// Блок профиля (legacy .psec): маленький заголовок капсом с иконкой и содержимое
export default function ProfileSection({ icon: Icon, title, children }) {
  return (
    <section className={styles.section}>
      <h2 className={styles.title}>
        {Icon && <Icon size={13} aria-hidden="true" />}
        {title}
      </h2>
      {children}
    </section>
  );
}
