import { api } from '../lib/apiClient.js';

// GET /api/me/ → Own-профиль (401, если не вошёл; 404, если у аккаунта нет профиля)
export const getMe = () => api.get('/me/');

// PATCH /api/me/ → обновлённый Own-профиль. Разрешены: first_name, last_name, gender, country,
// region, city, status, school, university, field, year_level, bio, interests, languages, goals, contacts
export const updateMe = (changes) => api.patch('/me/', changes);
