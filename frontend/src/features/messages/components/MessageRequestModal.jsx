import { useState } from 'react';
import { Link } from 'react-router-dom';
import { createRequest } from '../../../api/conversations.js';
import useSummary from '../../../app/providers/useSummary.js';
import Alert from '../../../components/ui/Alert.jsx';
import Button from '../../../components/ui/Button.jsx';
import Field from '../../../components/ui/Field.jsx';
import Modal from '../../../components/ui/Modal.jsx';
import useToast from '../../../components/ui/useToast.js';
import { texts } from '../../../texts/en.js';
import { conversationLink, sendErrorText } from '../errors.js';
import SafetyNotice from './SafetyNotice.jsx';
import styles from './MessageRequestModal.module.css';

const t = texts.messages.request;

// Модалка «Send a message request»: первое сообщение до request_max символов. Пока идёт отправка,
// кнопка заблокирована. Ошибки (409 / 429 / длина) — обычным текстом; при 409 — ссылка на диалог.
export default function MessageRequestModal({ open, onClose, username, name, maxLength }) {
  const [value, setValue] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState(null);
  const showToast = useToast();
  const { refresh } = useSummary();
  const body = value.trim();
  const link = error ? conversationLink(error) : null;

  function close() {
    if (sending) return;
    setError(null);
    onClose();
  }

  async function submit(event) {
    event.preventDefault();
    if (!body || sending) return;
    setSending(true);
    setError(null);
    try {
      await createRequest(username, body);
      setValue('');
      showToast(t.sentToast, 'success');
      refresh().catch(() => {});
      onClose();
    } catch (err) {
      setError(err);
    } finally {
      setSending(false);
    }
  }

  return (
    <Modal open={open} onClose={close} title={t.title} description={t.intro(name)}>
      <form className={styles.form} onSubmit={submit} noValidate>
        <Field
          as="textarea"
          label={t.label}
          rows={4}
          value={value}
          maxLength={maxLength}
          placeholder={t.placeholder}
          hint={t.counter(value.length, maxLength)}
          onChange={(event) => setValue(event.target.value)}
        />
        {error && (
          <Alert>
            {sendErrorText(error, maxLength)}
            {link && (
              <>
                {' '}
                <Link to={link} onClick={onClose}>
                  {t.open}
                </Link>
              </>
            )}
          </Alert>
        )}
        <SafetyNotice />
        <div className={styles.actions}>
          <Button variant="ghost" onClick={close}>
            {t.cancel}
          </Button>
          <Button type="submit" loading={sending} disabled={!body}>
            {t.send}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
