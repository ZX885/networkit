import { Bookmark, MessageCircle } from 'lucide-react';
import Button from '../../../components/ui/Button.jsx';
import useToast from '../../../components/ui/useToast.js';
import { texts } from '../../../texts/en.js';

const t = texts.profile;

// Кнопки на чужом профиле: «Send message» и «Save». Пока без функции: тост «Coming soon»
// (сообщения подключим в B6/B7, избранное — в B9).
export default function ProfileActions() {
  const showToast = useToast();
  const comingSoon = () => showToast(texts.app.comingSoon);

  return (
    <>
      <Button size="sm" onClick={comingSoon}>
        <MessageCircle size={14} aria-hidden="true" />
        {t.sendMessage}
      </Button>
      <Button variant="ghost" size="sm" onClick={comingSoon}>
        <Bookmark size={14} aria-hidden="true" />
        {t.save}
      </Button>
    </>
  );
}
