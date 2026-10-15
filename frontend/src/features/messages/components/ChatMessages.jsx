import { Fragment, useLayoutEffect, useRef } from 'react';
import Button from '../../../components/ui/Button.jsx';
import { texts } from '../../../texts/en.js';
import { formatDay } from '../format.js';
import MessageBubble from './MessageBubble.jsx';
import styles from './ChatMessages.module.css';

const t = texts.messages;
const NEAR_BOTTOM = 80; // px от низа, в пределах которых новые сообщения прокручивают список вниз

// Лента сообщений: разделители дней, «Load earlier messages». Прокрутка вниз при открытии диалога и
// при новых сообщениях (если человек не листает историю вверх). Текст сообщений — только как текст.
export default function ChatMessages({
  conversationId,
  messages,
  hasMoreOlder,
  loadingOlder,
  onLoadOlder,
}) {
  const listRef = useRef(null);
  const state = useRef({ id: null, firstId: null, height: 0, stick: true });
  const firstId = messages[0]?.id ?? null;
  const lastId = messages.at(-1)?.id ?? null;

  useLayoutEffect(() => {
    const list = listRef.current;
    const prev = state.current;
    if (prev.id !== conversationId) {
      list.scrollTop = list.scrollHeight; // новый диалог → вниз
    } else if (
      firstId !== prev.firstId &&
      prev.firstId !== null &&
      messages.some((m) => m.id === prev.firstId)
    ) {
      list.scrollTop += list.scrollHeight - prev.height; // подгрузили старые → не прыгаем
    } else if (prev.stick) {
      list.scrollTop = list.scrollHeight; // новое сообщение, а мы внизу
    }
    state.current = { id: conversationId, firstId, height: list.scrollHeight, stick: prev.stick };
  }, [conversationId, firstId, lastId, messages]);

  function handleScroll() {
    const list = listRef.current;
    state.current.stick = list.scrollHeight - list.scrollTop - list.clientHeight < NEAR_BOTTOM;
  }

  const days = messages.map((message) => formatDay(message.created_at));
  return (
    <div
      ref={listRef}
      className={styles.messages}
      role="log"
      aria-live="polite"
      aria-label={t.messagesLabel}
      onScroll={handleScroll}
    >
      {hasMoreOlder && (
        <div className={styles.earlier}>
          <Button size="sm" variant="ghost" loading={loadingOlder} onClick={onLoadOlder}>
            {t.loadEarlier}
          </Button>
        </div>
      )}
      {messages.length === 0 && <p className={styles.none}>{t.noMessages}</p>}
      {messages.map((message, index) => (
        <Fragment key={message.id}>
          {(index === 0 || days[index] !== days[index - 1]) && (
            <div className={styles.day}>{days[index]}</div>
          )}
          <MessageBubble message={message} />
        </Fragment>
      ))}
    </div>
  );
}
