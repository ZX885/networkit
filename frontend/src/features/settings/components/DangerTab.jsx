import { useState } from 'react';
import Button from '../../../components/ui/Button.jsx';
import useToast from '../../../components/ui/useToast.js';
import { texts } from '../../../texts/en.js';
import DeleteAccountModal from './DeleteAccountModal.jsx';
import SettingsPanel from './SettingsPanel.jsx';
import styles from './DangerTab.module.css';

const t = texts.settings.danger;

// Danger zone: удаление аккаунта. Пока без отправки: после подтверждения — «Coming soon».
export default function DangerTab() {
  const [open, setOpen] = useState(false);
  const showToast = useToast();

  return (
    <SettingsPanel title={t.title} subtitle={t.subtitle}>
      <div className={styles.box}>
        <h3 className={styles.title}>{t.deleteTitle}</h3>
        <p className={styles.text}>{t.deleteText}</p>
        <Button variant="danger" size="sm" onClick={() => setOpen(true)}>
          {t.deleteButton}
        </Button>
      </div>
      <DeleteAccountModal
        open={open}
        onClose={() => setOpen(false)}
        onConfirm={() => showToast(texts.app.comingSoon)}
      />
    </SettingsPanel>
  );
}
