import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, ChevronRight, PartyPopper } from 'lucide-react';
import Alert from '../../../../components/ui/Alert.jsx';
import Button from '../../../../components/ui/Button.jsx';
import { texts } from '../../../../texts/en.js';
import { TOTAL_STEPS } from '../../hooks/useRegisterForm.js';
import RegisterProgress from './RegisterProgress.jsx';
import { STEPS } from './steps/index.js';
import styles from './RegisterWizard.module.css';

const t = texts.register;

// Мастер регистрации: прогресс, карточка текущего шага, кнопки Back/Continue.
// form — результат useRegisterForm. Фокус: при смене шага уходит на заголовок,
// при ошибке — на первое поле с ошибкой.
export default function RegisterWizard({ form }) {
  const { step, errors, focusSignal, submitting, submitError } = form;
  const navigate = useNavigate();
  const formRef = useRef(null);
  const headingRef = useRef(null);
  const isFirstRender = useRef(true);
  const StepComponent = STEPS[step - 1];
  const isLast = step === TOTAL_STEPS;
  const content = t.steps[step - 1];
  const subtitle =
    typeof content.subtitle === 'function' ? content.subtitle(form.limits) : content.subtitle;

  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }
    headingRef.current?.focus();
  }, [step]);

  useEffect(() => {
    if (focusSignal) formRef.current?.querySelector('[aria-invalid="true"]')?.focus();
  }, [focusSignal]);

  function handleSubmit(event) {
    event.preventDefault();
    if (isLast) form.submit();
    else form.goNext();
  }

  return (
    <>
      <RegisterProgress step={step} total={TOTAL_STEPS} />
      <div className={styles.card}>
        <form key={step} ref={formRef} className={styles.step} noValidate onSubmit={handleSubmit}>
          <h2 ref={headingRef} className={styles.title} tabIndex={-1}>
            {content.title}
          </h2>
          <p className={styles.subtitle}>{subtitle}</p>
          {isLast && submitError && <Alert>{submitError}</Alert>}
          <StepComponent form={form} errors={errors} />
          <div className={styles.nav}>
            {step > 1 ? (
              <Button variant="ghost" size="sm" onClick={form.goBack} disabled={submitting}>
                <ChevronLeft size={16} aria-hidden="true" /> {t.back}
              </Button>
            ) : (
              <Button variant="ghost" size="sm" onClick={() => navigate('/')}>
                <ChevronLeft size={16} aria-hidden="true" /> {t.home}
              </Button>
            )}
            <Button type="submit" loading={submitting}>
              {isLast ? (
                <>
                  <PartyPopper size={16} aria-hidden="true" /> {t.submit}
                </>
              ) : (
                <>
                  {t.next} <ChevronRight size={16} aria-hidden="true" />
                </>
              )}
            </Button>
          </div>
        </form>
      </div>
    </>
  );
}
