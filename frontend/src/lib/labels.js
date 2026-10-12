import { COUNTRIES } from '../constants/countries.js';
import { FIELDS } from '../constants/fields.js';
import { STATUSES } from '../constants/options.js';

// Показываем люди названия, а не коды: code → label по справочнику (неизвестный код — как есть)
export function labelOf(list, code) {
  return list.find((item) => item.code === code)?.label ?? code;
}

export function labelsOf(list, codes = []) {
  return codes.map((code) => labelOf(list, code));
}

export const countryLabel = (code) => labelOf(COUNTRIES, code);
export const statusLabel = (code) => labelOf(STATUSES, code);
export const fieldLabel = (code) => labelOf(FIELDS, code);

// «Oct 2026» из даты ISO ('2026-10-10T08:15:30Z') или месяца ('2026-09')
export function formatMonthYear(value) {
  if (!value) return '';
  const date = new Date(value.length === 7 ? `${value}-01T00:00:00` : value);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
}

// «Jane Doe»
export const fullName = (person) => `${person.first_name} ${person.last_name}`.trim();

// «Tashkent, Uzbekistan» (скрытые приватностью части пропускаются)
export function formatPlace(person) {
  return [person.city, person.country && countryLabel(person.country)].filter(Boolean).join(', ');
}
