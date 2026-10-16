import { useEffect, useId, useRef, useState } from 'react';
import { Ban, Ellipsis, Flag } from 'lucide-react';
import useToast from '../../../components/ui/useToast.js';
import { fullName } from '../../../lib/labels.js';
import { texts } from '../../../texts/en.js';
import BlockModal from './BlockModal.jsx';
import ReportModal from './ReportModal.jsx';
import styles from './ReportBlockMenu.module.css';

const t = texts.moderation;

// Меню «⋯» с пунктами «Report» и «Block» (профиль и окно чата). Клавиатура: Enter/Space/↓ открывают,
// ↑/↓/Home/End двигаются по пунктам, Esc закрывает и возвращает фокус на кнопку, Tab закрывает.
// Разблокировка — только в Settings → Blocked users: профиль заблокированного для заблокировавшего
// недоступен (404), поэтому «Unblock» на его странице показать негде.
// person — { username, first_name, last_name }; conversationId — если открыто из чата (жалоба на диалог);
// onBlocked() — после успешной блокировки (родитель уходит со страницы).
export default function ReportBlockMenu({ person, conversationId, onBlocked }) {
  const [open, setOpen] = useState(false);
  const [dialog, setDialog] = useState(null); // 'report' | 'block'
  const rootRef = useRef(null);
  const buttonRef = useRef(null);
  const itemRefs = useRef([]);
  const menuId = useId();
  const showToast = useToast();
  const name = fullName(person);

  // Открыли меню → фокус на первый пункт
  useEffect(() => {
    if (open) itemRefs.current[0]?.focus();
  }, [open]);

  // Клик или фокус вне меню закрывает его
  useEffect(() => {
    if (!open) return undefined;
    function handleOutside(event) {
      if (!rootRef.current?.contains(event.target)) setOpen(false);
    }
    document.addEventListener('mousedown', handleOutside);
    document.addEventListener('focusin', handleOutside);
    return () => {
      document.removeEventListener('mousedown', handleOutside);
      document.removeEventListener('focusin', handleOutside);
    };
  }, [open]);

  function closeMenu() {
    setOpen(false);
    buttonRef.current?.focus();
  }

  function choose(kind) {
    closeMenu(); // фокус возвращается на кнопку: окно вернёт его туда после закрытия
    setDialog(kind);
  }

  function handleButtonKeyDown(event) {
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      setOpen(true);
    }
  }

  function handleMenuKeyDown(event) {
    const items = itemRefs.current.filter(Boolean);
    const index = items.indexOf(document.activeElement);
    const move = (next) => {
      event.preventDefault();
      items[(next + items.length) % items.length]?.focus();
    };
    if (event.key === 'Escape') {
      event.preventDefault();
      event.stopPropagation();
      closeMenu();
    } else if (event.key === 'ArrowDown') move(index + 1);
    else if (event.key === 'ArrowUp') move(index - 1);
    else if (event.key === 'Home') move(0);
    else if (event.key === 'End') move(items.length - 1);
    else if (event.key === 'Tab') setOpen(false);
  }

  function handleBlocked() {
    setDialog(null);
    showToast(t.blockedToast(name), 'success');
    onBlocked?.();
  }

  return (
    <div className={styles.root} ref={rootRef}>
      <button
        ref={buttonRef}
        type="button"
        className={styles.button}
        aria-label={t.menuLabel(name)}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={open ? menuId : undefined}
        onClick={() => setOpen((value) => !value)}
        onKeyDown={handleButtonKeyDown}
      >
        <Ellipsis size={18} aria-hidden="true" />
      </button>
      {open && (
        <ul id={menuId} className={styles.menu} role="menu" onKeyDown={handleMenuKeyDown}>
          <li role="none">
            <button
              ref={(el) => (itemRefs.current[0] = el)}
              type="button"
              role="menuitem"
              tabIndex={-1}
              className={styles.item}
              onClick={() => choose('report')}
            >
              <Flag size={15} aria-hidden="true" />
              {t.report}
            </button>
          </li>
          <li role="none">
            <button
              ref={(el) => (itemRefs.current[1] = el)}
              type="button"
              role="menuitem"
              tabIndex={-1}
              className={[styles.item, styles.danger].join(' ')}
              onClick={() => choose('block')}
            >
              <Ban size={15} aria-hidden="true" />
              {t.block}
            </button>
          </li>
        </ul>
      )}
      {dialog === 'report' && (
        <ReportModal
          person={person}
          conversationId={conversationId}
          onClose={() => setDialog(null)}
        />
      )}
      {dialog === 'block' && (
        <BlockModal person={person} onClose={() => setDialog(null)} onBlocked={handleBlocked} />
      )}
    </div>
  );
}
