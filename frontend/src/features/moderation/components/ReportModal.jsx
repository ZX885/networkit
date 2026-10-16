import { useState } from 'react';
import { reportUser } from '../../../api/moderation.js';
import useMeta from '../../../api/useMeta.js';
import Alert from '../../../components/ui/Alert.jsx';
import Button from '../../../components/ui/Button.jsx';
import Field from '../../../components/ui/Field.jsx';
import Modal from '../../../components/ui/Modal.jsx';
import { fullName } from '../../../lib/labels.js';
import { texts } from '../../../texts/en.js';
import { moderationErrorText } from '../errors.js';
import styles from './ModerationModal.module.css';

const t = texts.moderation;
const DEFAULT_DETAILS_MAX = 1000; // запасное значение, пока справочники не загружены

// Жалоба: причина (meta.report_reasons) + описание до details_max. Пока идёт отправка, кнопка заблокирована.
// После успеха — «Thank you, we'll review your report». Ответ сервера всегда одинаков (дубль тоже успех).
// Компонент монтируется только пока окно открыто, поэтому состояние каждый раз чистое.
export default function ReportModal({ person, conversationId, onClose }) {
  const { meta } = useMeta();
  const maxLength = meta?.limits?.details_max ?? DEFAULT_DETAILS_MAX;
  const [reason, setReason] = useState('');
  const [details, setDetails] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState(null);
  const [done, setDone] = useState(false);
  const name = fullName(person);

  async function submit(event) {
    event.preventDefault();
    if (!reason || sending) return;
    setSending(true);
    setError(null);
    try {
      await reportUser({
        username: person.username,
        reason,
        details: details.trim(),
        conversationId,
      });
      setDone(true);
    } catch (err) {
      setError(err);
    } finally {
      setSending(false);
    }
  }

  const close = () => !sending && onClose();

  if (done) {
    return (
      <Modal
        open
        onClose={onClose}
        title={t.reportTitle(name)}
        actions={<Button onClick={onClose}>{t.close}</Button>}
      >
        <p className={styles.thanks} role="status">
          {t.thanks}
        </p>
      </Modal>
    );
  }

  return (
    <Modal open onClose={close} title={t.reportTitle(name)} description={t.reportIntro}>
      <form className={styles.form} onSubmit={submit} noValidate>
        <Field
          as="select"
          label={t.reasonLabel}
          value={reason}
          onChange={(event) => setReason(event.target.value)}
        >
          <option value="">{t.reasonPlaceholder}</option>
          {(meta?.report_reasons ?? []).map((item) => (
            <option key={item.code} value={item.code}>
              {item.label}
            </option>
          ))}
        </Field>
        <Field
          as="textarea"
          label={t.detailsLabel}
          optionalText={t.detailsOptional}
          rows={4}
          value={details}
          maxLength={maxLength}
          placeholder={t.detailsPlaceholder}
          hint={t.counter(details.length, maxLength)}
          onChange={(event) => setDetails(event.target.value)}
        />
        {conversationId && <p className={styles.note}>{t.reportConversationNote}</p>}
        {error && <Alert>{moderationErrorText(error, maxLength)}</Alert>}
        <div className={styles.actions}>
          <Button variant="ghost" onClick={close}>
            {t.cancel}
          </Button>
          <Button type="submit" loading={sending} disabled={!reason}>
            {t.send}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
