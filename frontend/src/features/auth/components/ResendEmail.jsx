import Alert from '../../../components/ui/Alert.jsx';
import Button from '../../../components/ui/Button.jsx';
import { texts } from '../../../texts/en.js';
import useResendEmail from '../hooks/useResendEmail.js';
import styles from './ResendEmail.module.css';

// Кнопка «Resend email» с паузой и сообщением. email — адрес, на который просим повторить письмо.
export default function ResendEmail({ email }) {
  const { resend, loading, secondsLeft, message } = useResendEmail(email);
  const t = texts.resend;

  return (
    <div className={styles.wrap}>
      <Button
        variant="ghost"
        fullWidth
        loading={loading}
        disabled={secondsLeft > 0}
        onClick={resend}
      >
        {secondsLeft > 0 ? t.wait(secondsLeft) : t.button}
      </Button>
      {/* Область объявляется скринридером при появлении текста */}
      <div role="status" aria-live="polite">
        {message.tone === 'success' && <p className={styles.note}>{message.text}</p>}
      </div>
      {message.tone === 'error' && <Alert>{message.text}</Alert>}
    </div>
  );
}
