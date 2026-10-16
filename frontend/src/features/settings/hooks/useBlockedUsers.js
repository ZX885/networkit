import { useCallback, useEffect, useState } from 'react';
import { listBlocks } from '../../../api/moderation.js';

// Список заблокированных (GET /api/blocks/) с постраничной загрузкой. Устаревший запрос отменяется.
// remove(username) убирает человека из списка сразу после успешной разблокировки.
// Возвращает { loading, error, data, retry, remove }. Обновления состояния чистые (StrictMode).
export default function useBlockedUsers(page) {
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState({ key: null, data: null, error: null });
  const key = `${page}#${attempt}`;

  useEffect(() => {
    const controller = new AbortController();
    let ignore = false;
    listBlocks({ page }, { signal: controller.signal }).then(
      (data) => !ignore && setState({ key, data, error: null }),
      (error) => !ignore && setState({ key, data: null, error }),
    );
    return () => {
      ignore = true;
      controller.abort();
    };
  }, [key, page]);

  const remove = useCallback((username) => {
    setState((prev) => {
      if (!prev.data) return prev;
      const results = prev.data.results.filter((person) => person.username !== username);
      return { ...prev, data: { ...prev.data, results, count: prev.data.count - 1 } };
    });
  }, []);

  const loading = state.key !== key;
  return {
    loading,
    error: loading ? null : state.error,
    data: loading ? null : state.data,
    retry: () => setAttempt((n) => n + 1),
    remove,
  };
}
