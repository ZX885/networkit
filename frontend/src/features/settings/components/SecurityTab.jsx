import { texts } from '../../../texts/en.js';
import ChangeEmailForm from './ChangeEmailForm.jsx';
import ChangePasswordForm from './ChangePasswordForm.jsx';
import SettingsPanel from './SettingsPanel.jsx';
import styles from './SecurityTab.module.css';

const t = texts.settings.security;

// Security: смена пароля и email (UI с проверками; отправка подключается в B4)
export default function SecurityTab() {
  return (
    <SettingsPanel title={t.title} subtitle={t.subtitle}>
      <ChangePasswordForm />
      <hr className={styles.divider} />
      <ChangeEmailForm />
    </SettingsPanel>
  );
}
