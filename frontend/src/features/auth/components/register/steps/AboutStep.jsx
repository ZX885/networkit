import Field from '../../../../../components/ui/Field.jsx';
import { texts } from '../../../../../texts/en.js';
import { errorText } from '../../../../../lib/apiErrors.js';

const f = texts.register.fields;

// Шаг 6: короткое био (максимум — из meta.limits) со счётчиком.
export default function AboutStep({ form }) {
  const { data, errors, update, limits } = form;

  return (
    <Field
      label={f.bio(limits.bio_max)}
      as="textarea"
      rows={5}
      maxLength={limits.bio_max}
      placeholder={f.bioPlaceholder}
      value={data.bio}
      onChange={(e) => update('bio', e.target.value)}
      hint={`${data.bio.length}/${limits.bio_max}`}
      error={errorText(errors.bio)}
    />
  );
}
