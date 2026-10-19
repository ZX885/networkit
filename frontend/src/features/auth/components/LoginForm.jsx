import { useState } from 'react';
import { Link } from 'react-router-dom';
import useAuth from '../../../app/providers/useAuth.js';
import Alert from '../../../components/ui/Alert.jsx';
import Button from '../../../components/ui/Button.jsx';
import Field from '../../../components/ui/Field.jsx';
import { apiErrorText } from '../../../lib/apiErrors.js';
import { texts } from '../../../texts/en.js';
import ResendEmail from './ResendEmail.jsx';
import styles from './LoginForm.module.css';

const t = texts.login;
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// Форма входа. onSuccess(user) вызывается после успешного входа.
// Ошибки: у каждого поля свои, плюс общая — текст по коду ответа сервера (texts.apiErrors).
export default function LoginForm({ onSuccess }) {
  const { login, refresh } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState('');
  const [notVerified, setNotVerified] = useState(false); // почта не подтверждена → кнопка «Resend email»
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    const found = {};
    if (!email.trim()) found.email = t.errors.emailRequired;
    else if (!EMAIL_REGEX.test(email.trim())) found.email = t.errors.emailInvalid;
    if (!password) found.password = t.errors.passwordRequired;
    setErrors(found);
    setFormError('');
    setNotVerified(false);
    if (Object.keys(found).length > 0) {
      event.currentTarget.querySelector('[aria-invalid="true"]')?.focus();
      return;
    }

    setLoading(true);
    try {
      const user = await login(email, password);
      setPassword('');
      onSuccess(user);
    } catch (error) {
      if (error.code === 'already_authenticated') {
        await refresh(); // уже вошли в другой вкладке: обновляем состояние, GuestRoute уведёт в профиль
        return;
      }
      setNotVerified(error.code === 'email_not_verified');
      setFormError(apiErrorText(error));
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      {formError && <Alert>{formError}</Alert>}
      {notVerified && <ResendEmail email={email.trim()} />}
      <form onSubmit={handleSubmit} noValidate>
        <Field
          label={t.email}
          type="email"
          placeholder={t.emailPlaceholder}
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          error={errors.email}
        />
        <Field
          label={t.password}
          type="password"
          revealable
          placeholder={t.passwordPlaceholder}
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          error={errors.password}
        />
        <p className={styles.forgot}>
          <Link to="/forgot-password">{texts.passwordReset.forgotLink}</Link>
        </p>
        <Button type="submit" fullWidth loading={loading}>
          {t.submit}
        </Button>
      </form>
      <p className={styles.footer}>
        {t.noAccount} <Link to="/register">{t.createOne}</Link>
      </p>
    </>
  );
}
