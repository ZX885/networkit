import { texts } from '../texts/en.js';

// Текст из словаря: строка или функция от лимитов сервера (meta.limits), например «at least 13 years»
const resolve = (text, limits) => (typeof text === 'function' ? text(limits ?? {}) : text);

// Текст ошибки поля от сервера: по коду из словаря, иначе — message сервера.
// limits — meta.limits (нужны сообщениям с числами: возраст, максимумы)
export function fieldErrorText(item, limits) {
  return resolve(texts.apiErrors[item.code], limits) ?? item.message;
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
export function errorText(value, limits) {
  if (!value) return undefined;
  if (typeof value === 'string') return resolve(texts.validation[value], limits) ?? value;
  return fieldErrorText(value, limits);
}

// Текст первой серверной ошибки поля формы (ApiError.fields[name]) или undefined, если по полю ошибки нет
export function serverFieldError(error, name, limits) {
  const item = error.fields?.[name]?.[0];
  return item ? fieldErrorText(item, limits) : undefined;
}
