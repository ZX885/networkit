import { useEffect, useId, useRef } from 'react';
import { createPortal } from 'react-dom';
import styles from './Modal.module.css';

const FOCUSABLE =
  'a[href], button:not(:disabled), input:not(:disabled), select:not(:disabled), textarea:not(:disabled), [tabindex]:not([tabindex="-1"])';

// Модальное окно (role=dialog). Закрывается по Esc и клику на фон.
// Фокус уходит внутрь окна, Tab не выходит за его пределы, после закрытия фокус возвращается.
// title / description / actions — тексты и кнопки передаёт вызывающий код.
export default function Modal({ open, onClose, title, description, actions, children }) {
  const titleId = useId();
  const descId = useId();
  const boxRef = useRef(null);
  const pressedOnOverlay = useRef(false);
  const onCloseRef = useRef(onClose);

  // Храним свежий onClose, чтобы эффект ниже не перезапускался при каждом рендере родителя
  useEffect(() => {
    onCloseRef.current = onClose;
  });

  useEffect(() => {
    if (!open) return undefined;
    const box = boxRef.current;
    const previouslyFocused = document.activeElement;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden'; // фон не прокручивается
    (box.querySelector('input, select, textarea') || box).focus();

    function handleKeyDown(event) {
      if (event.key === 'Escape') {
        onCloseRef.current();
        return;
      }
      if (event.key !== 'Tab') return;
      const items = box.querySelectorAll(FOCUSABLE);
      if (items.length === 0) {
        event.preventDefault();
        return;
      }
      const first = items[0];
      const last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = previousOverflow;
      previouslyFocused?.focus?.();
    };
  }, [open]);

  if (!open) return null;

  return createPortal(
    <div
      className={styles.overlay}
      onMouseDown={(event) => {
        pressedOnOverlay.current = event.target === event.currentTarget;
      }}
      onClick={(event) => {
        // Закрываем, только если и нажатие, и отпускание были на фоне (не при выделении текста)
        if (pressedOnOverlay.current && event.target === event.currentTarget) onClose();
      }}
    >
      <div
        ref={boxRef}
        className={styles.box}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={description ? descId : undefined}
        tabIndex={-1}
      >
        <h3 id={titleId} className={styles.title}>
          {title}
        </h3>
        {description && (
          <p id={descId} className={styles.description}>
            {description}
          </p>
        )}
        {children}
        {actions && <div className={styles.actions}>{actions}</div>}
      </div>
    </div>,
    document.body,
  );
}
