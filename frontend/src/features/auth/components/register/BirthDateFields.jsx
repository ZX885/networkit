import Field from '../../../../components/ui/Field.jsx';
import FieldGroup from '../../../../components/ui/FieldGroup.jsx';
import { texts } from '../../../../texts/en.js';
import styles from './BirthDateFields.module.css';

const f = texts.register.fields;

// Дата рождения тремя полями День / Месяц / Год (как в legacy).
// Ошибка одна на всю дату: подсвечиваются все три поля, текст — под ними.
export default function BirthDateFields({ data, update, error }) {
  const common = { type: 'text', inputMode: 'numeric', labelHidden: true, invalid: Boolean(error) };

  return (
    <FieldGroup legend={f.birthDate} required hint={f.birthHint} error={error}>
      <div className={styles.grid}>
        <Field
          {...common}
          label={f.day}
          placeholder={f.day}
          maxLength={2}
          autoComplete="bday-day"
          value={data.birthDay}
          onChange={(e) => update('birthDay', e.target.value.replace(/\D/g, ''))}
        />
        <Field
          {...common}
          label={f.month}
          placeholder={f.month}
          maxLength={2}
          autoComplete="bday-month"
          value={data.birthMonth}
          onChange={(e) => update('birthMonth', e.target.value.replace(/\D/g, ''))}
        />
        <Field
          {...common}
          label={f.year}
          placeholder={f.year}
          maxLength={4}
          autoComplete="bday-year"
          value={data.birthYear}
          onChange={(e) => update('birthYear', e.target.value.replace(/\D/g, ''))}
        />
      </div>
    </FieldGroup>
  );
}
