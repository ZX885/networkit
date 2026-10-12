import { useState } from 'react';
import useAuth from '../../../app/providers/useAuth.js';
import useToast from '../../../components/ui/useToast.js';
import { ADULT_AGE } from '../../../constants/rules.js';
import { texts } from '../../../texts/en.js';
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

// Privacy: 5 тумблеров. DEMO: пока меняют только локальное состояние страницы (на сервер не уходят,
// после перезагрузки вернутся прежние значения), поэтому тост честно говорит «Saved (demo)».
export default function PrivacyTab() {
  const { user } = useAuth();
  const showToast = useToast();
  const [values, setValues] = useState(user.privacy);
  const isMinor = user.is_minor || user.age < ADULT_AGE; // контакты младше 18 лет запрещены

  function change(key, next) {
    setValues((prev) => ({ ...prev, [key]: next }));
    showToast(texts.app.savedDemo);
  }

  return (
    <SettingsPanel title={t.title} subtitle={t.subtitle}>
      {ROWS.map((row) => {
        const locked = row.key === 'show_contacts' && isMinor;
        return (
          <PrivacyRow
            key={row.key}
            title={row.title}
            hint={locked ? t.showContactsMinor : row.hint}
            checked={locked ? false : values[row.key]}
            disabled={locked}
            onChange={(next) => change(row.key, next)}
          />
        );
      })}
    </SettingsPanel>
  );
}
