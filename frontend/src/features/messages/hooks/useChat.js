import { useCallback, useEffect, useRef, useState } from 'react';
import {
  acceptConversation,
  declineConversation,
  getConversation,
  listMessages,
  markRead,
  sendMessage,
} from '../../../api/conversations.js';
import usePolling from '../../../lib/usePolling.js';

const POLL_MS = 5000; // открытый чат опрашивается раз в 5 секунд (только пока вкладка видна)
const REFRESH_WINDOW = 30; // сколько последних сообщений перечитываем, чтобы обновить «seen»

// Объединяет сообщения по id (новые данные заменяют старые: так обновляется seen_at), по возрастанию id
export function mergeMessages(current, incoming) {
  const byId = new Map(current.map((message) => [message.id, message]));
  incoming.forEach((message) => byId.set(message.id, message));
  return [...byId.values()].sort((a, b) => a.id - b.id);
}

// Состояние открытого диалога: сам диалог, сообщения (по возрастанию id), «загрузить более ранние»,
// отправка, accept/decline, опрос новых сообщений after=<последний id>. onChanged() сообщает наружу, что
// список диалогов и счётчики нужно обновить.
export default function useChat(conversationId, onChanged) {
  const [state, setState] = useState({
    id: null,
    status: 'loading', // loading | ready | notFound | error
    error: null,
    conversation: null,
    messages: [],
    hasMoreOlder: false,
  });
  const [attempt, setAttempt] = useState(0);
  const [loadingOlder, setLoadingOlder] = useState(false);
  const stateRef = useRef(state);
  useEffect(() => {
    stateRef.current = state;
  });

  const ready = state.id === conversationId && state.status === 'ready';

  // Помечает входящие прочитанными (только в принятом диалоге) и локально, и на сервере
  const readIncoming = useCallback(
    async (conversation, messages) => {
      const unseen = messages.some((m) => !m.sender_is_me && !m.seen_at);
      if (conversation.status !== 'accepted' || !unseen) return messages;
      await markRead(conversationId);
      onChanged?.();
      const now = new Date().toISOString();
      return messages.map((m) => (!m.sender_is_me && !m.seen_at ? { ...m, seen_at: now } : m));
    },
    [conversationId, onChanged],
  );

  // Первая загрузка: диалог + последние сообщения
  useEffect(() => {
    const controller = new AbortController();
    let ignore = false;
    Promise.all([
      getConversation(conversationId, { signal: controller.signal }),
      listMessages(conversationId, {}, { signal: controller.signal }),
    ])
      .then(async ([conversation, page]) => {
        const messages = await readIncoming(conversation, page.results).catch(() => page.results);
        if (ignore) return;
        setState({
          id: conversationId,
          status: 'ready',
          error: null,
          conversation,
          messages,
          hasMoreOlder: page.has_more_older,
        });
      })
      .catch((error) => {
        if (ignore) return;
        const status = error.status === 404 ? 'notFound' : 'error';
        setState((prev) => ({ ...prev, id: conversationId, status, error }));
      });
    return () => {
      ignore = true;
      controller.abort();
    };
  }, [conversationId, attempt, readIncoming]);

  const patch = useCallback((changes) => setState((prev) => ({ ...prev, ...changes })), []);

  // Опрос: новые сообщения after=<последний id>; пока запрос не принят — ещё и статус диалога;
  // если есть мои непрочитанные собеседником — перечитываем последние, чтобы появилась отметка «seen»
  usePolling(
    async () => {
      const current = stateRef.current;
      if (current.id !== conversationId || current.status !== 'ready') return;
      let { conversation, messages } = current;
      let changed = false;
      const lastId = messages.at(-1)?.id;
      const fresh = await listMessages(conversationId, lastId ? { after: lastId } : {});
      if (fresh.results.length > 0) {
        messages = mergeMessages(messages, fresh.results);
        changed = true;
      }
      if (conversation.status !== 'accepted') {
        const latest = await getConversation(conversationId);
        if (latest.status !== conversation.status) changed = true;
        conversation = latest;
      } else if (messages.some((m) => m.sender_is_me && !m.seen_at)) {
        const window = await listMessages(conversationId, { limit: REFRESH_WINDOW });
        messages = mergeMessages(messages, window.results);
      }
      messages = await readIncoming(conversation, messages).catch(() => messages);
      if (stateRef.current.id !== conversationId) return;
      patch({ conversation, messages });
      if (changed) onChanged?.();
    },
    POLL_MS,
    ready,
  );

  async function loadOlder() {
    const oldest = state.messages[0]?.id;
    if (!oldest || loadingOlder) return;
    setLoadingOlder(true);
    try {
      const page = await listMessages(conversationId, { before: oldest });
      setState((prev) => ({
        ...prev,
        messages: mergeMessages(prev.messages, page.results),
        hasMoreOlder: page.has_more_older,
      }));
    } finally {
      setLoadingOlder(false);
    }
  }

  async function send(body) {
    const message = await sendMessage(conversationId, body);
    setState((prev) => ({
      ...prev,
      messages: mergeMessages(prev.messages, [message]),
      conversation: { ...prev.conversation, last_message_at: message.created_at },
    }));
    onChanged?.();
    return message;
  }

  async function decide(accept) {
    const conversation = await (accept
      ? acceptConversation(conversationId)
      : declineConversation(conversationId));
    patch({ conversation });
    onChanged?.();
    return conversation;
  }

  return {
    status: ready ? 'ready' : state.id === conversationId ? state.status : 'loading',
    error: state.id === conversationId ? state.error : null,
    conversation: ready ? state.conversation : null,
    messages: ready ? state.messages : [],
    hasMoreOlder: ready && state.hasMoreOlder,
    loadingOlder,
    retry: () => {
      setState((prev) => ({ ...prev, id: null, status: 'loading', error: null }));
      setAttempt((n) => n + 1);
    },
    loadOlder,
    send,
    accept: () => decide(true),
    decline: () => decide(false),
  };
}
