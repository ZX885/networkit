import { useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { X } from 'lucide-react';
import Button from '../ui/Button.jsx';
import { texts } from '../../texts/en.js';
import styles from './MobileMenu.module.css';

// Мобильное меню на весь экран (legacy #mobile-menu). Esc закрывает, фокус уходит на кнопку «закрыть».
// В закрытом состоянии элемент inert — скрыт от клавиатуры и скринридера.
// status — состояние входа (loading / anonymous / authenticated / error), onLogout — выход.
export default function MobileMenu({ open, onClose, links, status, onLogout }) {
  const closeRef = useRef(null);
  const navigate = useNavigate();
  const t = texts.nav;

  useEffect(() => {
    if (!open) return undefined;
    closeRef.current?.focus();
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const onKeyDown = (event) => event.key === 'Escape' && onClose();
    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener('keydown', onKeyDown);
    };
  }, [open, onClose]);

  function goTo(path) {
    onClose();
    navigate(path);
  }

  return (
    <div className={[styles.menu, open && styles.open].filter(Boolean).join(' ')} inert={!open}>
      <button
        ref={closeRef}
        type="button"
        className={styles.close}
        aria-label={t.closeMenu}
        onClick={onClose}
      >
        <X size={16} aria-hidden="true" />
      </button>
      {links.map((link) => (
        <Link
          key={link.hash}
          to={{ pathname: '/', hash: link.hash }}
          className={styles.link}
          onClick={onClose}
        >
          {link.label}
        </Link>
      ))}
      {status === 'authenticated' && (
        <>
          <Link to="/discover" className={styles.link} onClick={onClose}>
            {t.openApp}
          </Link>
          <Button
            variant="ghost"
            onClick={() => {
              onClose();
              onLogout();
            }}
          >
            {t.logOut}
          </Button>
        </>
      )}
      {(status === 'anonymous' || status === 'error') && (
        <>
          <Link to="/login" className={styles.link} onClick={onClose}>
            {t.logIn}
          </Link>
          <Button onClick={() => goTo('/register')}>{t.joinNow}</Button>
        </>
      )}
    </div>
  );
}
