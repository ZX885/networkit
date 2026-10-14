import { useParams } from 'react-router-dom';
import BackLink from '../components/shared/BackLink.jsx';
import MetaGate from '../components/shared/MetaGate.jsx';
import PageHeader from '../components/shared/PageHeader.jsx';
import Button from '../components/ui/Button.jsx';
import Spinner from '../components/ui/Spinner.jsx';
import ProfileActions from '../features/profile/components/ProfileActions.jsx';
import ProfileView from '../features/profile/components/ProfileView.jsx';
import ReportBlock from '../features/profile/components/ReportBlock.jsx';
import useProfile from '../features/profile/hooks/useProfile.js';
import { texts } from '../texts/en.js';
import styles from './ProfilePage.module.css';

const t = texts.profile;

// Чужой профиль /u/:username (MOCK: api/mock/people.js). Неизвестный username → «Profile not found».
export default function ProfilePage() {
  const { username } = useParams();
  const { status, profile, retry } = useProfile(username);

  if (status === 'loading') {
    return (
      <>
        <h1 className="visually-hidden">{t.loading}</h1>
        <div className={styles.center} role="status">
          <Spinner size="lg" tone="primary" label={t.loading} />
        </div>
      </>
    );
  }

  if (status === 'notFound' || status === 'error') {
    const failed = status === 'error';
    return (
      <>
        <PageHeader title={failed ? texts.app.errorTitle : t.notFoundTitle}>
          <BackLink to="/discover" />
        </PageHeader>
        <div role="alert">
          {!failed && <p className={styles.text}>{t.notFoundText}</p>}
          {failed && <Button onClick={retry}>{texts.app.retry}</Button>}
        </div>
      </>
    );
  }

  return (
    <>
      <div className={styles.bar}>
        <BackLink to="/discover" />
        <div className={styles.actions}>
          <ProfileActions key={profile.username} profile={profile} />
        </div>
      </div>
      <MetaGate>
        <ProfileView profile={profile}>
          <ReportBlock />
        </ProfileView>
      </MetaGate>
    </>
  );
}
