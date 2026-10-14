import { useCallback, useEffect, useRef, useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Menu } from 'lucide-react';
import { loadMeta } from '../../api/meta.js';
import { texts } from '../../texts/en.js';
import styles from './AppLayout.module.css';
import Sidebar from './Sidebar.jsx';
import useFocusOnNavigate from './useFocusOnNavigate.js';

const SIDEBAR_ID = 'app-sidebar';

// Оболочка приложения для вошедшего: боковая панель + страница. Navbar лендинга здесь не показываем.
// children — вместо вложенных маршрутов (404 внутри приложения). На ≤900px панель открывается кнопкой-гамбургером; закрывается по фону, Esc и при переходе.
export default function AppLayout({ children }) {
  const { pathname } = useLocation();
  // Запоминаем, на какой странице открыли меню: после перехода оно закрывается само
  const [openedAt, setOpenedAt] = useState(null);
  const open = openedAt === pathname;
  const buttonRef = useRef(null);
  const mainRef = useRef(null);

  useFocusOnNavigate(mainRef);

  // Прогрев кэша справочников (GET /api/meta/): один фоновый запрос при входе в приложение, без
  // индикатора. Ошибку игнорируем: страницы, которым справочники нужны, сами покажут «Try again».
  useEffect(() => {
    loadMeta().catch(() => {});
  }, []);

  const closeMenu = useCallback(() => {
    setOpenedAt(null);
    buttonRef.current?.focus(); // возвращаем фокус на кнопку, которая открыла меню
  }, []);

  useEffect(() => {
    if (!open) return undefined;
    const onKeyDown = (event) => event.key === 'Escape' && closeMenu();
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [open, closeMenu]);

  return (
    <div className={styles.layout}>
      <button
        ref={buttonRef}
        type="button"
        className={styles.menuButton}
        aria-label={texts.app.nav.openMenu}
        aria-expanded={open}
        aria-controls={SIDEBAR_ID}
        onClick={() => setOpenedAt(pathname)}
      >
        <Menu size={20} aria-hidden="true" />
      </button>
      {open && <div className={styles.backdrop} onClick={closeMenu} aria-hidden="true" />}
      <Sidebar id={SIDEBAR_ID} open={open} />
      <main ref={mainRef} className={styles.main}>
        {children ?? <Outlet />}
      </main>
    </div>
  );
}
