import styles from './SettingsPanel.module.css';

// Содержимое вкладки настроек (legacy .s-cont): заголовок, подзаголовок и тело
export default function SettingsPanel({ title, subtitle, children }) {
  return (
    <section className={styles.panel} aria-labelledby="settings-panel-title">
      <h2 id="settings-panel-title" className={styles.title}>
        {title}
      </h2>
      {subtitle && <p className={styles.subtitle}>{subtitle}</p>}
      {children}
    </section>
  );
}
