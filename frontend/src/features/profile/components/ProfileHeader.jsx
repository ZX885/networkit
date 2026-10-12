import { Building2, Calendar, GraduationCap, MapPin } from 'lucide-react';
import Avatar from '../../../components/ui/Avatar.jsx';
import { fieldLabel, formatMonthYear, formatPlace, fullName } from '../../../lib/labels.js';
import { texts } from '../../../texts/en.js';
import ContactButtons from './ContactButtons.jsx';
import styles from './ProfileHeader.module.css';

// Шапка-карточка профиля (legacy .phc): аватар, имя, @username, строка «место · направление · вуз · Joined»
// и кнопки контактов. /api/me/ не отдаёт field_label (в отличие от публичных ответов) — берём из справочника. Поля, скрытые приватностью, приходят как null и просто не показываются.
export default function ProfileHeader({ profile, isOwner = false }) {
  // На /me заголовок страницы «My profile» уже h1, поэтому имя — h2
  const Heading = isOwner ? 'h2' : 'h1';
  const joined = formatMonthYear(profile.joined ?? profile.created_at);
  const place = formatPlace(profile);
  const meta = [
    { icon: MapPin, text: place },
    { icon: GraduationCap, text: profile.field_label ?? fieldLabel(profile.field) },
    { icon: Building2, text: profile.university },
    { icon: Calendar, text: joined && texts.profile.joined(joined) },
  ].filter((item) => item.text);

  return (
    <section className={styles.card}>
      <Avatar
        id={profile.username}
        firstName={profile.first_name}
        lastName={profile.last_name}
        src={profile.avatar_url}
        size="xl"
      />
      <div className={styles.info}>
        <Heading className={`${styles.name} user-text`}>{fullName(profile)}</Heading>
        <p className={`${styles.username} user-text`}>@{profile.username}</p>
        <ul className={styles.meta}>
          {meta.map((item) => (
            <li key={item.text} className={`${styles.metaItem} user-text`}>
              <item.icon size={14} aria-hidden="true" />
              {item.text}
            </li>
          ))}
        </ul>
        {!profile.is_minor && <ContactButtons contacts={profile.contacts} />}
      </div>
    </section>
  );
}
