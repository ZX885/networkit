import { useEffect, useState } from 'react';
import { checkUsername } from '../../../api/auth.js';
import { USERNAME_REGEX } from '../../../constants/rules.js';

const DEBOUNCE_MS = 400;

// Проверка username на сервере: запрос уходит после паузы в наборе, предыдущий запрос отменяется,
// устаревшие ответы игнорируются. Возвращает:
// 'idle' | 'invalid' (формат) | 'checking' | 'available' | 'taken' | 'reserved' | 'unknown'.
// 'unknown' — лимит запросов или нет связи: ввод не блокируем (сервер проверит при отправке формы).
export default function useUsernameCheck(rawUsername) {
  const username = rawUsername.trim();
  const [result, setResult] = useState({ username: '', status: 'idle' });

  useEffect(() => {
    if (!USERNAME_REGEX.test(username)) return undefined;
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      try {
        const { available, reason } = await checkUsername(username, { signal: controller.signal });
        const status = available ? 'available' : reason === 'reserved' ? 'reserved' : 'taken';
        setResult({ username, status });
      } catch (error) {
        if (error.name === 'AbortError') return; // имя уже изменилось
        setResult({ username, status: 'unknown' });
      }
    }, DEBOUNCE_MS);
    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [username]);

  if (!username) return 'idle';
  if (!USERNAME_REGEX.test(username)) return 'invalid';
  // Ответ относится к другому имени (или ещё не пришёл) — значит, идёт проверка
  return result.username === username ? result.status : 'checking';
}
