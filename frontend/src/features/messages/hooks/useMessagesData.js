import { useEffect, useState, useSyncExternalStore } from 'react';
import {
  getConversation,
  getMessagesVersion,
  listConversations,
  subscribeMessages,
} from '../../../api/mock/messages.js';

// Версия данных сообщений: меняется, когда пришло/ушло сообщение или диалог прочитан (MOCK)
const useVersion = () => useSyncExternalStore(subscribeMessages, getMessagesVersion);

// Загрузка по «ключу запроса». scope — что именно грузим (arg и повтор по кнопке); version —
// обновление данных: при смене version прежние данные остаются на экране, без мигания загрузки.
// loader — функция вне компонента (стабильная), arg — её единственный аргумент.
function useLoad(loader, arg) {
  const version = useVersion();
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState({ key: null, scope: null, data: null, error: false });
  const scope = `${arg}#${attempt}`;
  const key = `${scope}#${version}`;

  useEffect(() => {
    let ignore = false;
    loader(arg).then(
      (data) => !ignore && setState({ key, scope, data, error: false }),
      () => !ignore && setState({ key, scope, data: null, error: true }),
    );
    return () => {
      ignore = true;
    };
  }, [loader, arg, key, scope]);

  const loading = state.scope !== scope;
  return {
    loading,
    error: !loading && state.error,
    data: loading ? null : state.data,
    retry: () => setAttempt((n) => n + 1),
  };
}

const loadList = () => listConversations();
const loadOne = (id) => (id ? getConversation(id) : Promise.resolve(null));

// Список диалогов (MOCK, потом GET /api/conversations/)
export function useConversations() {
  return useLoad(loadList, '');
}

// Один диалог с сообщениями; data = null и loading = false — такого диалога нет
export function useConversation(id) {
  return useLoad(loadOne, id ?? '');
}
