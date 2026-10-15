import { useState } from 'react';
import { MessageCircle } from 'lucide-react';
import useMeta from '../../../api/useMeta.js';
import Button from '../../../components/ui/Button.jsx';
import { fullName } from '../../../lib/labels.js';
import { texts } from '../../../texts/en.js';
import MessageRequestModal from './MessageRequestModal.jsx';

const t = texts.messages.request;
const DEFAULT_MAX = 500; // запасное значение, пока справочники не загружены

// Кнопка «Message» (карточка и профиль): открывает модалку запроса на переписку.
// person — { username, first_name, last_name }.
export default function MessageRequestButton({ person, size = 'sm', variant = 'primary' }) {
  const [open, setOpen] = useState(false);
  const { meta } = useMeta();
  const name = fullName(person);

  return (
    <>
      <Button
        size={size}
        variant={variant}
        aria-label={t.messageLabel(name)}
        onClick={() => setOpen(true)}
      >
        <MessageCircle size={14} aria-hidden="true" />
        {t.message}
      </Button>
      <MessageRequestModal
        open={open}
        onClose={() => setOpen(false)}
        username={person.username}
        name={name}
        maxLength={meta?.limits?.request_max ?? DEFAULT_MAX}
      />
    </>
  );
}
