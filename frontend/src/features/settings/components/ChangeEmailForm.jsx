import { useState } from 'react';
import useAuth from '../../../app/providers/useAuth.js';
import Button from '../../../components/ui/Button.jsx';
import Field from '../../../components/ui/Field.jsx';
import useToast from '../../../components/ui/useToast.js';
import { EMAIL_MAX } from '../../../constants/rules.js';
import { EMAIL_REGEX } from '../../auth/validation.js';
import { texts } from '../../../texts/en.js';
import styles from './ChangeEmailForm.module.css';

const t = texts.settings.security;

// Смена email: форма с проверками. Отправку подключим в B4: сейчас после проверки — «Coming soon».
export default function ChangeEmailForm() {
  const { user } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState({});
  const showToast = useToast();

  function handleSubmit(event) {
    event.preventDefault();
    const found = {};
    const value = email.trim();
    if (!EMAIL_REGEX.test(value) || value.length > EMAIL_MAX) found.email = t.errors.emailInvalid;
    if (!password) found.password = t.errors.passwordRequired;
    setErrors(found);
    if (Object.keys(found).length === 0) {
      setEmail('');
      setPassword('');
      showToast(texts.app.comingSoon);
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
      <h3 className={styles.title}>{t.changeEmail}</h3>
      <p className={`${styles.current} user-text`}>
        {t.currentEmail} <strong>{user.email}</strong>
      </p>
      <Field
        type="email"
        label={t.newEmail}
        autoComplete="email"
        value={email}
        error={errors.email}
        onChange={(event) => setEmail(event.target.value)}
      />
      <Field
        type="password"
        label={t.passwordForEmail}
        autoComplete="current-password"
        value={password}
        error={errors.password}
        onChange={(event) => setPassword(event.target.value)}
      />
      <Button type="submit" size="sm">
        {t.updateEmail}
      </Button>
    </form>
  );
}
