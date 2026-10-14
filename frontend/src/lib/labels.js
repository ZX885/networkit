// Названия по кодам. Списки берутся из справочников сервера (api/useMeta.js → meta.countries и т.д.).

// Название по коду; неизвестный код показываем как есть
export function labelOf(list, code) {
  return list.find((item) => item.code === code)?.label ?? code;
}

export function labelsOf(list, codes = []) {
  return codes.map((code) => labelOf(list, code));
}

// «Oct 2026» из даты ISO ('2026-10-10T08:15:30Z') или месяца ('2026-09')
export function formatMonthYear(value) {
  if (!value) return '';
  const date = new Date(value.length === 7 ? `${value}-01T00:00:00` : value);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
}

// «Jane Doe»
export const fullName = (person) => `${person.first_name} ${person.last_name}`.trim();

// «Tashkent, Uzbekistan» (скрытые приватностью части пропускаются); countries — meta.countries
export function formatPlace(person, countries) {
  return [person.city, person.country && labelOf(countries, person.country)]
    .filter(Boolean)
    .join(', ');
}
