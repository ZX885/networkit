import { Flag } from 'lucide-react';
import Button from '../../../components/ui/Button.jsx';
import useToast from '../../../components/ui/useToast.js';
import { texts } from '../../../texts/en.js';
import ProfileSection from './ProfileSection.jsx';
import styles from './ReportBlock.module.css';

const t = texts.profile;

// Блок «Report». Жалобы подключим позже (POST /api/reports/): пока кнопка честно говорит «Coming soon».
export default function ReportBlock() {
  const showToast = useToast();

  return (
    <ProfileSection icon={Flag} title={t.report}>
      <p className={styles.text}>{t.reportText}</p>
      <Button variant="ghost" size="sm" onClick={() => showToast(texts.app.comingSoon)}>
        {t.reportButton}
      </Button>
    </ProfileSection>
  );
}
