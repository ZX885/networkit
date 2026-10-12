import { Fragment, useEffect, useRef } from 'react';
import { ChevronLeft } from 'lucide-react';
import { Link } from 'react-router-dom';
import { markRead, sendMessage } from '../../../api/mock/messages.js';
import Avatar from '../../../components/ui/Avatar.jsx';
import { fullName } from '../../../lib/labels.js';
import { texts } from '../../../texts/en.js';
import { formatDay } from '../format.js';
import MessageBubble from './MessageBubble.jsx';
import MessageInput from './MessageInput.jsx';
import styles from './ChatWindow.module.css';

const t = texts.messages;

// Окно чата (правая колонка): шапка с «View profile», сообщения с разделителями дней, поле ввода.
// Открытый диалог помечается прочитанным; список прокручивается к последнему сообщению.
export default function ChatWindow({ conversation }) {
  const { id, other_user: user, messages } = conversation;
  const listRef = useRef(null);
  const unread = conversation.unread_count;

  useEffect(() => {
    if (unread > 0) markRead(id);
  }, [id, unread]);

  useEffect(() => {
    const list = listRef.current;
    list.scrollTop = list.scrollHeight;
  }, [id, messages.length]);

  const days = messages.map((message) => formatDay(message.created_at));
  return (
    <section className={styles.chat} aria-label={t.chatLabel(fullName(user))}>
      <header className={styles.header}>
        <Link to="/messages" className={styles.back} aria-label={t.back}>
          <ChevronLeft size={20} aria-hidden="true" />
        </Link>
        <Avatar
          id={user.username}
          firstName={user.first_name}
          lastName={user.last_name}
          src={user.avatar_url}
          size="sm"
        />
        <div className={styles.who}>
          <h2 className={`${styles.name} user-text`}>{fullName(user)}</h2>
          <p className={`${styles.field} user-text`}>{user.field_label}</p>
        </div>
        <Link to={`/u/${user.username}`} className={styles.profile}>
          {t.viewProfile}
        </Link>
      </header>
      <div
        ref={listRef}
        className={styles.messages}
        role="log"
        aria-live="polite"
        aria-label={t.messagesLabel}
      >
        {messages.length === 0 && <p className={styles.none}>{t.noMessages}</p>}
        {messages.map((message, index) => {
          const showDay = index === 0 || days[index] !== days[index - 1];
          return (
            <Fragment key={message.id}>
              {showDay && <div className={styles.day}>{days[index]}</div>}
              <MessageBubble message={message} />
            </Fragment>
          );
        })}
      </div>
      <MessageInput onSend={(body) => sendMessage(id, body)} />
    </section>
  );
}
