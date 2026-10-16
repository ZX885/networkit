import { useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import useMeta from '../../../api/useMeta.js';
import { SHOW_COUNTRY_FILTER } from '../../../constants/features.js';

// Фильтр стран скрыт флагом SHOW_COUNTRY_FILTER: тогда country из адреса игнорируется и не отправляется
export const FILTER_KEYS = [
  ...(SHOW_COUNTRY_FILTER ? ['country'] : []),
  'city',
  'field',
  'status',
  'goal',
  'language',
];

// Справочник, из которого берутся допустимые значения каждого фильтра
const META_LIST = {
  country: 'countries',
  city: 'cities',
  field: 'fields',
  status: 'statuses',
  goal: 'goals',
  language: 'languages',
};

// Поиск, фильтры и страница лежат в адресе (/discover?q=&city=&field=&…&page=), поэтому «Назад» работает.
// update(patch) меняет часть параметров; любое изменение, кроме номера страницы, сбрасывает страницу.
// Значение фильтра, которого нет в справочнике сервера (например, город, убранный из meta.cities),
// игнорируется: в params его нет (на сервер не уходит), а из адреса оно убирается через replace.
// Пока справочники не загружены, значения не проверяются. cleanUrl: false — не трогать адрес
// (для второго экземпляра хука на той же странице).
export default function useDiscoverParams({ cleanUrl = true } = {}) {
  const [searchParams, setSearchParams] = useSearchParams();
  const { meta } = useMeta();

  const params = { q: searchParams.get('q') ?? '', page: 1 };
  const unknownKeys = [];
  FILTER_KEYS.forEach((key) => {
    const value = searchParams.get(key) ?? '';
    const known = !meta || !value || meta[META_LIST[key]]?.some((item) => item.code === value);
    params[key] = known ? value : '';
    if (!known) unknownKeys.push(key);
  });
  const page = Number.parseInt(searchParams.get('page') ?? '', 10);
  params.page = Number.isInteger(page) && page > 0 ? page : 1;

  // options.replace — не добавлять запись в историю (набор текста в поиске)
  function update(patch, { replace = false } = {}) {
    const next = { ...params, ...(patch.page ? {} : { page: 1 }), ...patch };
    const query = {};
    Object.entries(next).forEach(([key, value]) => {
      if (value && !(key === 'page' && value === 1)) query[key] = String(value);
    });
    setSearchParams(query, { replace });
  }

  // Лишние параметры убираем из адреса, не добавляя запись в историю («Назад» работает как раньше)
  const unknown = unknownKeys.join(',');
  useEffect(() => {
    if (!cleanUrl || !unknown) return;
    const next = new URLSearchParams(searchParams);
    unknown.split(',').forEach((key) => next.delete(key));
    setSearchParams(next, { replace: true });
  }, [cleanUrl, unknown]); // eslint-disable-line react-hooks/exhaustive-deps

  return { params, update };
}
