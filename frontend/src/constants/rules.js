// Правила и лимиты (по docs/SPEC.md §5). Сервер проверяет всё то же самое повторно.
export const MIN_AGE = 13; // минимальный возраст регистрации
export const ADULT_AGE = 18; // с этого возраста доступны контакты
export const MAX_AGE = 100;

export const PASSWORD_MIN = 8;
export const PASSWORD_MAX = 128;
export const NAME_MAX = 60;
export const BIO_MAX = 300;
export const CITY_MAX = 100;
export const REGION_MAX = 100;
export const SCHOOL_MAX = 100;
export const UNIVERSITY_MAX = 120;
export const FIELD_OTHER_MAX = 60;
export const YEAR_LEVEL_MAX = 40;
export const EMAIL_MAX = 254;

export const INTERESTS_MAX = 10;
export const LANGUAGES_MAX = 10;
export const GOALS_MAX = 8;

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
