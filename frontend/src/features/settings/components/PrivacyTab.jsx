import useAuth from '../../../app/providers/useAuth.js';
import Button from '../../../components/ui/Button.jsx';
import EmptyState from '../../../components/ui/EmptyState.jsx';
import Spinner from '../../../components/ui/Spinner.jsx';
import { apiErrorText } from '../../../lib/apiErrors.js';
import { texts } from '../../../texts/en.js';
import usePrivacy from '../hooks/usePrivacy.js';
import PrivacyRow from './PrivacyRow.jsx';
import SettingsPanel from './SettingsPanel.jsx';

const t = texts.settings.privacy;
const ROWS = [
  { key: 'show_location', title: t.showLocation, hint: t.showLocationHint },
  { key: 'show_university', title: t.showUniversity, hint: t.showUniversityHint },
  { key: 'show_contacts', title: t.showContacts, hint: t.showContactsHint },
  { key: 'show_in_search', title: t.showInSearch, hint: t.showInSearchHint },
  { key: 'show_join_date', title: t.showJoinDate, hint: t.showJoinDateHint },
];

// Privacy: 5 тумблеров, данные и сохранение через /api/me/privacy/ (сразу при переключении).
// Для младше 18 лет «Show contacts» заблокирован (решает сервер, is_minor).
export default function PrivacyTab() {
  const { user } = useAuth();
  const { loading, error, values, pending, toggle, retry } = usePrivacy();

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
  } else {
    body = ROWS.map((row) => {
      const locked = row.key === 'show_contacts' && user.is_minor;
      return (
        <PrivacyRow
          key={row.key}
          title={row.title}
          hint={locked ? t.showContactsMinor : row.hint}
          checked={locked ? false : values[row.key]}
          disabled={locked || pending.includes(row.key)}
          onChange={(next) => toggle(row.key, next)}
        />
      );
    });
  }

  return (
    <SettingsPanel title={t.title} subtitle={t.subtitle}>
      {body}
    </SettingsPanel>
  );
}
