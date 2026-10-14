import Field from '../../../../../components/ui/Field.jsx';
import useMeta from '../../../../../api/useMeta.js';
import { texts } from '../../../../../texts/en.js';
import { errorText } from '../../../../../lib/apiErrors.js';

const f = texts.register.fields;

// Шаг 2: страна, регион, город.
export default function LocationStep({ form }) {
  const { data, errors, update } = form;
  const { meta } = useMeta();
  const text = (name) => (e) => update(name, e.target.value);

  return (
    <>
      <Field
        label={f.country}
        as="select"
        required
        value={data.country}
        onChange={text('country')}
        error={errorText(errors.country)}
      >
        <option value="">{f.countryPlaceholder}</option>
        {meta.countries.map((country) => (
          <option key={country.code} value={country.code}>
            {country.label}
          </option>
        ))}
      </Field>
      <Field
        label={f.region}
        placeholder={f.regionPlaceholder}
        autoComplete="address-level1"
        value={data.region}
        onChange={text('region')}
        error={errorText(errors.region)}
      />
      <Field
        label={f.city}
        required
        placeholder={f.cityPlaceholder}
        autoComplete="address-level2"
        value={data.city}
        onChange={text('city')}
        error={errorText(errors.city)}
      />
    </>
  );
}
