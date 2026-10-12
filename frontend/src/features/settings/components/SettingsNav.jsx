import { NavLink } from 'react-router-dom';
import { AlertTriangle, Lock, Shield, User } from 'lucide-react';
import { texts } from '../../../texts/en.js';
import styles from './SettingsNav.module.css';

const t = texts.settings;
const TABS = [
  { path: 'account', label: t.tabs.account, icon: User },
  { path: 'privacy', label: t.tabs.privacy, icon: Lock },
  { path: 'security', label: t.tabs.security, icon: Shield },
  { path: 'danger', label: t.tabs.danger, icon: AlertTriangle, danger: true },
];

// Вкладки настроек (legacy .s-nav). Это подмаршруты /settings/…, активную отмечает NavLink (aria-current).
export default function SettingsNav() {
  return (
    <nav className={styles.nav} aria-label={t.navLabel}>
      {TABS.map((tab) => (
        <NavLink
          key={tab.path}
          to={`/settings/${tab.path}`}
          className={({ isActive }) =>
            [styles.item, tab.danger && styles.danger, isActive && styles.active]
              .filter(Boolean)
              .join(' ')
          }
        >
          <tab.icon size={16} aria-hidden="true" />
          {tab.label}
        </NavLink>
      ))}
    </nav>
  );
}
