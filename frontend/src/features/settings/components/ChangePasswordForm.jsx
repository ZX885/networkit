import { useState } from 'react';
import Button from '../../../components/ui/Button.jsx';
import Field from '../../../components/ui/Field.jsx';
import useToast from '../../../components/ui/useToast.js';
import { PASSWORD_MAX, PASSWORD_MIN } from '../../../constants/rules.js';
import { texts } from '../../../texts/en.js';

const t = texts.settings.security;
const EMPTY = { current: '', next: '', confirm: '' };

// Смена пароля: форма с проверками. Отправку подключим в B4 — пока после проверки кнопка отвечает
// «Coming soon» и ничего не меняет (пароли никуда не отправляются).
export default function ChangePasswordForm() {
  const [values, setValues] = useState(EMPTY);
  const [errors, setErrors] = useState({});
  const showToast = useToast();

  const set = (key) => (event) => setValues((prev) => ({ ...prev, [key]: event.target.value }));

  function handleSubmit(event) {
    event.preventDefault();
    const found = {};
    if (!values.current) found.current = t.errors.currentRequired;
    if (values.next.length < PASSWORD_MIN) found.next = t.errors.newTooShort(PASSWORD_MIN);
    if (values.confirm !== values.next) found.confirm = t.errors.mismatch;
    setErrors(found);
    if (Object.keys(found).length === 0) {
      setValues(EMPTY);
      showToast(texts.app.comingSoon);
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
      <Field
        type="password"
        label={t.currentPassword}
        autoComplete="current-password"
        value={values.current}
        error={errors.current}
        onChange={set('current')}
      />
      <Field
        type="password"
        label={t.newPassword}
        placeholder={t.newPasswordPlaceholder}
        autoComplete="new-password"
        maxLength={PASSWORD_MAX}
        value={values.next}
        error={errors.next}
        onChange={set('next')}
      />
      <Field
        type="password"
        label={t.confirmPassword}
        autoComplete="new-password"
        maxLength={PASSWORD_MAX}
        value={values.confirm}
        error={errors.confirm}
        onChange={set('confirm')}
      />
      <Button type="submit" size="sm">
        {t.updatePassword}
      </Button>
    </form>
  );
}
