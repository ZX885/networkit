import ChipSelect from '../../../../../components/ui/ChipSelect.jsx';
import FieldGroup from '../../../../../components/ui/FieldGroup.jsx';
import { GOALS } from '../../../../../constants/goals.js';
import { GOALS_MAX } from '../../../../../constants/rules.js';
import { texts } from '../../../../../texts/en.js';
import { errorText } from '../../../../../lib/apiErrors.js';

const f = texts.register.fields;

// Шаг 7: цели (до 8), список с иконками как в legacy.
export default function GoalsStep({ form }) {
  const { data, errors, update } = form;

  return (
    <FieldGroup
      legend={f.goals}
      legendHidden
      hint={`${data.goals.length}/${GOALS_MAX}`}
      error={errorText(errors.goals)}
    >
      <ChipSelect
        variant="list"
        options={GOALS}
        value={data.goals}
        max={GOALS_MAX}
        onChange={(next) => update('goals', next)}
      />
    </FieldGroup>
  );
}
