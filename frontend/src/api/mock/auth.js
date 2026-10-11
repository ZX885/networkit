import { MockApiError, sleep } from './delay.js';

// MOCK: ответы «сервера» для входа и регистрации. Настоящие endpoint'ы — docs/SPEC.md §3.2–3.4.
const DEMO_EMAIL = 'demo@networkit.test';
const DEMO_PASSWORD = 'demo12345';
const TAKEN_USERNAMES = ['admin', 'demo_user', 'test'];

// POST /api/auth/login/ — успех только для демо-пользователя
export async function login(email, password) {
  await sleep(800);
  if (email.trim().toLowerCase() === DEMO_EMAIL && password === DEMO_PASSWORD) {
    return { firstName: 'Demo' };
  }
  throw new MockApiError('invalid_credentials');
}

// POST /api/auth/password-reset/ — сервер всегда отвечает одинаково
export async function requestPasswordReset() {
  await sleep(600);
  return { status: 'sent' };
}

// GET /api/auth/username-available/
export async function checkUsername(username) {
  await sleep(500);
  return { available: !TAKEN_USERNAMES.includes(username) };
}

// POST /api/auth/register/ — всегда «письмо отправлено» (даже если email занят)
export async function register(payload) {
  await sleep(900);
  return { status: 'verification_sent', email: payload.email };
}
