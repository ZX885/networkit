// Правила и лимиты (по docs/SPEC.md §5). Сервер проверяет всё то же самое повторно.
// Здесь только то, чего нет в GET /api/meta/. Возраст (min_age, adult_age) и максимумы
// (bio_max, interests_max, languages_max, goals_max) берутся из meta.limits (api/useMeta.js).
export const MAX_AGE = 100;

export const PASSWORD_MIN = 8;
export const PASSWORD_MAX = 128;
export const NAME_MAX = 60;
export const CITY_MAX = 100;
export const REGION_MAX = 100;
export const SCHOOL_MAX = 100;
export const UNIVERSITY_MAX = 120;
export const YEAR_LEVEL_MAX = 40;
export const EMAIL_MAX = 254;

export const USERNAME_REGEX = /^[a-z][a-z0-9_]{2,29}$/;
// Зарезервированные имена (не должны совпадать с адресами сайта)
export const RESERVED_USERNAMES = [
  'admin',
  'api',
  'me',
  'settings',
  'login',
  'register',
  'support',
  'staff',
  'networkit',
];
