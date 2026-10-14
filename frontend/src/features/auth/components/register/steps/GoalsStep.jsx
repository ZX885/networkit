import ChipSelect from '../../../../../components/ui/ChipSelect.jsx';
import FieldGroup from '../../../../../components/ui/FieldGroup.jsx';
import useMeta from '../../../../../api/useMeta.js';
import { GOAL_ICONS } from '../../../../../constants/goalIcons.js';
import { texts } from '../../../../../texts/en.js';
import { errorText } from '../../../../../lib/apiErrors.js';

const f = texts.register.fields;

// Шаг 7: цели (максимум — из meta.limits), список с иконками как в legacy.
export default function GoalsStep({ form }) {
  const { data, errors, update, limits } = form;
  const { meta } = useMeta();
  // Список целей приходит с сервера, иконки добавляем по коду
  const options = meta.goals.map((goal) => ({ ...goal, icon: GOAL_ICONS[goal.code] }));

  return (
    <FieldGroup
      legend={f.goals}
      legendHidden
      hint={`${data.goals.length}/${limits.goals_max}`}
      error={errorText(errors.goals, limits)}
    >
      <ChipSelect
        variant="list"
        options={options}
        value={data.goals}
        max={limits.goals_max}
        onChange={(next) => update('goals', next)}
      />
    </FieldGroup>
  );
}
