import Field from '../../../../../components/ui/Field.jsx';
import { BIO_MAX } from '../../../../../constants/rules.js';
import { texts } from '../../../../../texts/en.js';

const f = texts.register.fields;

// Шаг 6: короткое био (до 300 символов) со счётчиком.
export default function AboutStep({ form }) {
  const { data, errors, update } = form;

  return (
    <Field
      label={f.bio}
      as="textarea"
      rows={5}
      maxLength={BIO_MAX}
      placeholder={f.bioPlaceholder}
      value={data.bio}
      onChange={(e) => update('bio', e.target.value)}
      hint={`${data.bio.length}/${BIO_MAX}`}
      error={texts.validation[errors.bio]}
    />
  );
}
