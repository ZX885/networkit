import { Link } from 'react-router-dom';
import Alert from '../../../../../components/ui/Alert.jsx';
import Checkbox from '../../../../../components/ui/Checkbox.jsx';
import Field from '../../../../../components/ui/Field.jsx';
import { texts } from '../../../../../texts/en.js';
import styles from './Steps.module.css';
import { errorText } from '../../../../../lib/apiErrors.js';

const f = texts.register.fields;
const terms = texts.register.terms;

// Шаг 8: контакты (только с 18 лет, все необязательные) и согласие с условиями.
// Младше 18 — вместо полей показываем пояснение; шаг принимается без данных.
export default function ContactStep({ form }) {
  const { data, errors, update, isAdult } = form;
  const text = (name) => (e) => update(name, e.target.value);

  return (
    <>
      {/* Ошибка сервера «контакты запрещены» (не должна возникать, если возраст посчитан одинаково) */}
      {errors.contacts && <Alert>{errorText(errors.contacts)}</Alert>}
      {isAdult ? (
        <>
          <div className={styles.row}>
            <Field
              label={f.telegram}
              placeholder={f.telegramPlaceholder}
              value={data.telegram}
              onChange={text('telegram')}
              error={errorText(errors.telegram)}
            />
            <Field
              label={f.instagram}
              placeholder={f.instagramPlaceholder}
              value={data.instagram}
              onChange={text('instagram')}
              error={errorText(errors.instagram)}
            />
          </div>
          <div className={styles.row}>
            <Field
              label={f.whatsapp}
              type="tel"
              placeholder={f.whatsappPlaceholder}
              value={data.whatsapp}
              onChange={text('whatsapp')}
              error={errorText(errors.whatsapp)}
            />
            <Field
              label={f.linkedin}
              placeholder={f.linkedinPlaceholder}
              value={data.linkedin}
              onChange={text('linkedin')}
              error={errorText(errors.linkedin)}
            />
          </div>
          <Field
            label={f.publicEmail}
            type="email"
            placeholder={f.publicEmailPlaceholder}
            value={data.publicEmail}
            onChange={text('publicEmail')}
            error={errorText(errors.publicEmail)}
          />
        </>
      ) : (
        <p className={styles.info}>{texts.register.contactsMinor}</p>
      )}
      <div className={styles.divider} />
      <Checkbox
        checked={data.acceptedTerms}
        onChange={(checked) => update('acceptedTerms', checked)}
        error={errorText(errors.acceptedTerms)}
      >
        {terms.before}
        <Link to="/terms" target="_blank" rel="noopener">
          {terms.terms}
        </Link>
        {terms.and}
        <Link to="/privacy" target="_blank" rel="noopener">
          {terms.privacy}
        </Link>{' '}
        <span className="visually-hidden">{terms.newTab}</span>
      </Checkbox>
    </>
  );
}
