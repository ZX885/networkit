// Запросы авторизации к backend (docs/SPEC.md §3.2–3.4; источник правды — код backend/apps/users).
import { api, ensureCsrf } from '../lib/apiClient.js';

// GET /api/auth/csrf/ — cookie csrftoken (apiClient вызывает сам; нужен, если токен нужен заранее)
export const csrf = () => ensureCsrf();

// GET /api/auth/username-available/?username= → { available, reason? }
export const checkUsername = (username, { signal } = {}) =>
  api.get('/auth/username-available/', { params: { username }, signal });

// POST /api/auth/register/ → 201 { status: 'verification_sent', email }
export const register = (payload) => api.post('/auth/register/', payload);

// POST /api/auth/verify-email/ → 200 { status: 'verified' }; токен одноразовый
export const verifyEmail = (token) => api.post('/auth/verify-email/', { token });

// POST /api/auth/resend-verification/ → 202 { status: 'sent' } (всегда, даже если email неизвестен)
export const resendVerification = (email) => api.post('/auth/resend-verification/', { email });

// POST /api/auth/login/ → 200 Own-профиль; создаёт сессию (cookie)
export const login = (email, password) => api.post('/auth/login/', { email, password });

// POST /api/auth/logout/ → 204
export const logout = () => api.post('/auth/logout/');
