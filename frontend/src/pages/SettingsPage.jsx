import { Outlet } from 'react-router-dom';
import PageHeader from '../components/shared/PageHeader.jsx';
import SettingsNav from '../features/settings/components/SettingsNav.jsx';
import { texts } from '../texts/en.js';
import styles from './SettingsPage.module.css';

// Настройки: вкладки Account / Privacy / Security / Danger — подмаршруты /settings/…
export default function SettingsPage() {
  return (
    <>
      <PageHeader title={texts.settings.title} />
      <div className={styles.layout}>
        <SettingsNav />
        <Outlet />
      </div>
    </>
  );
}
