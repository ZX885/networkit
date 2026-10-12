import { createContext } from 'react';

// Значение: { status, user, login, logout, refresh }
// status: 'loading' (проверяем сессию) | 'anonymous' | 'authenticated' | 'error' (сервер недоступен)
export const AuthContext = createContext(null);
