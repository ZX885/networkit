// Страны: код ISO 3166-1 alpha-2 + название. Состав — CTRS из legacy + Kyrgyzstan, Tajikistan,
// Turkmenistan (Центральная Азия). Список отсортирован по алфавиту.
// prettier-ignore
const COUNTRY_PAIRS = [
  ['AF', 'Afghanistan'], ['AL', 'Albania'], ['DZ', 'Algeria'], ['AR', 'Argentina'],
  ['AM', 'Armenia'], ['AU', 'Australia'], ['AT', 'Austria'], ['AZ', 'Azerbaijan'],
  ['BD', 'Bangladesh'], ['BY', 'Belarus'], ['BE', 'Belgium'], ['BR', 'Brazil'],
  ['CA', 'Canada'], ['CL', 'Chile'], ['CN', 'China'], ['CO', 'Colombia'],
  ['HR', 'Croatia'], ['CZ', 'Czech Republic'], ['DK', 'Denmark'], ['EG', 'Egypt'],
  ['FI', 'Finland'], ['FR', 'France'], ['GE', 'Georgia'], ['DE', 'Germany'],
  ['GH', 'Ghana'], ['GR', 'Greece'], ['HU', 'Hungary'], ['IN', 'India'],
  ['ID', 'Indonesia'], ['IR', 'Iran'], ['IE', 'Ireland'], ['IT', 'Italy'],
  ['JP', 'Japan'], ['KZ', 'Kazakhstan'], ['KE', 'Kenya'], ['KG', 'Kyrgyzstan'],
  ['MY', 'Malaysia'], ['MX', 'Mexico'], ['MA', 'Morocco'], ['NL', 'Netherlands'],
  ['NZ', 'New Zealand'], ['NG', 'Nigeria'], ['NO', 'Norway'], ['PK', 'Pakistan'],
  ['PS', 'Palestine'], ['PE', 'Peru'], ['PH', 'Philippines'], ['PL', 'Poland'],
  ['PT', 'Portugal'], ['RO', 'Romania'], ['RU', 'Russia'], ['SA', 'Saudi Arabia'],
  ['RS', 'Serbia'], ['SG', 'Singapore'], ['KR', 'South Korea'], ['ES', 'Spain'],
  ['SE', 'Sweden'], ['CH', 'Switzerland'], ['TJ', 'Tajikistan'], ['TR', 'Turkey'],
  ['TM', 'Turkmenistan'], ['UA', 'Ukraine'], ['AE', 'United Arab Emirates'],
  ['GB', 'United Kingdom'], ['US', 'United States'], ['UZ', 'Uzbekistan'], ['VN', 'Vietnam'],
];

export const COUNTRIES = COUNTRY_PAIRS.map(([code, label]) => ({ code, label })).sort((a, b) =>
  a.label.localeCompare(b.label),
);
