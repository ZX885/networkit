import { Bookmark, MessageCircle } from 'lucide-react';
import { INTERESTS } from '../../constants/interests.js';
import { formatPlace, fullName, labelOf, statusLabel } from '../../lib/labels.js';
import { texts } from '../../texts/en.js';
import Avatar from '../ui/Avatar.jsx';
import Button from '../ui/Button.jsx';
import ButtonLink from '../ui/ButtonLink.jsx';
import Tag from '../ui/Tag.jsx';
import styles from './PersonCard.module.css';
import useOpenChat from './useOpenChat.js';
import useSavedToggle from './useSavedToggle.js';

const t = texts.card;
const MAX_TAGS = 3;

// Карточка человека (legacy .rc) в Discover и Saved. person — формат Card (docs/SPEC.md §3.6).
// onSavedChange(username, saved) — чтобы список (Saved) мог убрать карточку.
export default function PersonCard({ person, onSavedChange }) {
  const name = fullName(person);
  const openChat = useOpenChat();
  const { saved, busy, toggle } = useSavedToggle(person.username, person.is_saved, (next) =>
    onSavedChange?.(person.username, next),
  );
  const place = [formatPlace(person), statusLabel(person.status)].filter(Boolean).join(' · ');

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
          <Tag key={code}>{labelOf(INTERESTS, code)}</Tag>
        ))}
      </div>
      <div className={styles.actions}>
        <ButtonLink to={`/u/${person.username}`} size="sm" className={styles.view}>
          {t.viewProfile}
        </ButtonLink>
        <Button
          variant="ghost"
          size="sm"
          aria-label={t.messageLabel(name)}
          onClick={() => openChat(person.username)}
        >
          <MessageCircle size={14} aria-hidden="true" />
          {t.message}
        </Button>
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
