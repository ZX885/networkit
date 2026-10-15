import { Bookmark } from 'lucide-react';
import useMeta from '../../api/useMeta.js';
import { formatPlace, fullName, labelOf } from '../../lib/labels.js';
import { texts } from '../../texts/en.js';
import Avatar from '../ui/Avatar.jsx';
import ButtonLink from '../ui/ButtonLink.jsx';
import MessageRequestButton from '../../features/messages/components/MessageRequestButton.jsx';
import Tag from '../ui/Tag.jsx';
import useSavedToggle from './useSavedToggle.js';
import styles from './PersonCard.module.css';

const t = texts.card;
const MAX_TAGS = 3;

// Карточка человека (legacy .rc) в Discover и Saved. person — формат Card (docs/SPEC.md §3.6);
// city/country могут быть null (скрыты приватностью). Закладка — настоящая (aria-pressed): состояние
// меняется сразу и откатывается при ошибке; onSavedChange/onSavedRevert сообщают список (Saved).
export default function PersonCard({ person, onSavedChange, onSavedRevert }) {
  const name = fullName(person);
  const { meta } = useMeta(); // карточки показываются после загрузки справочников (MetaGate)
  const { saved, busy, toggle } = useSavedToggle(person.username, person.is_saved, {
    onChange: (next) => onSavedChange?.(person.username, next),
    onRevert: (previous) => onSavedRevert?.(person.username, previous),
  });
  const place = [formatPlace(person, meta.countries), labelOf(meta.statuses, person.status)]
    .filter(Boolean)
    .join(' · ');

  return (
    <article className={styles.card}>
      <div className={styles.head}>
        <Avatar
          id={person.username}
          firstName={person.first_name}
          lastName={person.last_name}
          src={person.avatar_url}
        />
        <div className={styles.who}>
          <h3 className={`${styles.name} user-text`}>{name}</h3>
          <p className={`${styles.field} user-text`}>{person.field_label}</p>
        </div>
      </div>
      <p className={`${styles.place} user-text`}>{place}</p>
      {person.bio && <p className={`${styles.bio} user-text`}>{person.bio}</p>}
      <div className={styles.tags}>
        {person.interests.slice(0, MAX_TAGS).map((code) => (
          <Tag key={code}>{labelOf(meta.interests, code)}</Tag>
        ))}
      </div>
      <div className={styles.actions}>
        <ButtonLink to={`/u/${person.username}`} size="sm" className={styles.view}>
          {t.viewProfile}
        </ButtonLink>
        <MessageRequestButton person={person} />
        <button
          type="button"
          className={[styles.bookmark, saved && styles.bookmarked].filter(Boolean).join(' ')}
          aria-pressed={saved}
          aria-label={saved ? t.unsave(name) : t.save(name)}
          disabled={busy}
          onClick={toggle}
        >
          <Bookmark size={16} fill={saved ? 'currentColor' : 'none'} aria-hidden="true" />
        </button>
      </div>
    </article>
  );
}
