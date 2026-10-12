import { useState } from 'react';
import { Link } from 'react-router-dom';
import Avatar from '../../../components/ui/Avatar.jsx';
import Button from '../../../components/ui/Button.jsx';
import Field from '../../../components/ui/Field.jsx';
import useToast from '../../../components/ui/useToast.js';
import { COUNTRIES } from '../../../constants/countries.js';
import { FIELDS } from '../../../constants/fields.js';
import { GOALS } from '../../../constants/goals.js';
import { INTERESTS } from '../../../constants/interests.js';
import { LANGUAGES } from '../../../constants/languages.js';
import {
  ADULT_AGE,
  BIO_MAX,
  CITY_MAX,
  GOALS_MAX,
  INTERESTS_MAX,
  LANGUAGES_MAX,
  NAME_MAX,
  UNIVERSITY_MAX,
  YEAR_LEVEL_MAX,
} from '../../../constants/rules.js';
import { texts } from '../../../texts/en.js';
import ChipsSection from './ChipsSection.jsx';
import ContactsFields from './ContactsFields.jsx';
import styles from './EditProfileForm.module.css';
import ProfileSection from './ProfileSection.jsx';

const t = texts.editProfile;

const pick = (user) => ({
  first_name: user.first_name,
  last_name: user.last_name,
  field: user.field,
  university: user.university ?? '',
  country: user.country,
  city: user.city ?? '',
  year_level: user.year_level ?? '',
  bio: user.bio ?? '',
  contacts: { ...user.contacts },
  interests: user.interests ?? [],
  languages: user.languages ?? [],
  goals: user.goals ?? [],
});

// Форма редактирования профиля: заполняется данными пользователя, но пока ничего не отправляет
// (Save → «Coming soon»). Отправку PATCH /api/me/ подключим в шаге B4.
export default function EditProfileForm({ user }) {
  const [values, setValues] = useState(() => pick(user));
  const showToast = useToast();
  const isMinor = user.is_minor || user.age < ADULT_AGE;

  const set = (key, value) => setValues((prev) => ({ ...prev, [key]: value }));
  const text = (key) => ({
    value: values[key],
    onChange: (event) => set(key, event.target.value),
  });

  function handleSubmit(event) {
    event.preventDefault();
    showToast(t.saveSoon);
  }

  return (
    <form className={styles.form} onSubmit={handleSubmit}>
      <ProfileSection title={t.photo}>
        <div className={styles.photo}>
          <Avatar
            id={user.username}
            firstName={user.first_name}
            lastName={user.last_name}
            src={user.avatar_url}
            size="lg"
          />
          <Button variant="ghost" size="sm" disabled>
            {t.photoHint}
          </Button>
        </div>
      </ProfileSection>

      <ProfileSection title={t.basic}>
        <div className={styles.grid}>
          <Field label={t.firstName} maxLength={NAME_MAX} {...text('first_name')} />
          <Field label={t.lastName} maxLength={NAME_MAX} {...text('last_name')} />
        </div>
        <Field label={t.username} value={user.username} readOnly hint={t.usernameHint} />
        <Field as="select" label={t.field} {...text('field')}>
          {FIELDS.map((item) => (
            <option key={item.code} value={item.code}>
              {item.label}
            </option>
          ))}
        </Field>
        <Field
          label={t.university}
          optionalText={texts.common.optional}
          maxLength={UNIVERSITY_MAX}
          {...text('university')}
        />
        <div className={styles.grid}>
          <Field as="select" label={t.country} {...text('country')}>
            {COUNTRIES.map((item) => (
              <option key={item.code} value={item.code}>
                {item.label}
              </option>
            ))}
          </Field>
          <Field label={t.city} maxLength={CITY_MAX} {...text('city')} />
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
          optionalText={t.bioLimit(BIO_MAX)}
          maxLength={BIO_MAX}
          rows={4}
          hint={t.bioCount(values.bio.length, BIO_MAX)}
          {...text('bio')}
        />
      </ProfileSection>

      <ProfileSection title={t.contacts}>
        <ContactsFields
          values={values.contacts}
          disabled={isMinor}
          onChange={(key, value) => set('contacts', { ...values.contacts, [key]: value })}
        />
      </ProfileSection>

      <ChipsSection
        title={t.interests}
        options={INTERESTS}
        value={values.interests}
        max={INTERESTS_MAX}
        onChange={(next) => set('interests', next)}
      />
      <ChipsSection
        title={t.languages}
        options={LANGUAGES}
        value={values.languages}
        max={LANGUAGES_MAX}
        onChange={(next) => set('languages', next)}
      />
      <ChipsSection
        title={t.goals}
        options={GOALS}
        value={values.goals}
        max={GOALS_MAX}
        variant="pill"
        onChange={(next) => set('goals', next)}
      />

      <div className={styles.actions}>
        <Button type="submit">{t.save}</Button>
        <Link to="/me" className={styles.cancel}>
          {t.cancel}
        </Link>
      </div>
    </form>
  );
}
