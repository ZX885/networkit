import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { verifyEmail } from '../api/auth.js';
import Button from '../components/ui/Button.jsx';
import Spinner from '../components/ui/Spinner.jsx';
import AuthCard from '../features/auth/components/AuthCard.jsx';
import { apiErrorText } from '../lib/apiErrors.js';
import { texts } from '../texts/en.js';
import styles from './VerifyEmailPage.module.css';

const t = texts.verifyEmail;

// Токен в ссылке одноразовый, а React StrictMode в разработке запускает эффект дважды.
// Поэтому запрос по каждому токену делается один раз: промис хранится здесь и переиспользуется.
const requests = new Map();

function verifyOnce(token) {
  if (!requests.has(token)) requests.set(token, verifyEmail(token));
  return requests.get(token);
}

// Страница по ссылке из письма: /verify-email/:token. Состояния: проверяем / успех / ошибка.
export default function VerifyEmailPage() {
  const { token } = useParams();
  const navigate = useNavigate();
  const [result, setResult] = useState({ status: 'checking' });
  const [attempt, setAttempt] = useState(0); // растёт по кнопке «Try again» и перезапускает проверку

  useEffect(() => {
    let active = true;
    verifyOnce(token)
      .then(() => {
        if (active) setResult({ status: 'success' });
      })
      .catch((error) => {
        // Сеть и лимит можно повторить: убираем неудачный промис из кэша
        if (error.code !== 'invalid_token') requests.delete(token);
        if (active) setResult({ status: 'error', error });
      });
    return () => {
      active = false;
    };
  }, [token, attempt]);

  function retry() {
    setResult({ status: 'checking' });
    setAttempt((n) => n + 1);
  }

  if (result.status === 'success') {
    return (
      <AuthCard title={t.successTitle} subtitle={t.successText}>
        <Button fullWidth onClick={() => navigate('/login')}>
          {t.logIn}
        </Button>
      </AuthCard>
    );
  }

  if (result.status === 'error') {
    const invalid = result.error.code === 'invalid_token';
    return (
      <AuthCard
        title={t.errorTitle}
        subtitle={invalid ? t.invalidText : apiErrorText(result.error)}
      >
        {invalid ? (
          <Button fullWidth onClick={() => navigate('/resend-verification')}>
            {t.requestNew}
          </Button>
        ) : (
          <Button fullWidth onClick={retry}>
            {t.retry}
          </Button>
        )}
      </AuthCard>
    );
  }

  return (
    <AuthCard title={t.checking}>
      <div className={styles.spinner} role="status" aria-live="polite">
        <Spinner size="lg" tone="primary" label={t.checking} />
      </div>
    </AuthCard>
  );
}
