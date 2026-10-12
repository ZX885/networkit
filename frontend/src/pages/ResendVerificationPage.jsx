import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../components/ui/Button.jsx';
import Field from '../components/ui/Field.jsx';
import AuthCard from '../features/auth/components/AuthCard.jsx';
import ResendEmail from '../features/auth/components/ResendEmail.jsx';
import { texts } from '../texts/en.js';

const t = texts.resendPage;

// Страница «Request a new link»: человек вводит email, и мы просим сервер повторить письмо.
// Ответ всегда нейтральный (см. ResendEmail), так что адрес не проверяется на существование.
export default function ResendVerificationPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [touched, setTouched] = useState(false);
  const trimmed = email.trim();

  return (
    <AuthCard title={t.title} subtitle={t.subtitle}>
      <Field
        label={t.email}
        type="email"
        placeholder={t.emailPlaceholder}
        autoComplete="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        onBlur={() => setTouched(true)}
        error={touched && !trimmed ? t.emailRequired : undefined}
      />
      {trimmed ? <ResendEmail email={trimmed} /> : null}
      <Button variant="ghost" fullWidth onClick={() => navigate('/login')}>
        {t.back}
      </Button>
    </AuthCard>
  );
}
