import ChipSelect from '../../../../../components/ui/ChipSelect.jsx';
import FieldGroup from '../../../../../components/ui/FieldGroup.jsx';
import { INTERESTS } from '../../../../../constants/interests.js';
import { INTERESTS_MAX } from '../../../../../constants/rules.js';
import { texts } from '../../../../../texts/en.js';
import { errorText } from '../../../../../lib/apiErrors.js';

const f = texts.register.fields;

// Шаг 4: интересы (до 10 штук).
export default function InterestsStep({ form }) {
  const { data, errors, update } = form;

  return (
    <FieldGroup
      legend={f.interests}
      legendHidden
      hint={`${data.interests.length}/${INTERESTS_MAX}`}
      error={errorText(errors.interests)}
    >
      <ChipSelect
        options={INTERESTS}
        value={data.interests}
        max={INTERESTS_MAX}
        onChange={(next) => update('interests', next)}
      />
    </FieldGroup>
  );
}
