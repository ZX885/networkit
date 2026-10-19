// Управление аккаунтом (docs/SPEC.md §3.4–3.5). Ошибки приходят как ApiError (lib/apiClient.js).
import { api } from '../lib/apiClient.js';

// Сброс пароля: ответ всегда 202 { status: 'sent' }, есть ли такой адрес — не раскрывается
export const requestPasswordReset = (email) => api.post('/auth/password-reset/', { email });

// По ссылке из письма → 200 { status: 'password_changed' }; 400 invalid_token; слабый пароль → 400 по полю new_password
export const confirmPasswordReset = ({ uid, token, newPassword }) =>
  api.post('/auth/password-reset/confirm/', { uid, token, new_password: newPassword });

// Смена пароля вошедшим → 204. 400: old_password (incorrect), new_password (too_weak, same_as_old, …)
export const changePassword = ({ oldPassword, newPassword }) =>
  api.post('/auth/password/change/', { old_password: oldPassword, new_password: newPassword });

// Смена email → 202 { status: 'verification_sent' } (одинаково, даже если адрес занят). 400: password (incorrect)
export const requestEmailChange = ({ newEmail, password }) =>
  api.post('/auth/email/change/', { new_email: newEmail, password });

// По ссылке из письма → 200 { status: 'email_changed' }; 400 invalid_token
export const confirmEmailChange = (token) => api.post('/auth/email/change/confirm/', { token });

// Удаление аккаунта → 204 (сессия закрыта). 400: password (incorrect)
export const deleteAccount = (password) => api.delete('/me/', { body: { password } });
