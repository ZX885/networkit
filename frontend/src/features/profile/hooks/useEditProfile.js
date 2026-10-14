import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { updateMe } from '../../../api/me.js';
import useAuth from '../../../app/providers/useAuth.js';
import useToast from '../../../components/ui/useToast.js';
import { apiErrorText, fieldErrorText } from '../../../lib/apiErrors.js';
import { texts } from '../../../texts/en.js';

const t = texts.editProfile;
const TEXT_FIELDS = [
  'first_name',
  'last_name',
  'field',
  'university',
  'country',
  'city',
  'year_level',
  'bio',
];
const LIST_FIELDS = ['interests', 'languages', 'goals'];
const CONTACT_KEYS = ['telegram', 'instagram', 'whatsapp', 'linkedin', 'public_email'];

const fromUser = (user) => ({
  first_name: user.first_name,
  last_name: user.last_name,
  field: user.field,
  university: user.university ?? '',
  country: user.country,
  city: user.city ?? '',
  year_level: user.year_level ?? '',
  bio: user.bio ?? '',
  contacts: { ...user.contacts },
  interests: user.interests ?? [],
  languages: user.languages ?? [],
  goals: user.goals ?? [],
});

// Только изменённые поля (PATCH частичный). Контакты — только изменённые ключи; несовершеннолетним
// контакты не отправляем вообще (сервер их запрещает).
function diff(initial, values, isMinor) {
  const changes = {};
  TEXT_FIELDS.forEach((key) => {
    const next = values[key].trim();
    if (next !== initial[key].trim()) changes[key] = next;
  });
  LIST_FIELDS.forEach((key) => {
    if (values[key].join('|') !== initial[key].join('|')) changes[key] = values[key];
  });
  if (!isMinor) {
    const contacts = {};
    CONTACT_KEYS.forEach((key) => {
      const next = (values.contacts[key] ?? '').trim();
      if (next !== (initial.contacts[key] ?? '').trim()) contacts[key] = next;
    });
    if (Object.keys(contacts).length > 0) changes.contacts = contacts;
  }
  return changes;
}

// Ключ ошибки сервера → поле формы: «interests.0» → «interests», «contacts.telegram» остаётся
const formKey = (path) => path.replace(/^(interests|languages|goals)\.\d+$/, '$1');
const FORM_KEYS = new Set([
  ...TEXT_FIELDS,
  ...LIST_FIELDS,
  ...CONTACT_KEYS.map((k) => `contacts.${k}`),
]);

// Состояние формы редактирования профиля: значения, ошибки по полям (из error.fields сервера),
// отправка PATCH /api/me/ и обновление данных вошедшего (AuthProvider).
export default function useEditProfile(user, limits) {
  const [initial] = useState(() => fromUser(user));
  const [values, setValues] = useState(initial);
  const [errors, setErrors] = useState({});
  const [generalError, setGeneralError] = useState('');
  const [saving, setSaving] = useState(false);
  const [focusSignal, setFocusSignal] = useState(0); // растёт при ошибке → фокус на первое поле с ошибкой
  const { updateUser } = useAuth();
  const showToast = useToast();
  const navigate = useNavigate();
  const isMinor = user.is_minor;

  const clearError = (key) =>
    setErrors((current) => {
      if (!current[key]) return current;
      const next = { ...current };
      delete next[key];
      return next;
    });

  function set(key, value) {
    setValues((prev) => ({ ...prev, [key]: value }));
    clearError(key);
  }

  function setContact(key, value) {
    setValues((prev) => ({ ...prev, contacts: { ...prev.contacts, [key]: value } }));
    clearError(`contacts.${key}`);
  }

  function handleError(error) {
    if (error.code !== 'validation_error') {
      setGeneralError(apiErrorText(error));
      return;
    }
    const fieldErrors = {};
    const general = error.nonFieldErrors.map((item) => fieldErrorText(item, limits));
    Object.entries(error.fields).forEach(([path, items]) => {
      const key = formKey(path);
      const text = fieldErrorText(items[0], limits);
      if (FORM_KEYS.has(key)) fieldErrors[key] = fieldErrors[key] ?? text;
      else general.push(text); // поле, которого нет в форме (например, gender)
    });
    setErrors(fieldErrors);
    setGeneralError(general[0] ?? t.generalError);
    setFocusSignal((n) => n + 1);
  }

  async function submit() {
    const changes = diff(initial, values, isMinor);
    if (Object.keys(changes).length === 0) {
      showToast(t.noChanges);
      return;
    }
    setSaving(true);
    setErrors({});
    setGeneralError('');
    try {
      const updated = await updateMe(changes);
      updateUser(updated);
      showToast(t.saved, 'success');
      navigate('/me');
    } catch (error) {
      handleError(error);
    } finally {
      setSaving(false);
    }
  }

  return { values, errors, generalError, saving, focusSignal, isMinor, set, setContact, submit };
}
