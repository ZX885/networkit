import { useCallback, useEffect, useRef, useState } from 'react';
import Toast from './Toast.jsx';
import { ToastContext } from './ToastContext.js';
import styles from './ToastProvider.module.css';

const TOAST_MS = 3000; // как в legacy

// Показывает один тост за раз (новый заменяет старый).
// Область aria-live есть в DOM всегда — так скринридер зачитывает появление текста.
export default function ToastProvider({ children }) {
  const [toast, setToast] = useState({ message: '', type: 'info', visible: false });
  const timerRef = useRef(null);

  const showToast = useCallback((message, type = 'info') => {
    clearTimeout(timerRef.current);
    setToast({ message, type, visible: true });
    timerRef.current = setTimeout(() => setToast((t) => ({ ...t, visible: false })), TOAST_MS);
  }, []);

  useEffect(() => () => clearTimeout(timerRef.current), []);

  return (
    <ToastContext.Provider value={showToast}>
      {children}
      <div className={styles.region} role="status" aria-live="polite" aria-atomic="true">
        <Toast message={toast.message} type={toast.type} visible={toast.visible} />
      </div>
    </ToastContext.Provider>
  );
}
