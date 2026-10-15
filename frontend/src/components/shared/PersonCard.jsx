import { Bookmark, MessageCircle } from 'lucide-react';
import useMeta from '../../api/useMeta.js';
import { formatPlace, fullName, labelOf } from '../../lib/labels.js';
import { texts } from '../../texts/en.js';
import Avatar from '../ui/Avatar.jsx';
import Button from '../ui/Button.jsx';
import ButtonLink from '../ui/ButtonLink.jsx';
import Tag from '../ui/Tag.jsx';
import useToast from '../ui/useToast.js';
import styles from './PersonCard.module.css';

const t = texts.card;
const MAX_TAGS = 3;

// Карточка человека (legacy .rc) в Discover и Saved. person — формат Card (docs/SPEC.md §3.6);
// city/country могут быть null (скрыты приватностью). «Message» и закладка пока без функции:
// тост «Coming soon» (подключим в B6/B7 и B9).
export default function PersonCard({ person }) {
  const name = fullName(person);
  const { meta } = useMeta(); // карточки показываются после загрузки справочников (MetaGate)
  const showToast = useToast();
  const comingSoon = () => showToast(texts.app.comingSoon);
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
        <Button variant="ghost" size="sm" aria-label={t.messageLabel(name)} onClick={comingSoon}>
          <MessageCircle size={14} aria-hidden="true" />
          {t.message}
        </Button>
        <button
          type="button"
          className={styles.bookmark}
          aria-label={t.save(name)}
          onClick={comingSoon}
        >
          <Bookmark size={16} aria-hidden="true" />
        </button>
      </div>
    </article>
  );
}
