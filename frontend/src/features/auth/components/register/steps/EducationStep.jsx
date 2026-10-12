import ChipSelect from '../../../../../components/ui/ChipSelect.jsx';
import Field from '../../../../../components/ui/Field.jsx';
import FieldGroup from '../../../../../components/ui/FieldGroup.jsx';
import { FIELDS } from '../../../../../constants/fields.js';
import { STATUSES } from '../../../../../constants/options.js';
import { texts } from '../../../../../texts/en.js';
import { errorText } from '../../../../../lib/apiErrors.js';

const f = texts.register.fields;

// Шаг 3: статус, школа, вуз, направление (список, в конце «Other»), курс/уровень.
export default function EducationStep({ form }) {
  const { data, errors, update } = form;
  const text = (name) => (e) => update(name, e.target.value);

  return (
    <>
      <FieldGroup legend={f.status} required error={errorText(errors.status)}>
        <ChipSelect
          variant="pill"
          multiple={false}
          options={STATUSES}
          value={data.status ? [data.status] : []}
          onChange={([value]) => update('status', value)}
        />
      </FieldGroup>
      <Field
        label={f.school}
        optionalText={texts.common.optional}
        value={data.school}
        onChange={text('school')}
        error={errorText(errors.school)}
      />
      <Field
        label={f.university}
        optionalText={texts.common.optional}
        placeholder={f.universityPlaceholder}
        value={data.university}
        onChange={text('university')}
        error={errorText(errors.university)}
      />
      <Field
        label={f.field}
        as="select"
        required
        value={data.field}
        onChange={text('field')}
        error={errorText(errors.field)}
      >
        <option value="">{f.fieldPlaceholder}</option>
        {FIELDS.map((field) => (
          <option key={field.code} value={field.code}>
            {field.label}
          </option>
        ))}
      </Field>
      <Field
        label={f.yearLevel}
        placeholder={f.yearLevelPlaceholder}
        value={data.yearLevel}
        onChange={text('yearLevel')}
        error={errorText(errors.yearLevel)}
      />
    </>
  );
}
