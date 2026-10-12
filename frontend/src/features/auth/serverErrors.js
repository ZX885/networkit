// Раскладывает ошибки валидации сервера (ApiError.fields) по полям формы регистрации и шагам мастера.
// Ключи сервера — имена из backend (snake_case; вложенные через точку: contacts.telegram, interests.0).

// Поле сервера → поле формы
const SERVER_TO_FORM = {
  first_name: 'firstName',
  last_name: 'lastName',
  username: 'username',
  email: 'email',
  password: 'password',
  date_of_birth: 'birthDate',
  gender: 'gender',
  country: 'country',
  region: 'region',
  city: 'city',
  status: 'status',
  school: 'school',
  university: 'university',
  field: 'field',
  year_level: 'yearLevel',
  interests: 'interests',
  languages: 'languages',
  goals: 'goals',
  bio: 'bio',
  contacts: 'contacts',
  'contacts.telegram': 'telegram',
  'contacts.instagram': 'instagram',
  'contacts.whatsapp': 'whatsapp',
  'contacts.linkedin': 'linkedin',
  'contacts.public_email': 'publicEmail',
  accepted_terms: 'acceptedTerms',
};

// Поле формы → номер шага мастера
const FORM_STEP = {
  firstName: 1,
  lastName: 1,
  username: 1,
  email: 1,
  password: 1,
  birthDate: 1,
  gender: 1,
  country: 2,
  region: 2,
  city: 2,
  status: 3,
  school: 3,
  university: 3,
  field: 3,
  yearLevel: 3,
  interests: 4,
  languages: 5,
  bio: 6,
  goals: 7,
  contacts: 8,
  telegram: 8,
  instagram: 8,
  whatsapp: 8,
  linkedin: 8,
  publicEmail: 8,
  acceptedTerms: 8,
};

// Ключ сервера → поле формы. Ошибки элементов списка (interests.0) относим к самому списку.
function toFormField(serverKey) {
  if (SERVER_TO_FORM[serverKey]) return SERVER_TO_FORM[serverKey];
  const listRoot = serverKey.split('.')[0];
  return SERVER_TO_FORM[listRoot] ?? null;
}

// Возвращает { fieldErrors, firstStep, unmapped }:
//   fieldErrors — { поле формы: { code, message } } (показывается первая ошибка поля),
//   firstStep — самый ранний шаг с ошибкой (или 0, если полевых ошибок нет),
//   unmapped — ошибки полей, которых нет в форме (покажем общим сообщением).
export function mapServerErrors(fields) {
  const fieldErrors = {};
  const unmapped = [];
  Object.entries(fields).forEach(([serverKey, items]) => {
    const formField = toFormField(serverKey);
    if (formField && items.length > 0) {
      fieldErrors[formField] ??= items[0];
    } else {
      unmapped.push(...items);
    }
  });
  const steps = Object.keys(fieldErrors).map((name) => FORM_STEP[name]);
  return { fieldErrors, firstStep: steps.length > 0 ? Math.min(...steps) : 0, unmapped };
}
