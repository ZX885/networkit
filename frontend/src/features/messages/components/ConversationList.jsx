import { useState } from 'react';
import { Search } from 'lucide-react';
import Spinner from '../../../components/ui/Spinner.jsx';
import { fullName } from '../../../lib/labels.js';
import { texts } from '../../../texts/en.js';
import ConversationItem from './ConversationItem.jsx';
import styles from './ConversationList.module.css';

const t = texts.messages;

// Левая колонка: поиск по диалогам (по имени) и список. conversations = null — идёт загрузка.
export default function ConversationList({ conversations }) {
  const [query, setQuery] = useState('');
  const needle = query.trim().toLowerCase();
  const shown = (conversations ?? []).filter((c) =>
    fullName(c.other_user).toLowerCase().includes(needle),
  );

  let emptyText = null;
  if (conversations && conversations.length === 0) emptyText = t.noConversations;
  else if (conversations && shown.length === 0) emptyText = t.noMatches;

  return (
    <section className={styles.list} aria-label={t.listLabel}>
      <div className={styles.search}>
        <div className={styles.bar}>
          <Search size={16} className={styles.icon} aria-hidden="true" />
          <input
            type="search"
            className={styles.input}
            value={query}
            placeholder={t.searchPlaceholder}
            aria-label={t.searchLabel}
            autoComplete="off"
            onChange={(event) => setQuery(event.target.value)}
          />
        </div>
      </div>
      <div className={styles.items}>
        {!conversations && (
          <div className={styles.center}>
            <Spinner tone="primary" label={texts.app.loading} />
          </div>
        )}
        {emptyText && (
          <p className={styles.empty} role="status">
            {emptyText}
          </p>
        )}
        {shown.map((conversation) => (
          <ConversationItem key={conversation.id} conversation={conversation} />
        ))}
      </div>
    </section>
  );
}
