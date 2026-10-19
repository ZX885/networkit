import { NavLink } from 'react-router-dom';
import { Ban, Lock, ShieldCheck, TriangleAlert, User } from 'lucide-react';
import { texts } from '../../../texts/en.js';
import styles from './SettingsNav.module.css';

const t = texts.settings;
const TABS = [
  { path: 'account', label: t.tabs.account, icon: User },
  { path: 'privacy', label: t.tabs.privacy, icon: Lock },
  { path: 'security', label: t.tabs.security, icon: ShieldCheck },
  { path: 'danger', label: t.tabs.danger, icon: TriangleAlert },
  { path: 'blocked', label: t.tabs.blocked, icon: Ban },
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
            [styles.item, isActive && styles.active].filter(Boolean).join(' ')
          }
        >
          <tab.icon size={16} aria-hidden="true" />
          {tab.label}
        </NavLink>
      ))}
    </nav>
  );
}
