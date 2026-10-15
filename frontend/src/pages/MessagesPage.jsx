import { MessageCircle } from 'lucide-react';
import PageHeader from '../components/shared/PageHeader.jsx';
import EmptyState from '../components/ui/EmptyState.jsx';
import { texts } from '../texts/en.js';

const t = texts.messages;

// Сообщения: пока не готовы (шаг B7). Оболочка приложения работает, вместо диалогов — честная заглушка,
// без вымышленных людей.
export default function MessagesPage() {
  return (
    <>
      <PageHeader title={t.title} />
      <EmptyState
        icon={<MessageCircle size={36} />}
        title={t.comingSoonTitle}
        description={t.comingSoonText}
      />
    </>
  );
}
