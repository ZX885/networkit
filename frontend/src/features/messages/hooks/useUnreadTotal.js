import { useSyncExternalStore } from 'react';
import { getUnreadTotal, subscribeMessages } from '../../../api/mock/messages.js';

// Число непрочитанных сообщений для бейджа в сайдбаре (MOCK, потом GET /api/conversations/summary/)
export default function useUnreadTotal() {
  return useSyncExternalStore(subscribeMessages, getUnreadTotal);
}
