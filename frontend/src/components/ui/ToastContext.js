import { createContext } from 'react';

// Значение: функция showToast(message, type) — type: 'info' | 'success' | 'error'
export const ToastContext = createContext(null);
