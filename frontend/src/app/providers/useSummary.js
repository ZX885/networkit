import { useContext } from 'react';
import { SummaryContext } from './SummaryContext.js';

// { summary: { unread_messages, pending_requests }, refresh }. Вне SummaryProvider (оболочки приложения)
// возвращает нули и пустой refresh, чтобы компоненты не падали.
const FALLBACK = {
  summary: { unread_messages: 0, pending_requests: 0 },
  refresh: () => Promise.resolve(),
};

export default function useSummary() {
  return useContext(SummaryContext) ?? FALLBACK;
}
