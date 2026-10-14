// Справочники и лимиты с сервера: GET /api/meta/ (docs/SPEC.md §3.1). Единственный источник
// стран, направлений, статусов, интересов, языков, целей и лимитов (bio_max, min_age, adult_age…).
// Загружается один раз за сессию вкладки и хранится в памяти; при ошибке кэш не заполняется,
// и следующая попытка (кнопка «Try again») запросит заново.
import { api } from '../lib/apiClient.js';

let cached = null;
let pending = null;

// Уже загруженные справочники или null
export const getCachedMeta = () => cached;

export function loadMeta() {
  if (cached) return Promise.resolve(cached);
  if (!pending) {
    pending = api.get('/meta/').then(
      (data) => {
        cached = data;
        pending = null;
        return data;
      },
      (error) => {
        pending = null;
        throw error;
      },
    );
  }
  return pending;
}
