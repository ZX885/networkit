import { SearchX } from 'lucide-react';
import PageHeader from '../components/shared/PageHeader.jsx';
import ButtonLink from '../components/ui/ButtonLink.jsx';
import EmptyState from '../components/ui/EmptyState.jsx';
import { texts } from '../texts/en.js';

// 404 внутри приложения (с сайдбаром)
export default function AppNotFoundPage() {
  return (
    <>
      <PageHeader title={texts.app.notFoundTitle} />
      <EmptyState
        icon={<SearchX size={36} />}
        title="404"
        description={texts.app.notFoundText}
        action={<ButtonLink to="/discover">{texts.app.notFoundAction}</ButtonLink>}
      />
    </>
  );
}
