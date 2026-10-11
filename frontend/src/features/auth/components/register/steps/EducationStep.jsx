import ChipSelect from '../../../../../components/ui/ChipSelect.jsx';
import Field from '../../../../../components/ui/Field.jsx';
import FieldGroup from '../../../../../components/ui/FieldGroup.jsx';
import { FIELD_OTHER_CODE, FIELDS } from '../../../../../constants/fields.js';
import { STATUSES } from '../../../../../constants/options.js';
import { texts } from '../../../../../texts/en.js';

const f = texts.register.fields;
const v = texts.validation;

// Шаг 3: статус, школа, вуз, направление (список + «Other»), курс/уровень.
export default function EducationStep({ form }) {
  const { data, errors, update } = form;
  const text = (name) => (e) => update(name, e.target.value);

  return (
    <>
      <FieldGroup legend={f.status} required error={v[errors.status]}>
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
        error={v[errors.school]}
      />
      <Field
        label={f.university}
        optionalText={texts.common.optional}
        placeholder={f.universityPlaceholder}
        value={data.university}
        onChange={text('university')}
        error={v[errors.university]}
      />
      <Field
        label={f.field}
        as="select"
        required
        value={data.field}
        onChange={text('field')}
        error={v[errors.field]}
      >
        <option value="">{f.fieldPlaceholder}</option>
        {FIELDS.map((field) => (
          <option key={field.code} value={field.code}>
            {field.label}
          </option>
        ))}
      </Field>
      {data.field === FIELD_OTHER_CODE && (
        <Field
          label={f.fieldOther}
          required
          placeholder={f.fieldOtherPlaceholder}
          value={data.fieldOther}
          onChange={text('fieldOther')}
          error={v[errors.fieldOther]}
        />
      )}
      <Field
        label={f.yearLevel}
        placeholder={f.yearLevelPlaceholder}
        value={data.yearLevel}
        onChange={text('yearLevel')}
        error={v[errors.yearLevel]}
      />
    </>
  );
}
