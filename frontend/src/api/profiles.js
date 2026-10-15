// Поиск людей и публичный профиль: GET /api/profiles/ и /api/profiles/{username}/ (docs/SPEC.md §3.6).
import { api } from '../lib/apiClient.js';

export const PAGE_SIZE = 12; // размер страницы по умолчанию на сервере

const FILTERS = ['q', 'country', 'city', 'field', 'status', 'goal', 'language'];

// params: { q, country, field, status, goal, language, page } — пустые значения не отправляем.
// Возвращает { count, pageCount, results: [Card] }. signal (AbortController) отменяет устаревший запрос.
export async function searchProfiles(params, { signal } = {}) {
  const query = {};
  FILTERS.forEach((key) => {
    if (params[key]) query[key] = params[key];
  });
  if (params.page > 1) query.page = params.page;
  const data = await api.get('/profiles/', { params: query, signal });
  return {
    count: data.count,
    pageCount: Math.max(1, Math.ceil(data.count / PAGE_SIZE)),
    results: data.results,
  };
}

// Публичный профиль (Public, SPEC §6.1): скрытые поля приходят как null. 404 → ApiError с status 404.
export const getProfile = (username, { signal } = {}) =>
  api.get(`/profiles/${encodeURIComponent(username)}/`, { signal });
