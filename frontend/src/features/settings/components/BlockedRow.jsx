import Avatar from '../../../components/ui/Avatar.jsx';
import Button from '../../../components/ui/Button.jsx';
import { fullName } from '../../../lib/labels.js';
import { texts } from '../../../texts/en.js';
import styles from './BlockedTab.module.css';

const t = texts.settings.blocked;

// Строка заблокированного: аватар, имя, @username и кнопка Unblock (текст только как текст)
export default function BlockedRow({ person, busy, disabled, onUnblock }) {
  const name = fullName(person);
  return (
    <li className={styles.row}>
      <Avatar
        id={person.username}
        firstName={person.first_name}
        lastName={person.last_name}
        src={person.avatar_url}
      />
      <div className={styles.who}>
        <p className={`${styles.name} user-text`}>{name}</p>
        <p className={`${styles.username} user-text`}>@{person.username}</p>
      </div>
      <Button
        variant="ghost"
        size="sm"
        aria-label={t.unblockLabel(name)}
        loading={busy}
        disabled={disabled}
        onClick={onUnblock}
      >
        {t.unblock}
      </Button>
    </li>
  );
}
