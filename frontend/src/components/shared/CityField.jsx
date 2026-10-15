import useMeta from '../../api/useMeta.js';
import { CITY_MAX } from '../../constants/rules.js';
import { texts } from '../../texts/en.js';
import Field from '../ui/Field.jsx';

const t = texts.location;
const OTHER = '__other__';

const sameName = (a, b) => a.trim().toLowerCase() === b.trim().toLowerCase();

// Поле «город». Если страна — та, для которой сервер даёт список городов (meta.country_cities_default,
// сейчас Узбекистан), город выбирается из списка (meta.cities) с вариантом «Other» и текстовым полем;
// для остальных стран — текстовое поле. В профиль всегда уходит НАЗВАНИЕ города (текст).
// cityOther — человек выбрал «Other» (остаётся true, пока он не выберет город из списка).
// onChange(city, cityOther) — новые значения; label и placeholder текстового поля передаёт форма.
export default function CityField({
  country,
  city,
  cityOther,
  onChange,
  label,
  placeholder,
  error,
  required = false,
}) {
  const { meta } = useMeta();
  const useList = country === meta.country_cities_default;
  const match = meta.cities.find((item) => sameName(item.label, city));
  // Свой город (не из списка) показываем текстом, даже если человек «Other» не нажимал (старые данные)
  const other = cityOther || (city.trim() !== '' && !match);

  const textField = (
    <Field
      label={label}
      required={required}
      placeholder={placeholder}
      maxLength={CITY_MAX}
      autoComplete="address-level2"
      value={city}
      onChange={(event) => onChange(event.target.value, useList)}
      error={error}
    />
  );
  if (!useList) return textField;

  const selected = other ? OTHER : (match?.code ?? '');

  function handleSelect(event) {
    const value = event.target.value;
    if (value === OTHER) onChange('', true);
    else onChange(meta.cities.find((item) => item.code === value)?.label ?? '', false);
  }

  return (
    <>
      <Field
        as="select"
        label={label}
        required={required}
        value={selected}
        onChange={handleSelect}
        error={other ? undefined : error}
      >
        <option value="">{t.select}</option>
        {meta.cities.map((item) => (
          <option key={item.code} value={item.code}>
            {item.label}
          </option>
        ))}
        <option value={OTHER}>{t.other}</option>
      </Field>
      {other && (
        <Field
          label={t.otherLabel}
          required={required}
          placeholder={t.otherPlaceholder}
          maxLength={CITY_MAX}
          autoComplete="address-level2"
          value={city}
          onChange={(event) => onChange(event.target.value, true)}
          error={error}
        />
      )}
    </>
  );
}
