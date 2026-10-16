import { useState } from 'react';
import { Ban } from 'lucide-react';
import { unblockUser } from '../../../api/moderation.js';
import Button from '../../../components/ui/Button.jsx';
import EmptyState from '../../../components/ui/EmptyState.jsx';
import Pagination from '../../../components/ui/Pagination.jsx';
import Spinner from '../../../components/ui/Spinner.jsx';
import useToast from '../../../components/ui/useToast.js';
import { apiErrorText } from '../../../lib/apiErrors.js';
import { fullName } from '../../../lib/labels.js';
import { texts } from '../../../texts/en.js';
import BlockedRow from './BlockedRow.jsx';
import SettingsPanel from './SettingsPanel.jsx';
import useBlockedUsers from '../hooks/useBlockedUsers.js';
import styles from './BlockedTab.module.css';

const t = texts.settings.blocked;

// Blocked users: список тех, кого заблокировал я, и кнопка Unblock. Разблокировка — единственное
// место, где можно снять блокировку (профиль заблокированного для вас недоступен).
export default function BlockedTab() {
  const [page, setPage] = useState(1);
  const [busy, setBusy] = useState(null); // username, которого разблокируют сейчас
  const { loading, error, data, retry, remove } = useBlockedUsers(page);
  const showToast = useToast();

  async function unblock(person) {
    if (busy) return;
    setBusy(person.username);
    try {
      await unblockUser(person.username);
      showToast(t.unblockedToast(fullName(person)), 'success');
      remove(person.username);
      if (data.results.length === 1 && page > 1) setPage(page - 1); // страница опустела
    } catch (err) {
      showToast(apiErrorText(err), 'error');
    } finally {
      setBusy(null);
    }
  }

  let body;
  if (loading) {
    body = (
      <div role="status">
        <Spinner tone="primary" label={texts.app.loading} />
      </div>
    );
  } else if (error) {
    body = (
      <div role="alert">
        <EmptyState
          title={texts.app.errorTitle}
          description={apiErrorText(error)}
          action={<Button onClick={retry}>{texts.app.retry}</Button>}
        />
      </div>
    );
  } else if (data.count === 0) {
    body = <EmptyState icon={<Ban size={36} />} title={t.emptyTitle} description={t.emptyText} />;
  } else {
    body = (
      <>
        <ul className={styles.list} aria-label={t.listLabel}>
          {data.results.map((person) => (
            <BlockedRow
              key={person.username}
              person={person}
              busy={busy === person.username}
              disabled={busy !== null}
              onUnblock={() => unblock(person)}
            />
          ))}
        </ul>
        <Pagination
          page={page}
          pageCount={data.pageCount}
          onChange={setPage}
          label={texts.discover.pagination.label}
          prevLabel={texts.discover.pagination.prev}
          nextLabel={texts.discover.pagination.next}
          pageLabel={texts.discover.pagination.page}
        />
      </>
    );
  }

  return (
    <SettingsPanel title={t.title} subtitle={t.subtitle}>
      {body}
    </SettingsPanel>
  );
}
