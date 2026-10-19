import { texts } from '../../../texts/en.js';
import ChangeEmailForm from './ChangeEmailForm.jsx';
import ChangePasswordForm from './ChangePasswordForm.jsx';
import SettingsPanel from './SettingsPanel.jsx';

const t = texts.settings.security;

// Security: смена пароля и смена email
export default function SecurityTab() {
  return (
    <SettingsPanel title={t.title} subtitle={t.subtitle}>
      <ChangePasswordForm />
      <ChangeEmailForm />
    </SettingsPanel>
  );
}
