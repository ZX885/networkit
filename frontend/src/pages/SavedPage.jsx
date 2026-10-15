import { useEffect } from 'react';
import { Bookmark } from 'lucide-react';
import { useSearchParams } from 'react-router-dom';
import MetaGate from '../components/shared/MetaGate.jsx';
import PageHeader from '../components/shared/PageHeader.jsx';
import Button from '../components/ui/Button.jsx';
import ButtonLink from '../components/ui/ButtonLink.jsx';
import EmptyState from '../components/ui/EmptyState.jsx';
import Pagination from '../components/ui/Pagination.jsx';
import PeopleGrid from '../features/discover/components/PeopleGrid.jsx';
import useSaved from '../features/saved/hooks/useSaved.js';
import { apiErrorText } from '../lib/apiErrors.js';
import { texts } from '../texts/en.js';

const t = texts.saved;

// Избранное: GET /api/saved/ (новые закладки первыми), страница в адресе (?page=). Карточки те же,
// что в Discover. Снятая закладка сразу уходит из списка и возвращается, если запрос не удался.
export default function SavedPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const parsed = Number.parseInt(searchParams.get('page') ?? '', 10);
  const page = Number.isInteger(parsed) && parsed > 0 ? parsed : 1;
  const { loading, error, data, retry, remove, restore } = useSaved(page);

  const setPage = (next, options) =>
    setSearchParams(next > 1 ? { page: String(next) } : {}, options);

  // Страницы с таким номером нет (старая ссылка) или текущая опустела после снятия закладок
  const pageMissing = error?.status === 404 && page > 1;
  const pageEmptied = data && data.results.length === 0 && data.count > 0 && page > 1;
  useEffect(() => {
    if (pageMissing) setPage(1, { replace: true });
    else if (pageEmptied) setPage(page - 1, { replace: true });
  }, [pageMissing, pageEmptied]); // eslint-disable-line react-hooks/exhaustive-deps

  let content = (
    <PeopleGrid
      people={data?.results ?? null}
      onSavedChange={(username, saved) => !saved && remove(username)}
      onSavedRevert={(username) => restore(username)}
    />
  );
  if (error && !pageMissing) {
    content = (
      <EmptyState
        title={texts.app.errorTitle}
        description={apiErrorText(error)}
        action={<Button onClick={retry}>{texts.app.retry}</Button>}
      />
    );
  } else if (data && data.count === 0) {
    content = (
      <EmptyState
        icon={<Bookmark size={36} />}
        title={t.emptyTitle}
        description={t.emptyText}
        action={<ButtonLink to="/discover">{t.emptyAction}</ButtonLink>}
      />
    );
  }

  return (
    <>
      <PageHeader title={t.title} />
      <MetaGate>
        <div aria-live="polite" aria-busy={loading}>
          {content}
        </div>
        {data && data.count > 0 && (
          <Pagination
            page={page}
            pageCount={data.pageCount}
            onChange={(next) => {
              setPage(next);
              window.scrollTo({ top: 0 });
            }}
            label={texts.discover.pagination.label}
            prevLabel={texts.discover.pagination.prev}
            nextLabel={texts.discover.pagination.next}
            pageLabel={texts.discover.pagination.page}
          />
        )}
      </MetaGate>
    </>
  );
}
