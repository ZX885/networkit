import { apiErrorText, fieldErrorText } from '../../lib/apiErrors.js';
import { texts } from '../../texts/en.js';

const t = texts.messages.errors;

// Ошибка отправки сообщения или запроса → обычный текст (без технических кодов).
// 409 (диалог уже есть, запрос уже отправлен…), 429 (лимиты) и ошибки сети берутся из словаря
// texts.apiErrors; maxLength — лимит длины из /api/meta/ (request_max или message_max).
export function sendErrorText(error, maxLength) {
  const bodyError = error.fields?.body?.[0];
  if (bodyError) {
    if (bodyError.code === 'required') return t.empty;
    if (bodyError.code === 'too_long' && maxLength) return t.tooLong(maxLength);
    return fieldErrorText(bodyError);
  }
  if (error.status === 404) return t.notAvailable;
  return apiErrorText(error);
}

// Диалог из ответа 409 (куда вести человека): conversation_exists → Chats, request_pending → Sent,
// incoming_request_exists → Requests
const BOX_BY_CODE = {
  conversation_exists: 'chats',
  request_pending: 'sent',
  incoming_request_exists: 'requests',
};

export function conversationLink(error) {
  const box = BOX_BY_CODE[error.code];
  if (!box || !error.conversationId) return null;
  return `/messages/${error.conversationId}?box=${box}`;
}
