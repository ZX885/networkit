import { useState } from 'react';
import { blockUser } from '../../../api/moderation.js';
import Alert from '../../../components/ui/Alert.jsx';
import Button from '../../../components/ui/Button.jsx';
import Modal from '../../../components/ui/Modal.jsx';
import { fullName } from '../../../lib/labels.js';
import { texts } from '../../../texts/en.js';
import { moderationErrorText } from '../errors.js';
import styles from './ModerationModal.module.css';

const t = texts.moderation;

// Подтверждение блокировки. Пока идёт запрос, кнопки заблокированы. Монтируется только пока окно открыто.
// onBlocked() вызывается после успеха (родитель уходит со страницы и обновляет списки).
export default function BlockModal({ person, onClose, onBlocked }) {
  const [sending, setSending] = useState(false);
  const [error, setError] = useState(null);
  const name = fullName(person);

  async function confirm() {
    if (sending) return;
    setSending(true);
    setError(null);
    try {
      await blockUser(person.username);
      onBlocked();
    } catch (err) {
      setError(err);
      setSending(false);
    }
  }

  return (
    <Modal
      open
      onClose={() => !sending && onClose()}
      title={t.blockTitle(name)}
      description={t.blockText}
      actions={
        <>
          <Button variant="ghost" onClick={onClose} disabled={sending}>
            {t.cancel}
          </Button>
          <Button variant="danger" loading={sending} onClick={confirm}>
            {t.blockConfirm}
          </Button>
        </>
      }
    >
      {error && (
        <div className={styles.error}>
          <Alert>{moderationErrorText(error)}</Alert>
        </div>
      )}
    </Modal>
  );
}
