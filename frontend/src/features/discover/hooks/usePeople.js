import { useEffect, useState } from 'react';
import { searchPeople } from '../../../api/mock/people.js';

// Загружает людей по параметрам поиска (MOCK, потом GET /api/profiles/).
// Возвращает { loading, error, data, retry }. Состояние «загрузка» считается из ключа запроса:
// пока ответ относится к другому запросу, показываем загрузку.
export default function usePeople(params) {
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState({ key: null, data: null, error: false });
  const key = JSON.stringify([params, attempt]);

  useEffect(() => {
    let ignore = false;
    searchPeople(JSON.parse(key)[0]).then(
      (data) => !ignore && setState({ key, data, error: false }),
      () => !ignore && setState({ key, data: null, error: true }),
    );
    return () => {
      ignore = true;
    };
  }, [key]);

  const loading = state.key !== key;
  return {
    loading,
    error: !loading && state.error,
    data: loading ? null : state.data,
    retry: () => setAttempt((n) => n + 1),
  };
}
