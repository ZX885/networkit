import { useState } from 'react';
import { Link } from 'react-router-dom';
import { login } from '../../../api/mock/auth.js';
import Alert from '../../../components/ui/Alert.jsx';
import Button from '../../../components/ui/Button.jsx';
import Field from '../../../components/ui/Field.jsx';
import { texts } from '../../../texts/en.js';
import ForgotPasswordModal from './ForgotPasswordModal.jsx';
import GoogleIcon from './GoogleIcon.jsx';
import styles from './LoginForm.module.css';

const t = texts.login;
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// Форма входа. onSuccess(user) вызывается после успешного входа.
// Ошибки: у каждого поля свои, плюс общая («неверный email или пароль»).
export default function LoginForm({ onSuccess }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState('');
  const [loading, setLoading] = useState(false);
  const [forgotOpen, setForgotOpen] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    const found = {};
    if (!email.trim()) found.email = t.errors.emailRequired;
    else if (!EMAIL_REGEX.test(email.trim())) found.email = t.errors.emailInvalid;
    if (!password) found.password = t.errors.passwordRequired;
    setErrors(found);
    setFormError('');
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
      setFormError(
        error.code === 'invalid_credentials' ? t.errors.invalidCredentials : t.errors.network,
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      {formError && <Alert>{formError}</Alert>}
      <button type="button" className={styles.google} disabled aria-describedby="google-soon">
        <GoogleIcon /> {t.google}
      </button>
      <p id="google-soon" className={styles.googleNote}>
        {t.googleSoon}
      </p>
      <div className={styles.divider}>
        <span>{t.divider}</span>
      </div>
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
          placeholder={t.passwordPlaceholder}
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          error={errors.password}
        />
        <div className={styles.forgot}>
          <button type="button" className={styles.link} onClick={() => setForgotOpen(true)}>
            {t.forgot}
          </button>
        </div>
        <Button type="submit" fullWidth loading={loading}>
          {t.submit}
        </Button>
      </form>
      <p className={styles.footer}>
        {t.noAccount} <Link to="/register">{t.createOne}</Link>
      </p>
      <ForgotPasswordModal open={forgotOpen} onClose={() => setForgotOpen(false)} />
    </>
  );
}
