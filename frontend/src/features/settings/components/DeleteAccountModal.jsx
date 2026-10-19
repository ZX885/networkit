import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { deleteAccount } from '../../../api/account.js';
import useAuth from '../../../app/providers/useAuth.js';
import Alert from '../../../components/ui/Alert.jsx';
import Button from '../../../components/ui/Button.jsx';
import Field from '../../../components/ui/Field.jsx';
import Modal from '../../../components/ui/Modal.jsx';
import useToast from '../../../components/ui/useToast.js';
import { apiErrorText, serverFieldError } from '../../../lib/apiErrors.js';
import { texts } from '../../../texts/en.js';
import styles from './DangerTab.module.css';

const t = texts.settings.danger;

// Удаление аккаунта: предупреждение, пароль и слово DELETE. Кнопка активна только когда оба поля верны
// по форме и блокируется на время запроса. Успех: сессия закрыта сервером → становимся гостем, уходим на
// главную и показываем тост. Монтируется только пока окно открыто (состояние каждый раз чистое).
export default function DeleteAccountModal({ onClose }) {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const showToast = useToast();
  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [formError, setFormError] = useState('');
  const [loading, setLoading] = useState(false);
  const ready = password !== '' && confirmation === t.confirmWord;

  async function handleSubmit(event) {
    event.preventDefault();
    if (!ready || loading) return;
    setPasswordError('');
    setFormError('');
    setLoading(true);
    try {
      await deleteAccount(password);
      // Сначала уходим на главную: иначе защищённая страница после выхода сама отправит на /login
      // Как при обычном выходе (useLogout): сначала на главную, потом гость. Иначе защищённая страница
      // успеет отправить на /login. Сессия уже закрыта сервером, logout() просто переводит в гостя.
      navigate('/', { replace: true });
      await logout();
      showToast(t.deletedToast, 'success');
    } catch (error) {
      const message = serverFieldError(error, 'password');
      if (message) setPasswordError(message);
      else setFormError(apiErrorText(error));
      setLoading(false);
    }
  }

  return (
    <Modal
      open
      onClose={() => !loading && onClose()}
      title={t.modalTitle}
      description={t.modalIntro}
    >
      <form className={styles.form} onSubmit={handleSubmit} noValidate>
        <ul className={styles.list}>
          {t.willDelete.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
        {formError && <Alert>{formError}</Alert>}
        <Field
          label={t.password}
          type="password"
          revealable
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          error={passwordError}
        />
        <Field
          label={t.confirmLabel}
          autoComplete="off"
          autoCapitalize="characters"
          spellCheck={false}
          value={confirmation}
          onChange={(e) => setConfirmation(e.target.value)}
        />
        <div className={styles.actions}>
          <Button variant="ghost" onClick={onClose} disabled={loading}>
            {t.cancel}
          </Button>
          <Button type="submit" variant="danger" loading={loading} disabled={!ready}>
            {t.confirm}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
