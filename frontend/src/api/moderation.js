// Блокировки и жалобы: /api/blocks/ и /api/reports/ (docs/SPEC.md §3.7). Ошибки приходят как ApiError.
import { api } from '../lib/apiClient.js';
import { PAGE_SIZE } from './profiles.js';

const enc = encodeURIComponent;

// Кого заблокировал я: { count, pageCount, results: [{username, first_name, last_name, avatar_url}] }
export async function listBlocks({ page = 1 } = {}, { signal } = {}) {
  const params = {};
  if (page > 1) params.page = page;
  const data = await api.get('/blocks/', { params, signal });
  return {
    count: data.count,
    pageCount: Math.max(1, Math.ceil(data.count / PAGE_SIZE)),
    results: data.results,
  };
}

// Оба идемпотентны (204). Блокировка действует в обе стороны, заблокированный о ней не узнаёт.
export const blockUser = (username) => api.put(`/blocks/${enc(username)}/`);
export const unblockUser = (username) => api.delete(`/blocks/${enc(username)}/`);

// Жалоба на человека; conversationId — если жалуются из чата (к жалобе прикрепляется диалог).
// Ответ всегда один: { status: 'received' } (дубль открытой жалобы тоже).
export const reportUser = ({ username, reason, details, conversationId }) =>
  api.post('/reports/', {
    username,
    reason,
    details,
    ...(conversationId ? { conversation_id: conversationId } : {}),
  });
