import { NavLink } from 'react-router-dom';
import Avatar from '../../../components/ui/Avatar.jsx';
import { fullName } from '../../../lib/labels.js';
import { texts } from '../../../texts/en.js';
import { formatListTime } from '../format.js';
import styles from './ConversationItem.module.css';

const t = texts.messages;
const PREVIEW_LENGTH = 38;

// Строка диалога в списке (legacy .conv-item): аватар, имя, превью, время, бейдж непрочитанных
export default function ConversationItem({ conversation, box }) {
  const { other_user: user, last_message: last, unread_count: unread } = conversation;
  const preview = last
    ? (last.sender_is_me ? t.you : '') +
      last.body.slice(0, PREVIEW_LENGTH) +
      (last.body.length > PREVIEW_LENGTH ? '…' : '')
    : '';

  return (
    <NavLink
      to={`/messages/${conversation.id}?box=${box}`}
      className={({ isActive }) =>
        [styles.item, isActive && styles.active].filter(Boolean).join(' ')
      }
    >
      <Avatar
        id={user.username}
        firstName={user.first_name}
        lastName={user.last_name}
        src={user.avatar_url}
      />
      <span className={styles.info}>
        <span className={`${styles.name} user-text`}>{fullName(user)}</span>
        <span className={`${styles.preview} user-text`}>{preview}</span>
      </span>
      <span className={styles.side}>
        <span className={styles.time}>{formatListTime(conversation.last_message_at)}</span>
        {unread > 0 && (
          <span className={styles.unread}>
            {unread}
            <span className="visually-hidden"> {t.unread(unread)}</span>
          </span>
        )}
      </span>
    </NavLink>
  );
}
