import { useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import useMeta from '../../../api/useMeta.js';
import CityField from '../../../components/shared/CityField.jsx';
import Alert from '../../../components/ui/Alert.jsx';
import Button from '../../../components/ui/Button.jsx';
import Field from '../../../components/ui/Field.jsx';
import { GOAL_ICONS } from '../../../constants/goalIcons.js';
import { NAME_MAX, UNIVERSITY_MAX, YEAR_LEVEL_MAX } from '../../../constants/rules.js';
import { texts } from '../../../texts/en.js';
import useEditProfile from '../hooks/useEditProfile.js';
import ChipsSection from './ChipsSection.jsx';
import ContactsFields from './ContactsFields.jsx';
import styles from './EditProfileForm.module.css';
import ProfileSection from './ProfileSection.jsx';

const t = texts.editProfile;

// Форма редактирования профиля: заполняется данными пользователя, Save отправляет PATCH /api/me/
// (только изменённые поля). Списки и лимиты — с сервера (meta), ошибки показываются у полей.
export default function EditProfileForm({ user }) {
  const { meta } = useMeta();
  const { limits } = meta;
  const form = useEditProfile(user, limits);
  const { values, errors, saving } = form;
  const formRef = useRef(null);

  // При ошибке сохранения фокус уходит на первое поле с ошибкой
  useEffect(() => {
    if (form.focusSignal) formRef.current?.querySelector('[aria-invalid="true"]')?.focus();
  }, [form.focusSignal]);

  const text = (key) => ({
    value: values[key],
    onChange: (event) => form.set(key, event.target.value),
    error: errors[key],
  });
  const options = (list) =>
    list.map((item) => (
      <option key={item.code} value={item.code}>
        {item.label}
      </option>
    ));
  const goals = meta.goals.map((goal) => ({ ...goal, icon: GOAL_ICONS[goal.code] }));

  function handleSubmit(event) {
    event.preventDefault();
    form.submit();
  }

  return (
    <form ref={formRef} className={styles.form} noValidate onSubmit={handleSubmit}>
      {form.generalError && <Alert>{form.generalError}</Alert>}
      <ProfileSection title={t.basic}>
        <div className={styles.grid}>
          <Field label={t.firstName} maxLength={NAME_MAX} {...text('first_name')} />
          <Field label={t.lastName} maxLength={NAME_MAX} {...text('last_name')} />
        </div>
        <Field label={t.username} value={user.username} readOnly hint={t.usernameHint} />
        <Field as="select" label={t.field} {...text('field')}>
          {options(meta.fields)}
        </Field>
        <Field
          label={t.university}
          optionalText={texts.common.optional}
          maxLength={UNIVERSITY_MAX}
          {...text('university')}
        />
        <div className={styles.grid}>
          <Field as="select" label={t.country} {...text('country')}>
            {options(meta.countries)}
          </Field>
          <CityField
            label={t.city}
            country={values.country}
            city={values.city}
            cityOther={values.cityOther}
            error={errors.city}
            onChange={(city, cityOther) => {
              form.set('city', city);
              form.set('cityOther', cityOther);
            }}
          />
        </div>
        <Field
          label={t.yearLevel}
          optionalText={texts.common.optional}
          placeholder={t.yearLevelPlaceholder}
          maxLength={YEAR_LEVEL_MAX}
          {...text('year_level')}
        />
        <Field
          as="textarea"
          label={t.bio}
          optionalText={t.bioLimit(limits.bio_max)}
          maxLength={limits.bio_max}
          rows={4}
          hint={t.bioCount(values.bio.length, limits.bio_max)}
          {...text('bio')}
        />
      </ProfileSection>

      <ProfileSection title={t.contacts}>
        <ContactsFields
          values={values.contacts}
          errors={errors}
          disabled={form.isMinor}
          onChange={form.setContact}
        />
      </ProfileSection>

      <ChipsSection
        title={t.interests}
        options={meta.interests}
        value={values.interests}
        max={limits.interests_max}
        error={errors.interests}
        onChange={(next) => form.set('interests', next)}
      />
      <ChipsSection
        title={t.languages}
        options={meta.languages}
        value={values.languages}
        max={limits.languages_max}
        error={errors.languages}
        onChange={(next) => form.set('languages', next)}
      />
      <ChipsSection
        title={t.goals}
        options={goals}
        value={values.goals}
        max={limits.goals_max}
        variant="pill"
        error={errors.goals}
        onChange={(next) => form.set('goals', next)}
      />

      <div className={styles.actions}>
        <Button type="submit" loading={saving}>
          {t.save}
        </Button>
        <Link to="/me" className={styles.cancel}>
          {t.cancel}
        </Link>
      </div>
    </form>
  );
}
