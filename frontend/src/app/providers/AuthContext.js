import { createContext } from 'react';

// Значение: { status, user, login, logout, endSession, refresh, updateUser }
// status: 'loading' (проверяем сессию) | 'anonymous' | 'authenticated' | 'error' (сервер недоступен)
export const AuthContext = createContext(null);
