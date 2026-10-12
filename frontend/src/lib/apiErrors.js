import { texts } from '../texts/en.js';

// Текст ошибки поля от сервера: по коду из словаря, иначе — message сервера
export function fieldErrorText(item) {
  return texts.apiErrors[item.code] ?? item.message;
}

// Текст общей ошибки запроса (ApiError); для лимита подставляет секунды ожидания
export function apiErrorText(error) {
  if (error.code === 'throttled' && error.retryAfter) {
    return texts.auth.throttled(error.retryAfter);
  }
  const known = texts.apiErrors[error.code];
  return typeof known === 'string' ? known : (error.message ?? texts.apiErrors.unknown);
}

// Ошибка поля формы бывает клиентской (строка-код из validation.js) или серверной ({code, message}).
// Возвращает текст для показа или undefined, если ошибки нет.
export function errorText(value) {
  if (!value) return undefined;
  if (typeof value === 'string') return texts.validation[value] ?? value;
  return fieldErrorText(value);
}
