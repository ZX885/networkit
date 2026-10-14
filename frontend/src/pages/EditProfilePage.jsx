import useAuth from '../app/providers/useAuth.js';
import BackLink from '../components/shared/BackLink.jsx';
import MetaGate from '../components/shared/MetaGate.jsx';
import PageHeader from '../components/shared/PageHeader.jsx';
import EditProfileForm from '../features/profile/components/EditProfileForm.jsx';
import { texts } from '../texts/en.js';

// Редактирование профиля: форма отправляет PATCH /api/me/. Справочники — с сервера (MetaGate).
export default function EditProfilePage() {
  const { user } = useAuth();

  return (
    <>
      <PageHeader title={texts.editProfile.title}>
        <BackLink to="/me" />
      </PageHeader>
      <MetaGate>
        <EditProfileForm user={user} />
      </MetaGate>
    </>
  );
}
