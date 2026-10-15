// Личные сообщения: /api/conversations/ (docs/SPEC.md §3.8–3.9). Ошибки приходят как ApiError (apiClient).
import { api } from '../lib/apiClient.js';
import { PAGE_SIZE } from './profiles.js';

const enc = encodeURIComponent;

// box: 'chats' | 'requests' | 'sent'. Возвращает { count, pageCount, results: [Conversation] }.
export async function listConversations({ box = 'chats', page = 1 } = {}, { signal } = {}) {
  const params = { box };
  if (page > 1) params.page = page;
  const data = await api.get('/conversations/', { params, signal });
  return {
    count: data.count,
    pageCount: Math.max(1, Math.ceil(data.count / PAGE_SIZE)),
    results: data.results,
  };
}

// Запрос на переписку + первое сообщение: → { conversation, message }. Ошибки 409 несут id диалога
// (ApiError.conversationId).
export const createRequest = (username, body) => api.post('/conversations/', { username, body });

export const getConversation = (id, { signal } = {}) =>
  api.get(`/conversations/${enc(id)}/`, { signal });

// Только получатель, только из pending. → Conversation
export const acceptConversation = (id) => api.post(`/conversations/${enc(id)}/accept/`);
export const declineConversation = (id) => api.post(`/conversations/${enc(id)}/decline/`);

// → { unread_messages, pending_requests } (бейджи; опрос раз в 30 секунд)
export const getSummary = ({ signal } = {}) => api.get('/conversations/summary/', { signal });

// Курсорная выдача по возрастанию id: → { results, has_more_older }.
// before — более старые, after — более новые (опрос открытого чата), limit — до 50.
export function listMessages(id, { before, after, limit } = {}, { signal } = {}) {
  const params = {};
  if (before) params.before = before;
  if (after) params.after = after;
  if (limit) params.limit = limit;
  return api.get(`/conversations/${enc(id)}/messages/`, { params, signal });
}

export const sendMessage = (id, body) => api.post(`/conversations/${enc(id)}/messages/`, { body });

// Помечает входящие прочитанными (только в принятом диалоге) → { updated }
export const markRead = (id) => api.post(`/conversations/${enc(id)}/read/`);
