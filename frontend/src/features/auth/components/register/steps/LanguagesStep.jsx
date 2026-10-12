import ChipSelect from '../../../../../components/ui/ChipSelect.jsx';
import FieldGroup from '../../../../../components/ui/FieldGroup.jsx';
import { LANGUAGES } from '../../../../../constants/languages.js';
import { LANGUAGES_MAX } from '../../../../../constants/rules.js';
import { texts } from '../../../../../texts/en.js';
import { errorText } from '../../../../../lib/apiErrors.js';

const f = texts.register.fields;

// Шаг 5: языки (до 10).
export default function LanguagesStep({ form }) {
  const { data, errors, update } = form;

  return (
    <FieldGroup
      legend={f.languages}
      legendHidden
      hint={`${data.languages.length}/${LANGUAGES_MAX}`}
      error={errorText(errors.languages)}
    >
      <ChipSelect
        options={LANGUAGES}
        value={data.languages}
        max={LANGUAGES_MAX}
        onChange={(next) => update('languages', next)}
      />
    </FieldGroup>
  );
}
