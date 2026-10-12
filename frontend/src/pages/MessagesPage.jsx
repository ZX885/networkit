import { MessageCircle } from 'lucide-react';
import { useParams } from 'react-router-dom';
import PageHeader from '../components/shared/PageHeader.jsx';
import Button from '../components/ui/Button.jsx';
import EmptyState from '../components/ui/EmptyState.jsx';
import Spinner from '../components/ui/Spinner.jsx';
import ChatWindow from '../features/messages/components/ChatWindow.jsx';
import ConversationList from '../features/messages/components/ConversationList.jsx';
import { useConversation, useConversations } from '../features/messages/hooks/useMessagesData.js';
import { texts } from '../texts/en.js';
import styles from './MessagesPage.module.css';

const t = texts.messages;

// Сообщения (MOCK: api/mock/messages.js). Слева диалоги, справа чат; на ≤580px показывается что-то одно.
export default function MessagesPage() {
  const { conversationId } = useParams();
  const list = useConversations();
  const chat = useConversation(conversationId);

  let right;
  if (!conversationId) {
    right = (
      <div className={styles.empty}>
        <EmptyState
          icon={<MessageCircle size={36} />}
          title={t.emptyTitle}
          description={t.emptyText}
        />
      </div>
    );
  } else if (chat.loading) {
    right = (
      <div className={styles.empty}>
        <Spinner size="lg" tone="primary" label={texts.app.loading} />
      </div>
    );
  } else if (chat.error) {
    right = (
      <div className={styles.empty}>
        <EmptyState
          title={texts.app.errorTitle}
          action={<Button onClick={chat.retry}>{texts.app.retry}</Button>}
        />
      </div>
    );
  } else if (!chat.data) {
    right = (
      <div className={styles.empty} role="alert">
        <EmptyState title={t.notFoundTitle} />
      </div>
    );
  } else {
    right = <ChatWindow key={conversationId} conversation={chat.data} />;
  }

  return (
    <>
      <PageHeader title={t.title} />
      {/* data-chat: на узком экране при открытом чате прячем список (и наоборот) */}
      <div className={styles.layout} data-chat={conversationId ? 'open' : 'closed'}>
        <div className={styles.list}>
          <ConversationList conversations={list.data} />
        </div>
        <div className={styles.right}>{right}</div>
      </div>
    </>
  );
}
