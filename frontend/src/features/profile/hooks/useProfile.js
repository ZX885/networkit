import { useEffect, useState } from 'react';
import { getPublicProfile } from '../../../api/mock/people.js';

// Загружает чужой профиль по username (MOCK, потом GET /api/profiles/{username}/).
// status: loading | ready | notFound | error. «Загрузка» считается из ключа: ответ другого username не показываем.
export default function useProfile(username) {
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState({ key: null, profile: null, error: false });
  const key = `${username}#${attempt}`;

  useEffect(() => {
    let ignore = false;
    getPublicProfile(username).then(
      (profile) => !ignore && setState({ key, profile, error: false }),
      () => !ignore && setState({ key, profile: null, error: true }),
    );
    return () => {
      ignore = true;
    };
  }, [key, username]);

  const retry = () => setAttempt((n) => n + 1);
  if (state.key !== key) return { status: 'loading', profile: null, retry };
  if (state.error) return { status: 'error', profile: null, retry };
  if (!state.profile) return { status: 'notFound', profile: null, retry };
  return { status: 'ready', profile: state.profile, retry };
}
