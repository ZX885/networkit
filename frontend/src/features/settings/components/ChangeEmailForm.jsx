import { useState } from 'react';
import { requestEmailChange } from '../../../api/account.js';
import useAuth from '../../../app/providers/useAuth.js';
import Alert from '../../../components/ui/Alert.jsx';
import Button from '../../../components/ui/Button.jsx';
import Field from '../../../components/ui/Field.jsx';
import { apiErrorText, errorText, serverFieldError } from '../../../lib/apiErrors.js';
import { texts } from '../../../texts/en.js';
import { EMAIL_REGEX } from '../../auth/validation.js';
import styles from './SecurityForms.module.css';

const t = texts.settings.security.email;

// Смена email: новый адрес и пароль. Ответ сервера одинаков, даже если адрес занят, поэтому после
// отправки показываем нейтральное «Check your new email to confirm». Адрес меняется только по ссылке.
export default function ChangeEmailForm() {
  const { user } = useAuth();
  const [newEmail, setNewEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    if (loading) return;
    const email = newEmail.trim();
    const found = {};
    if (!email) found.email = t.newEmailRequired;
    else if (!EMAIL_REGEX.test(email)) found.email = t.newEmailInvalid;
    if (!password) found.password = errorText('required');
    setErrors(found);
    setFormError('');
    setSent(false);
    if (Object.keys(found).length > 0) return;

    setLoading(true);
    try {
      await requestEmailChange({ newEmail: email, password });
      setSent(true);
      setPassword('');
    } catch (error) {
      const server = {
        email: serverFieldError(error, 'new_email'),
        password: serverFieldError(error, 'password'),
      };
      if (server.email || server.password) setErrors(server);
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
      aria-labelledby="change-email-title"
    >
      <h3 id="change-email-title" className={styles.title}>
        {t.title}
      </h3>
      <p className={styles.hint}>{t.current(user.email)}</p>
      {formError && <Alert>{formError}</Alert>}
      <Field
        label={t.newEmail}
        type="email"
        placeholder={t.newEmailPlaceholder}
        autoComplete="email"
        value={newEmail}
        onChange={(e) => setNewEmail(e.target.value)}
        error={errors.email}
      />
      <Field
        label={t.password}
        type="password"
        revealable
        autoComplete="current-password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        error={errors.password}
        hint={t.note}
      />
      <Button type="submit" loading={loading}>
        {t.submit}
      </Button>
      {/* Область объявляется скринридером при появлении текста */}
      <div role="status" aria-live="polite">
        {sent && <p className={styles.sent}>{t.sent}</p>}
      </div>
    </form>
  );
}
