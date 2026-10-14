import { useState } from 'react';
import { SearchX, SlidersHorizontal } from 'lucide-react';
import MetaGate from '../components/shared/MetaGate.jsx';
import PageHeader from '../components/shared/PageHeader.jsx';
import Button from '../components/ui/Button.jsx';
import EmptyState from '../components/ui/EmptyState.jsx';
import Pagination from '../components/ui/Pagination.jsx';
import FilterPanel from '../features/discover/components/FilterPanel.jsx';
import PeopleGrid from '../features/discover/components/PeopleGrid.jsx';
import SearchBar from '../features/discover/components/SearchBar.jsx';
import useDiscoverParams, { FILTER_KEYS } from '../features/discover/hooks/useDiscoverParams.js';
import usePeople from '../features/discover/hooks/usePeople.js';
import { texts } from '../texts/en.js';
import styles from './DiscoverPage.module.css';

const t = texts.discover;
const FILTERS_ID = 'discover-filters';

// Discover: поиск и фильтры (в адресе страницы), сетка людей, пагинация. Данные — MOCK (api/mock/people.js);
// списки для фильтров и названия на карточках — с сервера (MetaGate).
export default function DiscoverPage() {
  const { params, update } = useDiscoverParams();
  const { loading, error, data, retry } = usePeople(params);
  const [filtersOpen, setFiltersOpen] = useState(false);

  function clearAll() {
    const empty = Object.fromEntries(FILTER_KEYS.map((key) => [key, '']));
    update({ ...empty, q: '' });
  }

  function changePage(page) {
    update({ page });
    window.scrollTo({ top: 0 });
  }

  const empty = data && data.results.length === 0;

  return (
    <>
      <PageHeader title={t.title}>
        <Button
          variant="ghost"
          size="sm"
          className={styles.filtersToggle}
          aria-expanded={filtersOpen}
          aria-controls={FILTERS_ID}
          onClick={() => setFiltersOpen((open) => !open)}
        >
          <SlidersHorizontal size={14} aria-hidden="true" />
          {t.filtersShow}
        </Button>
        <SearchBar value={params.q} onSearch={(q) => update({ q }, { replace: true })} />
      </PageHeader>
      <MetaGate>
        <FilterPanel
          id={FILTERS_ID}
          open={filtersOpen}
          params={params}
          onChange={update}
          onClear={clearAll}
        />
        {/* aria-live: скринридер зачитывает число найденных или «Loading» */}
        <p className={styles.info} role="status" aria-live="polite">
          {loading ? t.loadingList : data && t.found(data.count)}
        </p>
        {error ? (
          <EmptyState
            title={texts.app.errorTitle}
            action={<Button onClick={retry}>{texts.app.retry}</Button>}
          />
        ) : empty ? (
          <EmptyState
            icon={<SearchX size={36} />}
            title={t.emptyTitle}
            description={t.emptyText}
            action={
              <Button variant="ghost" onClick={clearAll}>
                {t.clearAll}
              </Button>
            }
          />
        ) : (
          <PeopleGrid people={data?.results ?? null} />
        )}
        {data && (
          <Pagination
            page={params.page}
            pageCount={data.pageCount}
            onChange={changePage}
            label={t.pagination.label}
            prevLabel={t.pagination.prev}
            nextLabel={t.pagination.next}
            pageLabel={t.pagination.page}
          />
        )}
      </MetaGate>
    </>
  );
}
