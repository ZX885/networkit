import { useEffect, useState } from 'react';
import { getProfile } from '../../../api/profiles.js';

// Загружает чужой профиль по username (GET /api/profiles/{username}/).
// status: loading | ready | notFound | error. «Загрузка» считается из ключа: ответ другого username
// не показываем. Устаревший запрос отменяется.
export default function useProfile(username) {
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState({ key: null, profile: null, error: null });
  const key = `${username}#${attempt}`;

  useEffect(() => {
    const controller = new AbortController();
    let ignore = false;
    getProfile(username, { signal: controller.signal }).then(
      (profile) => !ignore && setState({ key, profile, error: null }),
      (error) => !ignore && setState({ key, profile: null, error }),
    );
    return () => {
      ignore = true;
      controller.abort();
    };
  }, [key, username]);

  const retry = () => setAttempt((n) => n + 1);
  if (state.key !== key) return { status: 'loading', profile: null, error: null, retry };
  if (state.error?.status === 404) return { status: 'notFound', profile: null, error: null, retry };
  if (state.error) return { status: 'error', profile: null, error: state.error, retry };
  return { status: 'ready', profile: state.profile, error: null, retry };
}
