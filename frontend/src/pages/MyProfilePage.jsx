import { Link2 } from 'lucide-react';
import useAuth from '../app/providers/useAuth.js';
import MetaGate from '../components/shared/MetaGate.jsx';
import PageHeader from '../components/shared/PageHeader.jsx';
import Button from '../components/ui/Button.jsx';
import ButtonLink from '../components/ui/ButtonLink.jsx';
import useToast from '../components/ui/useToast.js';
import ProfileView from '../features/profile/components/ProfileView.jsx';
import { texts } from '../texts/en.js';
import styles from './MyProfilePage.module.css';

const t = texts.profile;

// Мой профиль: реальные данные из GET /api/me/ (через useAuth). Поля сервера уже учитывают возраст.
export default function MyProfilePage() {
  const { user } = useAuth();
  const showToast = useToast();

  // Копируем ссылку на публичную страницу {origin}/u/username
  async function handleShare() {
    try {
      await navigator.clipboard.writeText(`${window.location.origin}/u/${user.username}`);
      showToast(t.shareDone, 'success');
    } catch {
      showToast(t.shareFailed, 'error'); // буфер недоступен (нет прав или http)
    }
  }

  return (
    <>
      <PageHeader title={t.myTitle}>
        <div className={styles.actions}>
          <Button variant="ghost" size="sm" onClick={handleShare}>
            <Link2 size={14} aria-hidden="true" />
            {t.share}
          </Button>
          <ButtonLink to="/me/edit" size="sm">
            {t.edit}
          </ButtonLink>
        </div>
      </PageHeader>
      <MetaGate>
        <ProfileView profile={user} isOwner />
      </MetaGate>
    </>
  );
}
