import { useSearchParams } from 'react-router-dom';

export const FILTER_KEYS = ['country', 'field', 'status', 'goal', 'language'];

// Поиск, фильтры и страница лежат в адресе (/discover?q=&country=&…&page=), поэтому «Назад» работает.
// update(patch) меняет часть параметров; любое изменение, кроме номера страницы, сбрасывает страницу.
export default function useDiscoverParams() {
  const [searchParams, setSearchParams] = useSearchParams();

  const params = { q: searchParams.get('q') ?? '', page: 1 };
  FILTER_KEYS.forEach((key) => {
    params[key] = searchParams.get(key) ?? '';
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

  return { params, update };
}
