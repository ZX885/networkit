// Справочники и лимиты с сервера: GET /api/meta/ (docs/SPEC.md §3.1). Единственный источник
// стран, направлений, статусов, интересов, языков, целей и лимитов (bio_max, min_age, adult_age…).
// Загружается один раз за сессию вкладки и хранится в памяти; при ошибке кэш не заполняется,
// и следующая попытка (кнопка «Try again») запросит заново.
import { api } from '../lib/apiClient.js';
import { texts } from '../texts/en.js';

const LISTS = [
  'countries',
  'cities',
  'fields',
  'statuses',
  'interests',
  'languages',
  'goals',
  'genders',
];
// Без этих полей страницы работать не могут (cities и genders необязательны: пустой список допустим)
const REQUIRED = ['countries', 'fields', 'statuses', 'interests', 'languages', 'goals', 'limits'];

// Ответ сервера → безопасный вид: все списки — массивы, limits — объект. Значения по умолчанию
// заданы только здесь, компоненты их не повторяют.
function normalizeMeta(data) {
  const meta = { ...data };
  LISTS.forEach((key) => {
    if (!Array.isArray(meta[key])) meta[key] = [];
  });
  if (!meta.limits || typeof meta.limits !== 'object') meta.limits = {};
  if (typeof meta.country_cities_default !== 'string') meta.country_cities_default = '';
  return meta;
}

// Есть ли в ответе обязательные поля нужного вида
function isComplete(data) {
  if (!data || typeof data !== 'object') return false;
  return REQUIRED.every((key) =>
    key === 'limits'
      ? data.limits && typeof data.limits === 'object'
      : Array.isArray(data[key]) && data[key].length > 0,
  );
}

let cached = null;
let pending = null;

// Уже загруженные справочники или null
export const getCachedMeta = () => cached;

export function loadMeta() {
  if (cached) return Promise.resolve(cached);
  if (!pending) {
    pending = api.get('/meta/').then(
      (data) => {
        pending = null;
        if (!isComplete(data)) throw new Error(texts.app.metaIncomplete);
        cached = normalizeMeta(data);
        return cached;
      },
      (error) => {
        pending = null;
        throw error;
      },
    );
  }
  return pending;
}
