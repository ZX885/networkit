import { useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Moon, Sun } from 'lucide-react';
import useTheme from '../../app/providers/useTheme.js';
import Logo from '../ui/Logo.jsx';
import Button from '../ui/Button.jsx';
import { texts } from '../../texts/en.js';
import MobileMenu from './MobileMenu.jsx';
import styles from './Navbar.module.css';

const t = texts.nav;
// Ссылки на секции лендинга: переход на «/» с якорем, прокрутку делает LandingPage
const SECTION_LINKS = [
  { hash: '#features', label: t.features },
  { hash: '#how', label: t.how },
  { hash: '#faq', label: t.faq },
];

// Верхняя панель публичных страниц (legacy #nav): логотип, ссылки, вход, тема, регистрация.
export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);
  const menuButtonRef = useRef(null);
  const navigate = useNavigate();
  const { resolved, setMode } = useTheme();
  const isDark = resolved === 'dark';

  function closeMenu() {
    setMenuOpen(false);
    menuButtonRef.current?.focus(); // возвращаем фокус на кнопку, которая открыла меню
  }

  return (
    <>
      <nav className={styles.nav} aria-label={t.label}>
        <Logo />
        <div className={styles.links}>
          {SECTION_LINKS.map((link) => (
            <Link key={link.hash} to={{ pathname: '/', hash: link.hash }} className={styles.link}>
              {link.label}
            </Link>
          ))}
        </div>
        <div className={styles.actions}>
          <Button
            variant="ghost"
            size="sm"
            className={styles.desktopOnly}
            onClick={() => navigate('/login')}
          >
            {t.logIn}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className={`${styles.desktopOnly} ${styles.themeButton}`}
            aria-label={isDark ? t.toLight : t.toDark}
            onClick={() => setMode(isDark ? 'light' : 'dark')}
          >
            {isDark ? <Sun size={16} aria-hidden="true" /> : <Moon size={16} aria-hidden="true" />}
          </Button>
          <Button size="sm" onClick={() => navigate('/register')}>
            {t.joinNow}
          </Button>
          <button
            ref={menuButtonRef}
            type="button"
            className={styles.hamburger}
            aria-label={t.openMenu}
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen(true)}
          >
            <span />
            <span />
            <span />
          </button>
        </div>
      </nav>
      <MobileMenu open={menuOpen} onClose={closeMenu} links={SECTION_LINKS} />
    </>
  );
}
