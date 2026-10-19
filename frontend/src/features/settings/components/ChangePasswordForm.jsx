import { useState } from 'react';
import { changePassword } from '../../../api/account.js';
import Alert from '../../../components/ui/Alert.jsx';
import Button from '../../../components/ui/Button.jsx';
import Field from '../../../components/ui/Field.jsx';
import PasswordStrength from '../../../components/ui/PasswordStrength.jsx';
import useToast from '../../../components/ui/useToast.js';
import { apiErrorText, errorText, serverFieldError } from '../../../lib/apiErrors.js';
import { texts } from '../../../texts/en.js';
import { checkPassword } from '../../auth/validation.js';
import styles from './SecurityForms.module.css';

const t = texts.settings.security.password;
const EMPTY = { old: '', next: '', repeat: '' };

// Смена пароля: текущий, новый (с индикатором силы) и повтор. Ошибки — у полей, после успеха — тост
// и очистка полей. Остальные сессии сервер завершает сам; текущая остаётся.
export default function ChangePasswordForm() {
  const [values, setValues] = useState(EMPTY);
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState('');
  const [loading, setLoading] = useState(false);
  const showToast = useToast();

  const set = (name) => (event) => setValues((prev) => ({ ...prev, [name]: event.target.value }));

  async function handleSubmit(event) {
    event.preventDefault();
    if (loading) return;
    const found = {};
    if (!values.old) found.old = errorText('required');
    const problem = checkPassword(values.next);
    if (problem) found.next = errorText(problem);
    else if (values.repeat !== values.next) found.repeat = t.mismatch;
    setErrors(found);
    setFormError('');
    if (Object.keys(found).length > 0) return;

    setLoading(true);
    try {
      await changePassword({ oldPassword: values.old, newPassword: values.next });
      setValues(EMPTY);
      showToast(t.success, 'success');
    } catch (error) {
      const server = {
        old: serverFieldError(error, 'old_password'),
        next: serverFieldError(error, 'new_password'),
      };
      if (server.old || server.next) setErrors(server);
      else setFormError(apiErrorText(error));
    } finally {
      setLoading(false);
    }
  }

  return (
    <form
      className={styles.form}
      onSubmit={handleSubmit}
      noValidate
      aria-labelledby="change-password-title"
    >
      <h3 id="change-password-title" className={styles.title}>
        {t.title}
      </h3>
      {formError && <Alert>{formError}</Alert>}
      <Field
        label={t.old}
        type="password"
        revealable
        autoComplete="current-password"
        value={values.old}
        onChange={set('old')}
        error={errors.old}
      />
      <Field
        label={t.new}
        type="password"
        revealable
        autoComplete="new-password"
        describedBy="change-password-strength"
        value={values.next}
        onChange={set('next')}
        error={errors.next}
      />
      <PasswordStrength id="change-password-strength" value={values.next} />
      <Field
        label={t.repeat}
        type="password"
        revealable
        autoComplete="new-password"
        value={values.repeat}
        onChange={set('repeat')}
        error={errors.repeat}
      />
      <Button type="submit" loading={loading}>
        {t.submit}
      </Button>
    </form>
  );
}
