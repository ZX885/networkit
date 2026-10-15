import { useCallback, useEffect, useMemo, useState } from 'react';
import { getSummary } from '../../api/conversations.js';
import usePolling from '../../lib/usePolling.js';
import { SummaryContext } from './SummaryContext.js';

const POLL_MS = 30_000; // счётчики для бейджей — раз в 30 секунд
const EMPTY = { unread_messages: 0, pending_requests: 0 };

// Счётчики непрочитанных сообщений и входящих запросов (GET /api/conversations/summary/).
// Живёт внутри оболочки приложения (только для вошедшего): опрос раз в 30 секунд, только пока вкладка
// видна, и прекращается при выходе (провайдер размонтируется) и при 401. refresh() — после действий.
export default function SummaryProvider({ children }) {
  const [summary, setSummary] = useState(EMPTY);

  const refresh = useCallback(async () => {
    setSummary(await getSummary());
  }, []);

  useEffect(() => {
    // Первое значение; ошибку молча игнорируем (бейдж просто не покажется)
    let ignore = false;
    getSummary().then(
      (data) => !ignore && setSummary(data),
      () => {},
    );
    return () => {
      ignore = true;
    };
  }, []);
  usePolling(refresh, POLL_MS);

  const value = useMemo(() => ({ summary, refresh }), [summary, refresh]);
  return <SummaryContext.Provider value={value}>{children}</SummaryContext.Provider>;
}
