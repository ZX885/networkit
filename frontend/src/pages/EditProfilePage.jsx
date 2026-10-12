import useAuth from '../app/providers/useAuth.js';
import BackLink from '../components/shared/BackLink.jsx';
import PageHeader from '../components/shared/PageHeader.jsx';
import EditProfileForm from '../features/profile/components/EditProfileForm.jsx';
import { texts } from '../texts/en.js';

// Редактирование профиля (UI + форма без отправки до шага B4)
export default function EditProfilePage() {
  const { user } = useAuth();

  return (
    <>
      <PageHeader title={texts.editProfile.title}>
        <BackLink to="/me" />
      </PageHeader>
      <EditProfileForm user={user} />
    </>
  );
}
