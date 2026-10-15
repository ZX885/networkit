// Избранное: GET /api/saved/, PUT и DELETE /api/saved/{username}/ (docs/SPEC.md §3.6).
import { api } from '../lib/apiClient.js';
import { PAGE_SIZE } from './profiles.js';

// params: { page }. Возвращает { count, pageCount, results: [Card с is_saved: true] }.
export async function listSaved({ page = 1 } = {}, { signal } = {}) {
  const query = page > 1 ? { page } : undefined;
  const data = await api.get('/saved/', { params: query, signal });
  return {
    count: data.count,
    pageCount: Math.max(1, Math.ceil(data.count / PAGE_SIZE)),
    results: data.results,
  };
}

// Оба запроса идемпотентны и отвечают 204. Ошибки: 400 cannot_target_self, 404 (человек недоступен),
// 409 saved_limit_reached (лимит limits.saved_max из /api/meta/), 429 throttled.
export const saveProfile = (username) => api.put(`/saved/${encodeURIComponent(username)}/`);
export const unsaveProfile = (username) => api.delete(`/saved/${encodeURIComponent(username)}/`);
