import { useNavigate } from 'react-router-dom';
import { findConversationId } from '../../api/mock/messages.js';
import useToast from '../ui/useToast.js';
import { texts } from '../../texts/en.js';

// «Message»: открывает существующий диалог. Начало нового диалога появится вместе с настоящими
// сообщениями (MOCK: пока только заранее созданные диалоги).
export default function useOpenChat() {
  const navigate = useNavigate();
  const showToast = useToast();

  return function openChat(username) {
    const id = findConversationId(username);
    if (id) navigate(`/messages/${id}`);
    else showToast(texts.app.comingSoon);
  };
}
