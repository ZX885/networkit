import { toIsoDate } from '../../lib/date.js';
import { getAgeFromData, parseBirthDate } from './validation.js';

const clean = (value) => value.trim();
const withoutAt = (value) => clean(value).replace(/^@/, '');

// Собирает тело запроса POST /api/auth/register/ из данных формы (поля — как в backend).
// Контакты отправляются только совершеннолетним; телефона и field_other нет.
export function buildRegisterPayload(data, limits) {
  const { year, month, day } = parseBirthDate(data);
  const isAdult = (getAgeFromData(data) ?? 0) >= limits.adult_age;

  const payload = {
    email: clean(data.email).toLowerCase(),
    password: data.password,
    username: clean(data.username).toLowerCase(),
    first_name: clean(data.firstName),
    last_name: clean(data.lastName),
    date_of_birth: toIsoDate(year, month, day),
    gender: data.gender,
    country: data.country,
    region: clean(data.region),
    city: clean(data.city),
    status: data.status,
    school: clean(data.school),
    university: clean(data.university),
    field: data.field,
    year_level: clean(data.yearLevel),
    bio: data.bio.trim(),
    interests: data.interests,
    languages: data.languages,
    goals: data.goals,
    accepted_terms: data.acceptedTerms,
  };
  // Несовершеннолетним ключ contacts не отправляем (сервер отклонит null и любые контакты)
  if (isAdult) {
    payload.contacts = {
      telegram: withoutAt(data.telegram),
      instagram: withoutAt(data.instagram),
      whatsapp: data.whatsapp.replace(/[\s()-]/g, ''),
      linkedin: clean(data.linkedin),
      public_email: clean(data.publicEmail),
    };
  }
  return payload;
}
