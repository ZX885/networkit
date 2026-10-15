import { Bookmark } from 'lucide-react';
import Button from '../../../components/ui/Button.jsx';
import useSavedToggle from '../../../components/shared/useSavedToggle.js';
import MessageRequestButton from '../../messages/components/MessageRequestButton.jsx';
import { texts } from '../../../texts/en.js';

const t = texts.profile;

// Кнопка «Save» на чужом профиле: реальная закладка (aria-pressed), состояние меняется сразу
// и откатывается при ошибке (в том числе при лимите закладок).
export default function ProfileActions({ profile }) {
  const { saved, busy, toggle } = useSavedToggle(profile.username, profile.is_saved);

  return (
    <>
      <MessageRequestButton person={profile} />
      <Button variant="ghost" size="sm" aria-pressed={saved} loading={busy} onClick={toggle}>
        <Bookmark size={14} fill={saved ? 'currentColor' : 'none'} aria-hidden="true" />
        {saved ? t.saved : t.save}
      </Button>
    </>
  );
}
