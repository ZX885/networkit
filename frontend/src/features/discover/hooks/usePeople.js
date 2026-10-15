import { useEffect, useState } from 'react';
import { searchProfiles } from '../../../api/profiles.js';

// Загружает людей по параметрам поиска (GET /api/profiles/). Устаревший запрос отменяется
// (AbortController), а его ответ не применяется. Возвращает { loading, error, data, retry }.
// «Загрузка» считается из ключа запроса: пока ответ относится к другому запросу, показываем загрузку.
// error — ApiError; error.status === 404 при page > 1 значит «страницы с таким номером нет».
export default function usePeople(params) {
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState({ key: null, data: null, error: null });
  const key = JSON.stringify([params, attempt]);

  useEffect(() => {
    const controller = new AbortController();
    let ignore = false;
    searchProfiles(JSON.parse(key)[0], { signal: controller.signal }).then(
      (data) => !ignore && setState({ key, data, error: null }),
      (error) => !ignore && setState({ key, data: null, error }),
    );
    return () => {
      ignore = true;
      controller.abort();
    };
  }, [key]);

  const loading = state.key !== key;
  return {
    loading,
    error: loading ? null : state.error,
    data: loading ? null : state.data,
    retry: () => setAttempt((n) => n + 1),
  };
}
