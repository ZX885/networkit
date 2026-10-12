import { COUNTRIES } from '../../../constants/countries.js';
import { STATUSES } from '../../../constants/options.js';
import { formatMonthYear, labelOf } from '../../../lib/labels.js';
import { texts } from '../../../texts/en.js';
import styles from './DetailsList.module.css';

const t = texts.profile.labels;

// Таблица «Details» (legacy .dt): Status, Year, Region, Country, Joined — только то, что заполнено
export default function DetailsList({ profile }) {
  const joined = formatMonthYear(profile.joined ?? profile.created_at);
  const rows = [
    [t.status, profile.status && labelOf(STATUSES, profile.status)],
    [t.year, profile.year_level],
    [t.region, profile.region],
    [t.country, profile.country && labelOf(COUNTRIES, profile.country)],
    [t.joined, joined],
  ].filter(([, value]) => value);

  return (
    <dl className={styles.list}>
      {rows.map(([label, value]) => (
        <div key={label} className={styles.row}>
          <dt className={styles.label}>{label}</dt>
          <dd className={`${styles.value} user-text`}>{value}</dd>
        </div>
      ))}
    </dl>
  );
}
