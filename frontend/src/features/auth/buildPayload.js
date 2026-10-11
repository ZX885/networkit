import { ADULT_AGE } from '../../constants/rules.js';
import { toIsoDate } from '../../lib/date.js';
import { getAgeFromData, parseBirthDate } from './validation.js';

const clean = (value) => value.trim();
const withoutAt = (value) => clean(value).replace(/^@/, '');

// Собирает тело запроса регистрации из данных формы (формат — docs/SPEC.md §3.2).
// Контакты отправляются только совершеннолетним.
export function buildRegisterPayload(data) {
  const { year, month, day } = parseBirthDate(data);
  const isAdult = (getAgeFromData(data) ?? 0) >= ADULT_AGE;

  return {
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
    field_other: data.field === 'other' ? clean(data.fieldOther) : '',
    year_level: clean(data.yearLevel),
    bio: data.bio.trim(),
    interests: data.interests,
    languages: data.languages,
    goals: data.goals,
    contacts: isAdult
      ? {
          telegram: withoutAt(data.telegram),
          instagram: withoutAt(data.instagram),
          whatsapp: data.whatsapp.replace(/[\s()-]/g, ''),
          linkedin: clean(data.linkedin),
          public_email: clean(data.publicEmail),
        }
      : null,
    accepted_terms: data.acceptedTerms,
  };
}
