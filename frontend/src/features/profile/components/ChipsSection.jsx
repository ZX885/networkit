import ChipSelect from '../../../components/ui/ChipSelect.jsx';
import FieldGroup from '../../../components/ui/FieldGroup.jsx';
import ProfileSection from './ProfileSection.jsx';

// Блок формы с чипами (интересы, языки, цели): заголовок блока + доступная группа кнопок
export default function ChipsSection({ title, options, value, max, variant, onChange }) {
  return (
    <ProfileSection title={title}>
      <FieldGroup legend={title} legendHidden>
        <ChipSelect
          options={options}
          value={value}
          max={max}
          variant={variant}
          label={title}
          onChange={onChange}
        />
      </FieldGroup>
    </ProfileSection>
  );
}
