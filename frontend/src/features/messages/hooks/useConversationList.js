import { useCallback, useEffect, useState } from 'react';
import { listConversations } from '../../../api/conversations.js';

// Список диалогов вкладки (GET /api/conversations/?box=): загрузка по странице, устаревший запрос
// отменяется. refreshKey (например, счётчики summary) перезагружает список, не показывая загрузку:
// прежние данные остаются на экране. Возвращает { loading, error, data, retry, reload }.
export default function useConversationList(box, page, refreshKey) {
  const [attempt, setAttempt] = useState(0);
  const [reloads, setReloads] = useState(0);
  const [state, setState] = useState({ scope: null, data: null, error: null });
  const reload = useCallback(() => setReloads((n) => n + 1), []);
  const scope = `${box}#${page}#${attempt}`;
  const key = `${scope}#${refreshKey}#${reloads}`;

  useEffect(() => {
    const controller = new AbortController();
    let ignore = false;
    listConversations({ box, page }, { signal: controller.signal }).then(
      (data) => !ignore && setState({ scope, data, error: null }),
      (error) => !ignore && setState({ scope, data: null, error }),
    );
    return () => {
      ignore = true;
      controller.abort();
    };
  }, [key, box, page, scope]);

  const loading = state.scope !== scope;
  return {
    loading,
    error: loading ? null : state.error,
    data: loading ? null : state.data,
    retry: () => setAttempt((n) => n + 1),
    reload,
  };
}
