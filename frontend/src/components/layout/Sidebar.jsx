import { useEffect, useRef } from 'react';
import { Bookmark, LogOut, MessageCircle, Search, Settings, User } from 'lucide-react';
import useAuth from '../../app/providers/useAuth.js';
import useLogout from '../../app/providers/useLogout.js';
import useUnreadTotal from '../../features/messages/hooks/useUnreadTotal.js';
import { texts } from '../../texts/en.js';
import Logo from '../ui/Logo.jsx';
import SidebarLink from './SidebarLink.jsx';
import styles from './Sidebar.module.css';
import ThemeSwitch from './ThemeSwitch.jsx';
import UserBlock from './UserBlock.jsx';

const t = texts.app.nav;

// Боковая панель приложения (legacy .sidebar): 230px на широком экране, выезжает на ≤900px.
// open — только для узкого экрана; на широком панель видна всегда.
export default function Sidebar({ id, open }) {
  const { user } = useAuth();
  const handleLogout = useLogout();
  const unread = useUnreadTotal();
  const ref = useRef(null);

  // При открытии на узком экране фокус уходит на первый пункт меню
  useEffect(() => {
    if (open) ref.current?.querySelector('a')?.focus();
  }, [open]);

  return (
    <aside
      ref={ref}
      id={id}
      className={[styles.sidebar, open && styles.open].filter(Boolean).join(' ')}
    >
      <div className={styles.logo}>
        <Logo to="/discover" />
      </div>
      <nav className={styles.nav} aria-label={t.label}>
        <SidebarLink to="/discover" icon={Search}>
          {t.discover}
        </SidebarLink>
        <SidebarLink to="/me" icon={User}>
          {t.myProfile}
        </SidebarLink>
        <SidebarLink to="/messages" icon={MessageCircle} badge={unread}>
          {t.messages}
        </SidebarLink>
        <SidebarLink to="/saved" icon={Bookmark}>
          {t.saved}
        </SidebarLink>
        <SidebarLink to="/settings" icon={Settings}>
          {t.settings}
        </SidebarLink>
        <ThemeSwitch />
        <SidebarLink icon={LogOut} tone="danger" onClick={handleLogout}>
          {t.logOut}
        </SidebarLink>
      </nav>
      <UserBlock user={user} />
    </aside>
  );
}
