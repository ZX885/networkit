import {
  CITY_MAX,
  EMAIL_MAX,
  MAX_AGE,
  NAME_MAX,
  PASSWORD_MAX,
  PASSWORD_MIN,
  REGION_MAX,
  RESERVED_USERNAMES,
  SCHOOL_MAX,
  UNIVERSITY_MAX,
  USERNAME_REGEX,
  YEAR_LEVEL_MAX,
} from '../../constants/rules.js';
import { getAge, isRealDate } from '../../lib/date.js';

// Правила проверки полей регистрации (docs/SPEC.md §5). Функции возвращают объект
// { поле: 'код ошибки' }; тексты по кодам лежат в texts.validation. Пустой объект — всё верно.

const NAME_REGEX = /^\p{L}[\p{L}\p{M} '.-]*$/u; // буквы любого алфавита, пробел, дефис, апостроф, точка
export const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const TELEGRAM_REGEX = /^@?[A-Za-z0-9_]{5,32}$/;
const INSTAGRAM_REGEX = /^@?[A-Za-z0-9._]{1,30}$/;
const WHATSAPP_REGEX = /^\+[1-9]\d{6,14}$/;
const LINKEDIN_REGEX = /^(https?:\/\/)?(www\.)?(linkedin\.com\/in\/)?[\w%-]{3,100}\/?$/i;

const isEmpty = (value) => String(value).trim() === '';

// ── Дата рождения из трёх полей ──

// Возвращает { year, month, day } или null, если поля пусты или не числа
export function parseBirthDate({ birthDay, birthMonth, birthYear }) {
  if (!/^\d{1,2}$/.test(birthDay) || !/^\d{1,2}$/.test(birthMonth) || !/^\d{4}$/.test(birthYear)) {
    return null;
  }
  return { year: Number(birthYear), month: Number(birthMonth), day: Number(birthDay) };
}

// Возраст по данным формы; null, если дата неполная или несуществующая
export function getAgeFromData(data) {
  const date = parseBirthDate(data);
  if (!date || !isRealDate(date.year, date.month, date.day)) return null;
  return getAge(date.year, date.month, date.day);
}

function checkBirthDate(data, limits) {
  if (isEmpty(data.birthDay) || isEmpty(data.birthMonth) || isEmpty(data.birthYear)) {
    return 'dateRequired';
  }
  const date = parseBirthDate(data);
  if (!date || !isRealDate(date.year, date.month, date.day)) return 'dateInvalid';
  if (new Date(date.year, date.month - 1, date.day) > new Date()) return 'dateFuture';
  const age = getAge(date.year, date.month, date.day);
  if (age < limits.min_age) return 'tooYoung';
  if (age > MAX_AGE) return 'dateTooOld';
  return null;
}

// ── Проверки отдельных полей: возвращают код ошибки или null ──

function checkName(value) {
  const name = value.trim();
  if (!name) return 'required';
  return NAME_REGEX.test(name) && name.length <= NAME_MAX ? null : 'nameInvalid';
}

function checkUsername(value, status) {
  const username = value.trim();
  if (!username) return 'required';
  if (!USERNAME_REGEX.test(username) || username.includes('__')) return 'usernameFormat';
  if (RESERVED_USERNAMES.includes(username)) return 'usernameReserved';
  if (status === 'taken') return 'usernameTaken';
  if (status === 'reserved') return 'usernameReserved';
  if (status === 'checking') return 'usernameChecking';
  return null;
}

function checkEmail(value) {
  const email = value.trim();
  if (!email) return 'required';
  return EMAIL_REGEX.test(email) && email.length <= EMAIL_MAX ? null : 'emailInvalid';
}

function checkPassword(value) {
  if (!value) return 'required';
  if (value.length < PASSWORD_MIN) return 'passwordShort';
  return value.length > PASSWORD_MAX ? 'passwordLong' : null;
}

const checkRequired = (value) => (isEmpty(value) ? 'required' : null);
const checkMaxLength = (value, max) => (value.trim().length > max ? 'tooLong' : null);
const checkRequiredMax = (value, max) => checkRequired(value) || checkMaxLength(value, max);

// Необязательный контакт: пустой — ок, иначе должен подойти под формат
function checkContact(value, regex, errorCode, normalize = (v) => v) {
  if (isEmpty(value)) return null;
  return regex.test(normalize(value.trim())) ? null : errorCode;
}

const checkCount = (list, max, errorCode) => (list.length > max ? errorCode : null);

// ── Шаги ──

const stepValidators = {
  1: (d, { usernameStatus, limits }) => ({
    firstName: checkName(d.firstName),
    lastName: checkName(d.lastName),
    username: checkUsername(d.username, usernameStatus),
    email: checkEmail(d.email),
    password: checkPassword(d.password),
    birthDate: checkBirthDate(d, limits),
  }),
  2: (d) => ({
    country: checkRequired(d.country),
    region: checkMaxLength(d.region, REGION_MAX),
    city: checkRequiredMax(d.city, CITY_MAX),
  }),
  3: (d) => ({
    status: checkRequired(d.status),
    school: checkMaxLength(d.school, SCHOOL_MAX),
    university: checkMaxLength(d.university, UNIVERSITY_MAX),
    field: checkRequired(d.field),
    yearLevel: checkMaxLength(d.yearLevel, YEAR_LEVEL_MAX),
  }),
  4: (d, { limits }) => ({
    interests: checkCount(d.interests, limits.interests_max, 'tooManyInterests'),
  }),
  5: (d, { limits }) => ({
    languages: checkCount(d.languages, limits.languages_max, 'tooManyLanguages'),
  }),
  6: (d, { limits }) => ({ bio: checkMaxLength(d.bio, limits.bio_max) }),
  7: (d, { limits }) => ({ goals: checkCount(d.goals, limits.goals_max, 'tooManyGoals') }),
  8: (d, { isAdult }) => ({
    // Контакты проверяем только у совершеннолетних: у остальных поля не показываются
    telegram: isAdult ? checkContact(d.telegram, TELEGRAM_REGEX, 'telegramInvalid') : null,
    instagram: isAdult ? checkContact(d.instagram, INSTAGRAM_REGEX, 'instagramInvalid') : null,
    whatsapp: isAdult
      ? checkContact(d.whatsapp, WHATSAPP_REGEX, 'whatsappInvalid', (v) =>
          v.replace(/[\s()-]/g, ''),
        )
      : null,
    linkedin: isAdult ? checkContact(d.linkedin, LINKEDIN_REGEX, 'linkedinInvalid') : null,
    publicEmail: isAdult ? checkContact(d.publicEmail, EMAIL_REGEX, 'emailInvalid') : null,
    acceptedTerms: d.acceptedTerms ? null : 'termsRequired',
  }),
};

// Проверка одного шага. usernameStatus — результат проверки занятости имени (нужен шагу 1);
// limits — meta.limits с сервера (возраст и максимумы).
export function validateStep(step, data, usernameStatus, limits) {
  const context = {
    usernameStatus,
    limits,
    isAdult: (getAgeFromData(data) ?? 0) >= limits.adult_age,
  };
  const result = stepValidators[step](data, context);
  return Object.fromEntries(Object.entries(result).filter(([, code]) => code));
}

// Проверка всех шагов перед отправкой: номер первого неверного шага или 0
export function findInvalidStep(data, usernameStatus, limits) {
  for (let step = 1; step <= 8; step += 1) {
    if (Object.keys(validateStep(step, data, usernameStatus, limits)).length > 0) return step;
  }
  return 0;
}
