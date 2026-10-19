import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { confirmEmailChange } from '../api/account.js';
import { getMe } from '../api/me.js';
import useAuth from '../app/providers/useAuth.js';
import Button from '../components/ui/Button.jsx';
import Spinner from '../components/ui/Spinner.jsx';
import AuthCard from '../features/auth/components/AuthCard.jsx';
import { apiErrorText } from '../lib/apiErrors.js';
import { texts } from '../texts/en.js';
import styles from './VerifyEmailPage.module.css';

const t = texts.confirmEmailChange;

// Токен в ссылке одноразовый, а React StrictMode в разработке запускает эффект дважды.
// Поэтому запрос по каждому токену делается один раз: промис хранится здесь и переиспользуется.
const requests = new Map();

function confirmOnce(token) {
  if (!requests.has(token)) requests.set(token, confirmEmailChange(token));
  return requests.get(token);
}

// Страница по ссылке из письма: /confirm-email-change/:token. Подтверждает смену адреса одним вызовом
// при открытии. Состояния: проверяем / успех / ошибка. Сессии после смены остаются.
export default function ConfirmEmailChangePage() {
  const { token } = useParams();
  const navigate = useNavigate();
  const { status, updateUser } = useAuth();
  const [result, setResult] = useState({ status: 'checking' });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let active = true;
    confirmOnce(token)
      .then(() => {
        if (active) setResult({ status: 'success' });
        return getMe().then(updateUser, () => {}); // вошедший сразу видит новый адрес
      })
      .catch((error) => {
        if (error.code !== 'invalid_token') requests.delete(token); // сеть и лимит можно повторить
        if (active) setResult({ status: 'error', error });
      });
    return () => {
      active = false;
    };
  }, [token, attempt, updateUser]);

  function retry() {
    setResult({ status: 'checking' });
    setAttempt((n) => n + 1);
  }

  if (result.status === 'success') {
    const signedIn = status === 'authenticated';
    return (
      <AuthCard title={t.successTitle} subtitle={t.successText}>
        <Button fullWidth onClick={() => navigate(signedIn ? '/settings/security' : '/login')}>
          {signedIn ? t.goSettings : t.logIn}
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
          <Button fullWidth onClick={() => navigate('/settings/security')}>
            {t.goSettings}
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
