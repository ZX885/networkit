import { NavLink } from 'react-router-dom';
import styles from './SidebarLink.module.css';

// Пункт бокового меню (legacy .sbl): ссылка (NavLink, aria-current ставит сам) или кнопка действия.
// tone="danger" — красный (выход). badge — число в синей таблетке справа (0 — не показывается).
export default function SidebarLink({
  to,
  icon: Icon,
  onClick,
  tone,
  badge,
  badgeLabel,
  children,
}) {
  const classes = (isActive) =>
    [styles.item, tone === 'danger' && styles.danger, isActive && styles.active]
      .filter(Boolean)
      .join(' ');

  const content = (
    <>
      <Icon size={18} aria-hidden="true" />
      <span className={styles.label}>{children}</span>
      {badge > 0 && (
        <span className={styles.badge}>
          {badge}
          <span className="visually-hidden"> {badgeLabel}</span>
        </span>
      )}
    </>
  );

  if (to) {
    return (
      <NavLink to={to} className={({ isActive }) => classes(isActive)}>
        {content}
      </NavLink>
    );
  }
  return (
    <button type="button" className={classes(false)} onClick={onClick}>
      {content}
    </button>
  );
}
