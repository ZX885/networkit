import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { confirmPasswordReset } from '../api/account.js';
import useAuth from '../app/providers/useAuth.js';
import Alert from '../components/ui/Alert.jsx';
import Button from '../components/ui/Button.jsx';
import Field from '../components/ui/Field.jsx';
import PasswordStrength from '../components/ui/PasswordStrength.jsx';
import AuthCard from '../features/auth/components/AuthCard.jsx';
import { checkPassword } from '../features/auth/validation.js';
import { apiErrorText, errorText, serverFieldError } from '../lib/apiErrors.js';
import { texts } from '../texts/en.js';

const t = texts.passwordReset.reset;

// Страница по ссылке из письма: /reset-password/:uid/:token. Запрос на сервер уходит ТОЛЬКО по кнопке
// (один раз на нажатие; пока он идёт, кнопка заблокирована): ссылка одноразовая, автоматически её не тратим.
// Успех → «Password changed» и вход; invalid_token → экран «Request a new link».
export default function ResetPasswordPage() {
  const { uid, token } = useParams();
  const navigate = useNavigate();
  const { endSession } = useAuth();
  const [password, setPassword] = useState('');
  const [fieldError, setFieldError] = useState('');
  const [formError, setFormError] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState('form'); // form | success | invalid

  async function handleSubmit(event) {
    event.preventDefault();
    if (loading) return;
    const problem = checkPassword(password);
    if (problem) return setFieldError(errorText(problem));
    setFieldError('');
    setFormError('');
    setLoading(true);
    try {
      await confirmPasswordReset({ uid, token, newPassword: password });
      endSession(); // сервер завершил все сессии, в том числе в этом браузере
      setResult('success');
    } catch (error) {
      if (error.code === 'invalid_token') {
        setResult('invalid');
      } else {
        const message = serverFieldError(error, 'new_password');
        if (message) setFieldError(message);
        else setFormError(apiErrorText(error));
      }
    } finally {
      setLoading(false);
    }
  }

  if (result === 'success') {
    return (
      <AuthCard title={t.successTitle} subtitle={t.successText}>
        <Button fullWidth onClick={() => navigate('/login')}>
          {t.logIn}
        </Button>
      </AuthCard>
    );
  }

  if (result === 'invalid') {
    return (
      <AuthCard title={t.invalidTitle} subtitle={t.invalidText}>
        <Button fullWidth onClick={() => navigate('/forgot-password')}>
          {t.requestNew}
        </Button>
      </AuthCard>
    );
  }

  return (
    <AuthCard title={t.title} subtitle={t.subtitle}>
      {formError && <Alert>{formError}</Alert>}
      <form onSubmit={handleSubmit} noValidate>
        <Field
          label={t.newPassword}
          type="password"
          revealable
          placeholder={t.newPasswordPlaceholder}
          autoComplete="new-password"
          describedBy="reset-password-strength"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          error={fieldError}
        />
        <PasswordStrength id="reset-password-strength" value={password} />
        <Button type="submit" fullWidth loading={loading}>
          {t.submit}
        </Button>
      </form>
    </AuthCard>
  );
}
