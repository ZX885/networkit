import { useCallback, useState } from 'react';
import { register } from '../../../api/auth.js';
import { ADULT_AGE } from '../../../constants/rules.js';
import { apiErrorText, fieldErrorText } from '../../../lib/apiErrors.js';
import { buildRegisterPayload } from '../buildPayload.js';
import { mapServerErrors } from '../serverErrors.js';
import { findInvalidStep, getAgeFromData, validateStep } from '../validation.js';
import useUsernameCheck from './useUsernameCheck.js';

export const TOTAL_STEPS = 8;

const INITIAL_DATA = {
  firstName: '',
  lastName: '',
  username: '',
  email: '',
  password: '',
  birthDay: '',
  birthMonth: '',
  birthYear: '',
  gender: '',
  country: '',
  region: '',
  city: '',
  status: '',
  school: '',
  university: '',
  field: '',
  yearLevel: '',
  interests: [],
  languages: [],
  bio: '',
  goals: [],
  telegram: '',
  instagram: '',
  whatsapp: '',
  linkedin: '',
  publicEmail: '',
  acceptedTerms: false,
};

// Всё состояние мастера регистрации: текущий шаг, введённые данные (сохраняются при
// переходах назад), ошибки, отправка. Шаги только читают и меняют данные через update().
// Ошибки бывают клиентские (проверка шага) и серверные (ответ API): серверные остаются у поля,
// пока человек его не изменит.
export default function useRegisterForm() {
  const [step, setStep] = useState(1);
  const [data, setData] = useState(INITIAL_DATA);
  const [clientErrors, setClientErrors] = useState({});
  const [serverErrors, setServerErrors] = useState({});
  const [focusSignal, setFocusSignal] = useState(0); // растёт при ошибке → фокус на первое поле с ошибкой
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');
  const [registeredEmail, setRegisteredEmail] = useState('');

  const usernameStatus = useUsernameCheck(data.username);
  const isAdult = (getAgeFromData(data) ?? 0) >= ADULT_AGE;
  const errors = { ...serverErrors, ...clientErrors };

  // Меняет поле и убирает его ошибки (поля даты относятся к одной ошибке birthDate)
  const update = useCallback((field, value) => {
    setData((current) => ({ ...current, [field]: value }));
    const errorKey = field.startsWith('birth') ? 'birthDate' : field;
    const without = (current) => {
      if (!current[errorKey]) return current;
      const next = { ...current };
      delete next[errorKey];
      return next;
    };
    setClientErrors(without);
    setServerErrors(without);
  }, []);

  // Проверяет шаг; при ошибках показывает их и возвращает false
  function checkStep(stepNumber) {
    const found = validateStep(stepNumber, data, usernameStatus);
    setClientErrors(found);
    if (Object.keys(found).length === 0) return true;
    setFocusSignal((n) => n + 1);
    return false;
  }

  function goNext() {
    if (checkStep(step)) setStep((s) => Math.min(s + 1, TOTAL_STEPS));
  }

  function goBack() {
    setClientErrors({});
    setStep((s) => Math.max(s - 1, 1));
  }

  // Ответ сервера с ошибкой: полевые ошибки раскладываем по шагам и возвращаемся на самый ранний,
  // остальное (общие ошибки, лимит, сеть) показываем сообщением на последнем шаге
  function handleSubmitError(error) {
    if (error.code === 'validation_error') {
      const { fieldErrors, firstStep, unmapped } = mapServerErrors(error.fields);
      const general = [...error.nonFieldErrors, ...unmapped];
      setServerErrors(fieldErrors);
      setClientErrors({});
      setSubmitError(general.length > 0 ? fieldErrorText(general[0]) : '');
      if (firstStep > 0) {
        setStep(firstStep);
        setFocusSignal((n) => n + 1);
      }
      return;
    }
    setSubmitError(apiErrorText(error));
  }

  async function submit() {
    if (!checkStep(TOTAL_STEPS)) return;
    // Перед отправкой проверяем всё ещё раз (данные могли измениться на прошлых шагах)
    const invalidStep = findInvalidStep(data, usernameStatus);
    if (invalidStep) {
      setStep(invalidStep);
      setClientErrors(validateStep(invalidStep, data, usernameStatus));
      setFocusSignal((n) => n + 1);
      return;
    }
    setSubmitting(true);
    setSubmitError('');
    try {
      const result = await register(buildRegisterPayload(data));
      setRegisteredEmail(result.email);
    } catch (error) {
      handleSubmitError(error);
    } finally {
      setSubmitting(false);
    }
  }

  return {
    step,
    data,
    errors,
    focusSignal,
    submitting,
    submitError,
    registeredEmail,
    usernameStatus,
    isAdult,
    update,
    goNext,
    goBack,
    submit,
  };
}
