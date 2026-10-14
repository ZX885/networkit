import ChipSelect from '../../../../../components/ui/ChipSelect.jsx';
import Field from '../../../../../components/ui/Field.jsx';
import FieldGroup from '../../../../../components/ui/FieldGroup.jsx';
import useMeta from '../../../../../api/useMeta.js';
import { texts } from '../../../../../texts/en.js';
import BirthDateFields from '../BirthDateFields.jsx';
import styles from './Steps.module.css';
import { errorText } from '../../../../../lib/apiErrors.js';

const f = texts.register.fields;

// Шаг 1: имя, username (с проверкой занятости), email, пароль, дата рождения, пол.
export default function BasicInfoStep({ form }) {
  const { data, errors, update, usernameStatus, limits } = form;
  const { meta } = useMeta(); // справочники сервера (шаг показывается после их загрузки)
  const text = (name) => (e) => update(name, e.target.value);

  // Подсказка под username меняется по ходу проверки; «занято» показываем сразу, не ждём Continue
  const usernameHints = {
    checking: f.usernameChecking,
    available: f.usernameAvailable,
    unknown: f.usernameUnknown,
  };
  const liveErrors = { taken: 'usernameTaken', reserved: 'usernameReserved' };
  const usernameError = errorText(errors.username) || errorText(liveErrors[usernameStatus]);

  return (
    <>
      <div className={styles.row}>
        <Field
          label={f.firstName}
          required
          placeholder={f.firstNamePlaceholder}
          autoComplete="given-name"
          value={data.firstName}
          onChange={text('firstName')}
          error={errorText(errors.firstName)}
        />
        <Field
          label={f.lastName}
          required
          placeholder={f.lastNamePlaceholder}
          autoComplete="family-name"
          value={data.lastName}
          onChange={text('lastName')}
          error={errorText(errors.lastName)}
        />
      </div>
      <Field
        label={f.username}
        required
        placeholder={f.usernamePlaceholder}
        autoComplete="username"
        autoCapitalize="none"
        spellCheck={false}
        value={data.username}
        onChange={(e) => update('username', e.target.value.toLowerCase())}
        hint={usernameHints[usernameStatus] ?? f.usernameHint}
        error={usernameError}
      />
      <Field
        label={f.email}
        required
        type="email"
        placeholder={f.emailPlaceholder}
        autoComplete="email"
        value={data.email}
        onChange={text('email')}
        error={errorText(errors.email)}
      />
      <Field
        label={f.password}
        required
        type="password"
        placeholder={f.passwordPlaceholder}
        autoComplete="new-password"
        value={data.password}
        onChange={text('password')}
        error={errorText(errors.password)}
      />
      <BirthDateFields data={data} update={update} error={errorText(errors.birthDate, limits)} />
      <FieldGroup legend={f.gender} optionalText={texts.common.optional}>
        <ChipSelect
          variant="pill"
          multiple={false}
          options={meta.genders}
          value={data.gender ? [data.gender] : []}
          onChange={([value]) => update('gender', value)}
        />
      </FieldGroup>
    </>
  );
}
