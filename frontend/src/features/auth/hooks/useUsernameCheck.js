import { useEffect, useState } from 'react';
import { checkUsername } from '../../../api/mock/auth.js';
import { USERNAME_REGEX } from '../../../constants/rules.js';

const DEBOUNCE_MS = 400;

// Проверка занятости username: запрос уходит после паузы в наборе, устаревшие ответы игнорируются.
// Возвращает: 'idle' | 'invalid' (формат) | 'checking' | 'available' | 'taken' | 'error'.
export default function useUsernameCheck(rawUsername) {
  const username = rawUsername.trim();
  const [result, setResult] = useState({ username: '', status: 'idle' });

  useEffect(() => {
    if (!USERNAME_REGEX.test(username)) return undefined;
    let outdated = false; // станет true, если имя изменилось раньше, чем пришёл ответ
    const timer = setTimeout(async () => {
      try {
        const { available } = await checkUsername(username);
        if (!outdated) setResult({ username, status: available ? 'available' : 'taken' });
      } catch {
        if (!outdated) setResult({ username, status: 'error' });
      }
    }, DEBOUNCE_MS);
    return () => {
      outdated = true;
      clearTimeout(timer);
    };
  }, [username]);

  if (!username) return 'idle';
  if (!USERNAME_REGEX.test(username)) return 'invalid';
  // Ответ относится к другому имени (или ещё не пришёл) — значит, идёт проверка
  return result.username === username ? result.status : 'checking';
}
