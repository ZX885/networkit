import useMeta from '../../../api/useMeta.js';
import { SHOW_COUNTRY_FILTER } from '../../../constants/features.js';
import { texts } from '../../../texts/en.js';
import Button from '../../../components/ui/Button.jsx';
import Field from '../../../components/ui/Field.jsx';
import styles from './FilterPanel.module.css';

const t = texts.discover;

// Один выпадающий фильтр: пустое значение = «любой»
function FilterSelect({ id, label, any, options, value, onChange }) {
  return (
    <Field
      as="select"
      id={id}
      label={label}
      className={styles.field}
      value={value}
      onChange={(event) => onChange(event.target.value)}
    >
      <option value="">{any}</option>
      {options.map((option) => (
        <option key={option.code} value={option.code}>
          {option.label}
        </option>
      ))}
    </Field>
  );
}

// Панель фильтров (legacy .fp). На ≤600px скрыта, пока не нажата кнопка «Filters» (open).
export default function FilterPanel({ id, open, params, onChange, onClear }) {
  const { meta } = useMeta();
  const select = (key, label, any, options) => (
    <FilterSelect
      id={`filter-${key}`}
      label={label}
      any={any}
      options={options}
      value={params[key]}
      onChange={(value) => onChange({ [key]: value })}
    />
  );

  return (
    <div
      id={id}
      role="group"
      aria-label={t.filtersLabel}
      className={[styles.panel, open && styles.open].filter(Boolean).join(' ')}
    >
      {SHOW_COUNTRY_FILTER && select('country', t.country, t.allCountries, meta.countries)}
      {select('city', t.city, t.allCities, meta.cities)}
      {select('field', t.field, t.allFields, meta.fields)}
      {select('status', t.status, t.allStatuses, meta.statuses)}
      {select('goal', t.goal, t.anyGoal, meta.goals)}
      {select('language', t.language, t.anyLanguage, meta.languages)}
      <div className={styles.clear}>
        <Button variant="ghost" size="sm" onClick={onClear}>
          {t.clearAll}
        </Button>
      </div>
    </div>
  );
}
