import { ChevronLeft } from 'lucide-react';
import { Link } from 'react-router-dom';
import Avatar from '../../../components/ui/Avatar.jsx';
import Button from '../../../components/ui/Button.jsx';
import Spinner from '../../../components/ui/Spinner.jsx';
import { fullName } from '../../../lib/labels.js';
import { texts } from '../../../texts/en.js';
import ChatMessages from './ChatMessages.jsx';
import MessageInput from './MessageInput.jsx';
import RequestBar from './RequestBar.jsx';
import SafetyNotice from './SafetyNotice.jsx';
import useChat from '../hooks/useChat.js';
import styles from './ChatWindow.module.css';

const t = texts.messages;

// Окно чата (правая колонка): шапка с «View profile», лента, поле ввода (только в принятом диалоге)
// или полоса запроса, предупреждение безопасности. onChanged — обновить список и счётчики;
// onDecided(conversation) — получатель принял / отклонил запрос.
export default function ChatWindow({ conversationId, maxLength, onChanged, onDecided }) {
  const chat = useChat(conversationId, onChanged);
  const { status, conversation } = chat;

  if (status !== 'ready') {
    return (
      <section className={styles.chat} aria-label={t.messagesLabel}>
        <header className={styles.header}>
          <Link to="/messages" className={styles.back} aria-label={t.back}>
            <ChevronLeft size={20} aria-hidden="true" />
          </Link>
        </header>
        <div className={styles.state} role={status === 'loading' ? 'status' : 'alert'}>
          {status === 'loading' && <Spinner tone="primary" label={t.loading} />}
          {status === 'notFound' && (
            <>
              <h2 className={styles.stateTitle}>{t.notFoundTitle}</h2>
              <p>{t.notFoundText}</p>
            </>
          )}
          {status === 'error' && (
            <>
              <p>{t.errors.loadFailed}</p>
              <Button size="sm" onClick={chat.retry}>
                {texts.app.retry}
              </Button>
            </>
          )}
        </div>
      </section>
    );
  }

  const user = conversation.other_user;
  const accepted = conversation.status === 'accepted';

  async function decide(accept) {
    const result = await (accept ? chat.accept() : chat.decline());
    onDecided?.(result);
  }

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
      <ChatMessages
        conversationId={conversationId}
        messages={chat.messages}
        hasMoreOlder={chat.hasMoreOlder}
        loadingOlder={chat.loadingOlder}
        onLoadOlder={chat.loadOlder}
      />
      {accepted ? (
        <MessageInput key={conversationId} onSend={chat.send} maxLength={maxLength} />
      ) : (
        <RequestBar
          conversation={conversation}
          onAccept={() => decide(true)}
          onDecline={() => decide(false)}
        />
      )}
      <div className={styles.notes}>
        <SafetyNotice />
        {accepted && <p className={styles.encryption}>{t.notEncrypted}</p>}
      </div>
    </section>
  );
}
