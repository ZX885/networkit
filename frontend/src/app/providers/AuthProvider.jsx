import { useCallback, useEffect, useMemo, useState } from 'react';
import { login as apiLogin, logout as apiLogout } from '../../api/auth.js';
import { getMe } from '../../api/me.js';
import { setUnauthorizedHandler } from '../../lib/apiClient.js';
import { AuthContext } from './AuthContext.js';

const GUEST = { status: 'anonymous', user: null };

// Спрашивает сервер, кто вошёл (GET /api/me/), и возвращает новое состояние
function askServer() {
  return getMe().then(
    (user) => ({ status: 'authenticated', user }),
    (error) => {
      // Нет связи или сбой сервера — это не «гость», а повод показать «Try again»
      const failed = error.code === 'network_error' || error.code === 'server_error';
      return failed || error.status >= 500
        ? { status: 'error', user: null, errorCode: error.code }
        : GUEST;
    },
  );
}

// Хранит, кто сейчас вошёл. При старте спрашивает сервер (GET /api/me/): 401 — гость.
// Данные пользователя (Own-профиль) лежат только в памяти, в localStorage ничего не сохраняем.
export default function AuthProvider({ children }) {
  const [state, setState] = useState({ status: 'loading', user: null });

  // Повторная проверка (например, по кнопке «Try again»): на время запроса показываем загрузку
  const refresh = useCallback(() => {
    setState((current) => ({ status: 'loading', user: current.user }));
    return askServer().then(setState);
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(() => setState(GUEST)); // сессия закончилась посреди работы
    let ignore = false; // StrictMode в dev запускает эффект дважды: устаревший ответ не применяем
    askServer().then((next) => {
      if (!ignore) setState(next);
    });
    return () => {
      ignore = true;
    };
  }, []);

  const login = useCallback(async (email, password) => {
    const user = await apiLogin(email, password);
    setState({ status: 'authenticated', user });
    return user;
  }, []);

  const logout = useCallback(async () => {
    try {
      await apiLogout();
    } catch (error) {
      if (error.code === 'network_error') throw error; // не вышли: сервер недоступен
    }
    setState(GUEST);
  }, []);

  const value = useMemo(
    () => ({ ...state, login, logout, refresh }),
    [state, login, logout, refresh],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
