import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { requestPasswordReset } from '../api/account.js';
import Alert from '../components/ui/Alert.jsx';
import Button from '../components/ui/Button.jsx';
import Field from '../components/ui/Field.jsx';
import AuthCard from '../features/auth/components/AuthCard.jsx';
import { EMAIL_REGEX } from '../features/auth/validation.js';
import { apiErrorText } from '../lib/apiErrors.js';
import { texts } from '../texts/en.js';
import styles from './ForgotPasswordPage.module.css';

const t = texts.passwordReset.forgot;
const COOLDOWN_SECONDS = 60;

// «Forgot password?»: человек вводит email, мы просим сервер отправить ссылку. Ответ всегда нейтральный
// («If the email is registered…»): есть ли такой адрес, не раскрывается. После отправки — пауза 60 секунд.
export default function ForgotPasswordPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [fieldError, setFieldError] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');
  const [secondsLeft, setSecondsLeft] = useState(0);

  useEffect(() => {
    if (secondsLeft <= 0) return undefined;
    const timer = setTimeout(() => setSecondsLeft((seconds) => seconds - 1), 1000);
    return () => clearTimeout(timer);
  }, [secondsLeft]);

  async function handleSubmit(event) {
    event.preventDefault();
    if (loading || secondsLeft > 0) return;
    const trimmed = email.trim();
    if (!trimmed) return setFieldError(t.emailRequired);
    if (!EMAIL_REGEX.test(trimmed)) return setFieldError(t.emailInvalid);
    setFieldError('');
    setError('');
    setLoading(true);
    try {
      await requestPasswordReset(trimmed);
      setSent(true);
      setSecondsLeft(COOLDOWN_SECONDS);
    } catch (err) {
      setError(apiErrorText(err));
      // Лимит сервера: ждём столько, сколько он просит
      if (err.code === 'throttled' && err.retryAfter) setSecondsLeft(err.retryAfter);
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthCard title={t.title} subtitle={t.subtitle}>
      {error && <Alert>{error}</Alert>}
      <form onSubmit={handleSubmit} noValidate>
        <Field
          label={t.email}
          type="email"
          placeholder={t.emailPlaceholder}
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          error={fieldError}
        />
        <Button type="submit" fullWidth loading={loading} disabled={secondsLeft > 0}>
          {secondsLeft > 0 ? t.wait(secondsLeft) : sent ? t.again : t.submit}
        </Button>
      </form>
      {/* Область объявляется скринридером при появлении текста */}
      <div role="status" aria-live="polite">
        {sent && <p className={styles.note}>{t.sent}</p>}
      </div>
      <Button variant="ghost" fullWidth onClick={() => navigate('/login')}>
        {t.back}
      </Button>
    </AuthCard>
  );
}
