import ChipSelect from '../../../../../components/ui/ChipSelect.jsx';
import FieldGroup from '../../../../../components/ui/FieldGroup.jsx';
import useMeta from '../../../../../api/useMeta.js';
import { texts } from '../../../../../texts/en.js';
import { errorText } from '../../../../../lib/apiErrors.js';

const f = texts.register.fields;

// Шаг 5: языки (максимум — из meta.limits).
export default function LanguagesStep({ form }) {
  const { data, errors, update, limits } = form;
  const { meta } = useMeta();

  return (
    <FieldGroup
      legend={f.languages}
      legendHidden
      hint={`${data.languages.length}/${limits.languages_max}`}
      error={errorText(errors.languages, limits)}
    >
      <ChipSelect
        options={meta.languages}
        value={data.languages}
        max={limits.languages_max}
        onChange={(next) => update('languages', next)}
      />
    </FieldGroup>
  );
}
