import { apiErrorText } from '../../lib/apiErrors.js';
import { texts } from '../../texts/en.js';

const t = texts.moderation.errors;

// Ошибка жалобы или блокировки → обычный текст (без кодов): 429 с временем ожидания, лимит блокировок,
// «человек недоступен» (404), сеть. maxLength — details_max из /api/meta/.
export function moderationErrorText(error, maxLength) {
  const fields = error.fields ?? {};
  if (fields.reason) return t.chooseReason;
  if (fields.details?.[0]?.code === 'too_long' && maxLength) return t.tooLong(maxLength);
  if (error.status === 404) return t.notAvailable;
  return apiErrorText(error);
}
