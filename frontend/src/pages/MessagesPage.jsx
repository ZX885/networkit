import { useCallback, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { MessageCircle } from 'lucide-react';
import useMeta from '../api/useMeta.js';
import useSummary from '../app/providers/useSummary.js';
import MetaGate from '../components/shared/MetaGate.jsx';
import PageHeader from '../components/shared/PageHeader.jsx';
import EmptyState from '../components/ui/EmptyState.jsx';
import ChatWindow from '../features/messages/components/ChatWindow.jsx';
import ConversationList from '../features/messages/components/ConversationList.jsx';
import MessageTabs from '../features/messages/components/MessageTabs.jsx';
import useConversationList from '../features/messages/hooks/useConversationList.js';
import { texts } from '../texts/en.js';
import styles from './MessagesPage.module.css';

const t = texts.messages;
const BOXES = ['chats', 'requests', 'sent'];

// Сообщения: /messages и /messages/:conversationId. Вкладки Chats / Requests / Sent, слева список,
// справа чат. Вкладка хранится в адресе (?box=), поэтому переживает перезагрузку.
function MessagesLayout() {
  const { conversationId } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const { meta } = useMeta();
  const { summary, refresh } = useSummary();
  const boxParam = searchParams.get('box');
  const box = BOXES.includes(boxParam) ? boxParam : 'chats';
  const [pageState, setPageState] = useState({ box, page: 1 });
  const page = pageState.box === box ? pageState.page : 1;

  const list = useConversationList(
    box,
    page,
    `${summary.unread_messages}/${summary.pending_requests}`,
  );
  const { reload } = list;

  // Что-то изменилось (сообщение, принятие, прочтение): обновляем список и счётчики
  const onChanged = useCallback(() => {
    reload();
    refresh().catch(() => {});
  }, [reload, refresh]);

  function changeBox(next) {
    setSearchParams({ box: next }, { replace: true });
  }

  // Получатель принял запрос → диалог переходит во вкладку Chats; отклонил → возвращаемся к списку
  function onDecided(conversation) {
    if (conversation.status === 'accepted') {
      navigate(`/messages/${conversation.id}?box=chats`, { replace: true });
    } else {
      navigate(`/messages?box=${box}`, { replace: true });
    }
  }

  return (
    <>
      <PageHeader title={t.title} />
      <div className={styles.layout} data-chat={conversationId ? 'open' : 'closed'}>
        <div className={styles.list}>
          <MessageTabs
            box={box}
            counts={{ chats: summary.unread_messages, requests: summary.pending_requests }}
            onChange={changeBox}
          />
          <ConversationList
            box={box}
            data={list.data}
            error={list.error}
            page={page}
            onPage={(next) => setPageState({ box, page: next })}
            onRetry={list.retry}
          />
        </div>
        <div className={styles.right}>
          {conversationId ? (
            <ChatWindow
              key={conversationId}
              conversationId={conversationId}
              maxLength={meta.limits.message_max}
              onChanged={onChanged}
              onDecided={onDecided}
            />
          ) : (
            <div className={styles.empty}>
              <EmptyState
                icon={<MessageCircle size={36} />}
                title={t.noSelectionTitle}
                description={t.noSelectionText}
              />
            </div>
          )}
        </div>
      </div>
    </>
  );
}

export default function MessagesPage() {
  return (
    <MetaGate>
      <MessagesLayout />
    </MetaGate>
  );
}
