import { useState } from 'react';
import { Search } from 'lucide-react';
import Button from '../../../components/ui/Button.jsx';
import Pagination from '../../../components/ui/Pagination.jsx';
import Spinner from '../../../components/ui/Spinner.jsx';
import { fullName } from '../../../lib/labels.js';
import { texts } from '../../../texts/en.js';
import ConversationItem from './ConversationItem.jsx';
import styles from './ConversationList.module.css';

const t = texts.messages;

// Левая колонка: поиск по имени среди загруженных диалогов вкладки и сам список.
// data = null — идёт загрузка; для каждой вкладки (box) свой понятный текст пустого состояния.
export default function ConversationList({ box, data, error, page, onPage, onRetry }) {
  const [query, setQuery] = useState('');
  const needle = query.trim().toLowerCase();
  const conversations = data?.results ?? null;
  const shown = (conversations ?? []).filter((c) =>
    fullName(c.other_user).toLowerCase().includes(needle),
  );
  const empty = t.empty[box];

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
        {!conversations && !error && (
          <div className={styles.center}>
            <Spinner tone="primary" label={texts.app.loading} />
          </div>
        )}
        {error && (
          <div className={styles.center} role="alert">
            <Button size="sm" onClick={onRetry}>
              {texts.app.retry}
            </Button>
          </div>
        )}
        {conversations && conversations.length === 0 && (
          <div className={styles.empty} role="status">
            <p className={styles.emptyTitle}>{empty.title}</p>
            <p>{empty.text}</p>
          </div>
        )}
        {conversations && conversations.length > 0 && shown.length === 0 && (
          <p className={styles.empty} role="status">
            {t.empty.noMatches}
          </p>
        )}
        {shown.map((conversation) => (
          <ConversationItem key={conversation.id} conversation={conversation} box={box} />
        ))}
        {data && (
          <Pagination
            page={page}
            pageCount={data.pageCount}
            onChange={onPage}
            label={texts.discover.pagination.label}
            prevLabel={texts.discover.pagination.prev}
            nextLabel={texts.discover.pagination.next}
            pageLabel={texts.discover.pagination.page}
          />
        )}
      </div>
    </section>
  );
}
