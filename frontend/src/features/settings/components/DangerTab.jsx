import { useState } from 'react';
import Button from '../../../components/ui/Button.jsx';
import { texts } from '../../../texts/en.js';
import DeleteAccountModal from './DeleteAccountModal.jsx';
import SettingsPanel from './SettingsPanel.jsx';
import styles from './DangerTab.module.css';

const t = texts.settings.danger;

// Danger: удаление аккаунта (с подтверждением паролем и словом DELETE)
export default function DangerTab() {
  const [open, setOpen] = useState(false);

  return (
    <SettingsPanel title={t.title} subtitle={t.subtitle}>
      <section className={styles.card} aria-labelledby="delete-account-title">
        <h3 id="delete-account-title" className={styles.cardTitle}>
          {t.deleteTitle}
        </h3>
        <p className={styles.cardText}>{t.deleteText}</p>
        <Button variant="danger" onClick={() => setOpen(true)}>
          {t.deleteButton}
        </Button>
      </section>
      {open && <DeleteAccountModal onClose={() => setOpen(false)} />}
    </SettingsPanel>
  );
}
