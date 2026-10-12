import useAuth from '../../../app/providers/useAuth.js';
import Field from '../../../components/ui/Field.jsx';
import { fullName } from '../../../lib/labels.js';
import { texts } from '../../../texts/en.js';
import SettingsPanel from './SettingsPanel.jsx';

const t = texts.settings.account;

// Account: имя и username только для чтения (в этой версии не меняются)
export default function AccountTab() {
  const { user } = useAuth();

  return (
    <SettingsPanel title={t.title} subtitle={t.subtitle}>
      <Field label={t.displayName} value={fullName(user)} readOnly hint={t.readOnly} />
      <Field label={t.username} value={user.username} readOnly hint={t.readOnly} />
    </SettingsPanel>
  );
}
