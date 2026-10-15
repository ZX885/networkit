import { useEffect, useState } from 'react';
import { Bookmark } from 'lucide-react';
import { listSavedPeople } from '../api/mock/people.js';
import MetaGate from '../components/shared/MetaGate.jsx';
import PageHeader from '../components/shared/PageHeader.jsx';
import Button from '../components/ui/Button.jsx';
import ButtonLink from '../components/ui/ButtonLink.jsx';
import EmptyState from '../components/ui/EmptyState.jsx';
import PeopleGrid from '../features/discover/components/PeopleGrid.jsx';
import { texts } from '../texts/en.js';

const t = texts.saved;

// Избранное (MOCK: api/mock/people.js, потом GET /api/saved/). Карточки те же, что в Discover.
export default function SavedPage() {
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState({ attempt: null, people: null, error: false });

  useEffect(() => {
    let ignore = false;
    listSavedPeople().then(
      (people) => !ignore && setState({ attempt, people, error: false }),
      () => !ignore && setState({ attempt, people: null, error: true }),
    );
    return () => {
      ignore = true;
    };
  }, [attempt]);

  // Снятый с закладки профиль сразу уходит из списка
  function handleSavedChange(username, saved) {
    if (saved) return;
    setState((prev) => ({ ...prev, people: prev.people.filter((p) => p.username !== username) }));
  }

  const loading = state.attempt !== attempt;
  const people = loading ? null : state.people;

  let content = <PeopleGrid people={people} onSavedChange={handleSavedChange} />;
  if (!loading && state.error) {
    content = (
      <EmptyState
        title={texts.app.errorTitle}
        action={<Button onClick={() => setAttempt((n) => n + 1)}>{texts.app.retry}</Button>}
      />
    );
  } else if (people?.length === 0) {
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
      </MetaGate>
    </>
  );
}
