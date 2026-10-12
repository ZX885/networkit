import { Check, CheckCheck } from 'lucide-react';
import { texts } from '../../../texts/en.js';
import { formatTime } from '../format.js';
import styles from './MessageBubble.module.css';

// Пузырь сообщения (legacy .msg-bubble). Текст выводится как текст (React экранирует),
// переносы строк сохраняются стилем pre-wrap. У своих — галочки «отправлено / прочитано».
export default function MessageBubble({ message }) {
  const mine = message.sender_is_me;
  const Ticks = message.seen_at ? CheckCheck : Check;

  return (
    <div className={[styles.bubble, mine ? styles.mine : styles.theirs].join(' ')}>
      <p className={`${styles.body} user-text`}>{message.body}</p>
      <div className={styles.meta}>
        <time className={styles.time} dateTime={message.created_at}>
          {formatTime(message.created_at)}
        </time>
        {mine && (
          <span className={message.seen_at ? styles.seen : styles.sent}>
            <Ticks size={13} aria-hidden="true" />
            <span className="visually-hidden">
              {message.seen_at ? texts.messages.seen : texts.messages.sent}
            </span>
          </span>
        )}
      </div>
    </div>
  );
}
