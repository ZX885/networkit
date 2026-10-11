import { useState } from 'react';
import { requestPasswordReset } from '../../../api/mock/auth.js';
import Button from '../../../components/ui/Button.jsx';
import Field from '../../../components/ui/Field.jsx';
import Modal from '../../../components/ui/Modal.jsx';
import useToast from '../../../components/ui/useToast.js';
import { texts } from '../../../texts/en.js';

const t = texts.forgot;

// Модалка «Reset password»: поле email и тост. Текст тоста одинаков для любого адреса —
// так нельзя выяснить, зарегистрирован ли email (защита от перебора, как в legacy).
export default function ForgotPasswordModal({ open, onClose }) {
  const showToast = useToast();
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  function close() {
    setError('');
    onClose();
  }

  async function send() {
    if (!email.trim()) {
      setError(t.emailRequired);
      return;
    }
    setLoading(true);
    try {
      await requestPasswordReset(email.trim());
      showToast(t.sent, 'success');
      setEmail('');
      close();
    } catch {
      showToast(t.failed, 'error');
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal
      open={open}
      onClose={close}
      title={t.title}
      description={t.description}
      actions={
        <>
          <Button variant="ghost" size="sm" onClick={close}>
            {t.cancel}
          </Button>
          <Button size="sm" loading={loading} onClick={send}>
            {t.send}
          </Button>
        </>
      }
    >
      <Field
        label={t.email}
        type="email"
        placeholder={t.emailPlaceholder}
        autoComplete="email"
        value={email}
        onChange={(e) => {
          setEmail(e.target.value);
          setError('');
        }}
        onKeyDown={(e) => e.key === 'Enter' && send()}
        error={error}
      />
    </Modal>
  );
}
