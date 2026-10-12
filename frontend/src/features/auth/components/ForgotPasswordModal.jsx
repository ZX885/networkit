import Button from '../../../components/ui/Button.jsx';
import Modal from '../../../components/ui/Modal.jsx';
import { texts } from '../../../texts/en.js';

const t = texts.forgot;

// Окно «Reset password». Сброс пароля на сервере ещё не готов, поэтому окно только сообщает об этом
// и не обещает отправку письма.
export default function ForgotPasswordModal({ open, onClose }) {
  return (
    <Modal
      open={open}
      onClose={onClose}
      title={t.title}
      description={t.comingSoon}
      actions={
        <Button size="sm" onClick={onClose}>
          {t.close}
        </Button>
      }
    />
  );
}
