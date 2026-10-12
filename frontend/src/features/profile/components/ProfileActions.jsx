import { Bookmark, MessageCircle } from 'lucide-react';
import Button from '../../../components/ui/Button.jsx';
import useOpenChat from '../../../components/shared/useOpenChat.js';
import useSavedToggle from '../../../components/shared/useSavedToggle.js';
import { texts } from '../../../texts/en.js';

const t = texts.profile;

// Кнопки на чужом профиле: «Send message» и «Save» (закладка)
export default function ProfileActions({ profile }) {
  const openChat = useOpenChat();
  const { saved, busy, toggle } = useSavedToggle(profile.username, profile.is_saved);

  return (
    <>
      <Button size="sm" onClick={() => openChat(profile.username)}>
        <MessageCircle size={14} aria-hidden="true" />
        {t.sendMessage}
      </Button>
      <Button variant="ghost" size="sm" aria-pressed={saved} loading={busy} onClick={toggle}>
        <Bookmark size={14} fill={saved ? 'currentColor' : 'none'} aria-hidden="true" />
        {saved ? t.saved : t.save}
      </Button>
    </>
  );
}
