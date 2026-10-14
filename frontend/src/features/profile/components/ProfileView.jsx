import { ClipboardList, Languages, Lightbulb, Pencil, Target } from 'lucide-react';
import { Link } from 'react-router-dom';
import useMeta from '../../../api/useMeta.js';
import { texts } from '../../../texts/en.js';
import DetailsList from './DetailsList.jsx';
import ProfileHeader from './ProfileHeader.jsx';
import ProfileSection from './ProfileSection.jsx';
import styles from './ProfileView.module.css';
import TagList from './TagList.jsx';

const t = texts.profile;

// Вид профиля для /me (isOwner) и /u/:username. children — дополнительные блоки справа
// (например, «Report» на чужом профиле). Пользовательский текст выводим только как текст.
export default function ProfileView({ profile, isOwner = false, children }) {
  const { meta } = useMeta();
  const hasList = (list) => Array.isArray(list) && list.length > 0;

  return (
    <>
      <ProfileHeader profile={profile} isOwner={isOwner} />
      <div className={styles.body}>
        <div className={styles.column}>
          {(profile.bio || isOwner) && (
            <ProfileSection icon={Pencil} title={t.about}>
              {profile.bio ? (
                <p className={`${styles.bio} user-text`}>{profile.bio}</p>
              ) : (
                <p className={styles.empty}>
                  {t.noBio} <Link to="/me/edit">{t.noBioAction}</Link>
                </p>
              )}
            </ProfileSection>
          )}
          {hasList(profile.goals) && (
            <ProfileSection icon={Target} title={t.goals}>
              <TagList list={meta.goals} codes={profile.goals} />
            </ProfileSection>
          )}
          {hasList(profile.interests) && (
            <ProfileSection icon={Lightbulb} title={t.interests}>
              <TagList list={meta.interests} codes={profile.interests} />
            </ProfileSection>
          )}
        </div>
        <div className={styles.column}>
          <ProfileSection icon={ClipboardList} title={t.details}>
            <DetailsList profile={profile} />
          </ProfileSection>
          {hasList(profile.languages) && (
            <ProfileSection icon={Languages} title={t.languages}>
              <TagList list={meta.languages} codes={profile.languages} />
            </ProfileSection>
          )}
          {children}
        </div>
      </div>
    </>
  );
}
