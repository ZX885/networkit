import { useState } from 'react';
import Alert from '../../../components/ui/Alert.jsx';
import Button from '../../../components/ui/Button.jsx';
import { apiErrorText } from '../../../lib/apiErrors.js';
import { fullName } from '../../../lib/labels.js';
import { texts } from '../../../texts/en.js';
import styles from './RequestBar.module.css';

const t = texts.messages.requestBar;

// Полоса под сообщениями вместо поля ввода, пока диалог не принят:
// получателю — Accept / Decline; инициатору — «Request sent» (отказ ему не показывается);
// получателю после отказа — «closed».
export default function RequestBar({ conversation, onAccept, onDecline }) {
  const [busy, setBusy] = useState(null); // 'accept' | 'decline'
  const [error, setError] = useState(null);

  async function run(kind, action) {
    if (busy) return;
    setBusy(kind);
    setError(null);
    try {
      await action();
    } catch (err) {
      setError(apiErrorText(err));
    } finally {
      setBusy(null);
    }
  }

  if (conversation.initiated_by_me) {
    return (
      <div className={styles.bar} role="status">
        <p className={styles.title}>{t.sentTitle}</p>
        <p className={styles.text}>{t.sentText}</p>
      </div>
    );
  }

  if (conversation.status === 'declined') {
    return (
      <div className={styles.bar} role="status">
        <p className={styles.text}>{t.closedText}</p>
      </div>
    );
  }

  return (
    <div className={styles.bar}>
      <p className={`${styles.title} user-text`}>{t.title(fullName(conversation.other_user))}</p>
      <p className={styles.text}>{t.text}</p>
      {error && <Alert>{error}</Alert>}
      <div className={styles.actions}>
        <Button
          size="sm"
          loading={busy === 'accept'}
          disabled={busy !== null}
          onClick={() => run('accept', onAccept)}
        >
          {t.accept}
        </Button>
        <Button
          size="sm"
          variant="ghost"
          loading={busy === 'decline'}
          disabled={busy !== null}
          onClick={() => run('decline', onDecline)}
        >
          {t.decline}
        </Button>
      </div>
    </div>
  );
}
