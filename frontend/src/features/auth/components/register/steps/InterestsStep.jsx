import ChipSelect from '../../../../../components/ui/ChipSelect.jsx';
import FieldGroup from '../../../../../components/ui/FieldGroup.jsx';
import useMeta from '../../../../../api/useMeta.js';
import { texts } from '../../../../../texts/en.js';
import { errorText } from '../../../../../lib/apiErrors.js';

const f = texts.register.fields;

// Шаг 4: интересы (максимум — из meta.limits).
export default function InterestsStep({ form }) {
  const { data, errors, update, limits } = form;
  const { meta } = useMeta();

  return (
    <FieldGroup
      legend={f.interests}
      legendHidden
      hint={`${data.interests.length}/${limits.interests_max}`}
      error={errorText(errors.interests, limits)}
    >
      <ChipSelect
        options={meta.interests}
        value={data.interests}
        max={limits.interests_max}
        onChange={(next) => update('interests', next)}
      />
    </FieldGroup>
  );
}
