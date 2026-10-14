import { api } from '../lib/apiClient.js';

// GET /api/me/ → Own-профиль (401, если не вошёл; 404, если у аккаунта нет профиля)
export const getMe = () => api.get('/me/');

// PATCH /api/me/ → обновлённый Own-профиль. Разрешены: first_name, last_name, gender, country,
// region, city, status, school, university, field, year_level, bio, interests, languages, goals, contacts
export const updateMe = (changes) => api.patch('/me/', changes);

// GET /api/me/privacy/ → { show_location, show_university, show_contacts, show_in_search, show_join_date }
export const getPrivacy = () => api.get('/me/privacy/');

// PATCH /api/me/privacy/ → актуальные 5 флагов. Младше 18 лет show_contacts: true → 400 not_allowed_for_minors
export const updatePrivacy = (changes) => api.patch('/me/privacy/', changes);
