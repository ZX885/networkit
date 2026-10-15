import { useCallback, useEffect, useState } from 'react';
import { PAGE_SIZE } from '../../../api/profiles.js';
import { listSaved } from '../../../api/saved.js';

const pageCountOf = (count) => Math.max(1, Math.ceil(count / PAGE_SIZE));

// Список «Избранное» (GET /api/saved/) с постраничной загрузкой. Устаревший запрос отменяется.
// remove(username) убирает карточку из списка сразу, restore(username) возвращает её на прежнее место
// (если сохранение не удалось). Возвращает { loading, error, data, retry, remove, restore }.
// Обновления состояния чистые (без побочных эффектов): StrictMode вызывает их дважды.
export default function useSaved(page) {
  const [attempt, setAttempt] = useState(0);
  // removed — убранные из списка карточки и их позиции (для отката)
  const [state, setState] = useState({ key: null, data: null, error: null, removed: {} });
  const key = JSON.stringify([page, attempt]);

  useEffect(() => {
    const controller = new AbortController();
    let ignore = false;
    listSaved({ page }, { signal: controller.signal }).then(
      (data) => !ignore && setState({ key, data, error: null, removed: {} }),
      (error) => !ignore && setState({ key, data: null, error, removed: {} }),
    );
    return () => {
      ignore = true;
      controller.abort();
    };
  }, [key, page]);

  const remove = useCallback((username) => {
    setState((prev) => {
      if (!prev.data) return prev;
      const index = prev.data.results.findIndex((person) => person.username === username);
      if (index < 0) return prev;
      const results = prev.data.results.filter((person) => person.username !== username);
      const count = prev.data.count - 1;
      return {
        ...prev,
        data: { ...prev.data, results, count, pageCount: pageCountOf(count) },
        removed: { ...prev.removed, [username]: { person: prev.data.results[index], index } },
      };
    });
  }, []);

  const restore = useCallback((username) => {
    setState((prev) => {
      const entry = prev.removed[username];
      if (!prev.data || !entry) return prev;
      const { [username]: _restored, ...removed } = prev.removed; // eslint-disable-line no-unused-vars
      const results = [...prev.data.results];
      results.splice(Math.min(entry.index, results.length), 0, { ...entry.person, is_saved: true });
      const count = prev.data.count + 1;
      return {
        ...prev,
        data: { ...prev.data, results, count, pageCount: pageCountOf(count) },
        removed,
      };
    });
  }, []);

  const loading = state.key !== key;
  return {
    loading,
    error: loading ? null : state.error,
    data: loading ? null : state.data,
    retry: () => setAttempt((n) => n + 1),
    remove,
    restore,
  };
}
