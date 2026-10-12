import Field from '../../../components/ui/Field.jsx';
import { EMAIL_MAX } from '../../../constants/rules.js';
import { texts } from '../../../texts/en.js';
import styles from './EditProfileForm.module.css';

const t = texts.editProfile;
const LABELS = texts.profile.contactLabels;
const KEYS = ['telegram', 'instagram', 'whatsapp', 'linkedin', 'public_email'];

// Контакты в форме редактирования. Для младше 18 лет поля отключены с пояснением (правило сервера).
export default function ContactsFields({ values, onChange, disabled }) {
  return (
    <>
      {disabled && <p className={styles.note}>{t.contactsMinor}</p>}
      <div className={styles.grid}>
        {KEYS.map((key) => (
          <Field
            key={key}
            label={LABELS[key]}
            type={key === 'public_email' ? 'email' : 'text'}
            placeholder={t.contactPlaceholders[key]}
            maxLength={key === 'public_email' ? EMAIL_MAX : 100}
            disabled={disabled}
            value={values[key] ?? ''}
            onChange={(event) => onChange(key, event.target.value)}
          />
        ))}
      </div>
    </>
  );
}
