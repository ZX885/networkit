// Обёртка над fetch для запросов к backend (/api). Сессия — cookie same-origin (JS её не видит),
// защита от CSRF — заголовок X-CSRFToken со значением cookie csrftoken.
// Тела запросов и ответов нигде не логируются (там пароли и персональные данные).

const SAFE_METHODS = ['GET', 'HEAD', 'OPTIONS'];
const BASE = '/api';

// Ошибка API в едином виде (формат backend: docs/SPEC.md §3.0)
export class ApiError extends Error {
  constructor(status, error = {}) {
    super(error.message || 'Request failed');
    this.status = status;
    this.code = error.code || 'unknown';
    this.fields = error.fields || {}; // { поле: [{ code, message }] }
    this.nonFieldErrors = error.non_field_errors || []; // [{ code, message }]
    this.retryAfter = error.retry_after ?? null; // секунды (код throttled)
  }
}

function readCookie(name) {
  const entry = document.cookie.split('; ').find((item) => item.startsWith(`${name}=`));
  return entry ? decodeURIComponent(entry.slice(name.length + 1)) : '';
}

// Один раз получаем cookie csrftoken (дальше она обновляется ответами сервера)
let csrfPromise = null;
export function ensureCsrf() {
  if (!csrfPromise) {
    csrfPromise = request('GET', '/auth/csrf/').catch((error) => {
      csrfPromise = null; // при сбое попробуем снова при следующем запросе
      throw error;
    });
  }
  return csrfPromise;
}

// Вызывается, когда сервер ответил 401 (сессия закончилась); подписывается AuthProvider
let unauthorizedHandler = null;
export function setUnauthorizedHandler(handler) {
  unauthorizedHandler = handler;
}

async function request(method, path, { body, params, signal } = {}, retried = false) {
  const unsafe = !SAFE_METHODS.includes(method);
  if (unsafe) await ensureCsrf();

  const query = params ? `?${new URLSearchParams(params)}` : '';
  const headers = { Accept: 'application/json' };
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (unsafe) headers['X-CSRFToken'] = readCookie('csrftoken');

  let response;
  try {
    response = await fetch(`${BASE}${path}${query}`, {
      method,
      headers,
      credentials: 'same-origin',
      signal,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch (error) {
    if (error.name === 'AbortError') throw error; // запрос отменён нами — это не ошибка сети
    throw new ApiError(0, { code: 'network_error', message: "Can't reach the server." });
  }

  if (response.status === 204) return null;
  const data = await response.json().catch(() => null);
  // Ответ пришёл, но это не JSON нашего API (HTML-страница ошибки, заглушка прокси): это
  // server_error. network_error — только когда ответа не было совсем (fetch упал).
  if (response.ok) {
    if (data === null) throw new ApiError(response.status, { code: 'server_error' });
    return data;
  }
  const error = new ApiError(response.status, data?.error || { code: 'server_error' });

  // CSRF-токен мог устареть: берём новый и повторяем запрос один раз
  if (error.code === 'csrf_failed' && !retried) {
    csrfPromise = null;
    await ensureCsrf();
    return request(method, path, { body, params, signal }, true);
  }
  if (error.status === 401 && unauthorizedHandler) unauthorizedHandler(error);
  throw error;
}

export const api = {
  get: (path, options) => request('GET', path, options),
  post: (path, body, options) => request('POST', path, { ...options, body }),
  put: (path, body, options) => request('PUT', path, { ...options, body }),
  patch: (path, body, options) => request('PATCH', path, { ...options, body }),
  delete: (path, options) => request('DELETE', path, options),
};
