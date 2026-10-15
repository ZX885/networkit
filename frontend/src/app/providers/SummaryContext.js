import { createContext } from 'react';

// { summary: { unread_messages, pending_requests }, refresh() } — счётчики для бейджей
export const SummaryContext = createContext(null);
