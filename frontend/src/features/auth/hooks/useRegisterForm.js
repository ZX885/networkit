import { useCallback, useState } from 'react';
import { register } from '../../../api/mock/auth.js';
import { ADULT_AGE } from '../../../constants/rules.js';
import { texts } from '../../../texts/en.js';
import { buildRegisterPayload } from '../buildPayload.js';
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
  fieldOther: '',
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
export default function useRegisterForm() {
  const [step, setStep] = useState(1);
  const [data, setData] = useState(INITIAL_DATA);
  const [errors, setErrors] = useState({});
  const [focusSignal, setFocusSignal] = useState(0); // растёт при неудачной проверке → фокус на первое поле с ошибкой
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');
  const [registeredEmail, setRegisteredEmail] = useState('');

  const usernameStatus = useUsernameCheck(data.username);
  const isAdult = (getAgeFromData(data) ?? 0) >= ADULT_AGE;

  // Меняет поле и убирает его ошибку (поля даты относятся к одной ошибке birthDate)
  const update = useCallback((field, value) => {
    setData((current) => ({ ...current, [field]: value }));
    const errorKey = field.startsWith('birth') ? 'birthDate' : field;
    setErrors((current) => {
      if (!current[errorKey]) return current;
      const next = { ...current };
      delete next[errorKey];
      return next;
    });
  }, []);

  // Проверяет шаг; при ошибках показывает их и возвращает false
  function checkStep(stepNumber) {
    const found = validateStep(stepNumber, data, usernameStatus);
    setErrors(found);
    if (Object.keys(found).length === 0) return true;
    setFocusSignal((n) => n + 1);
    return false;
  }

  function goNext() {
    if (checkStep(step)) setStep((s) => Math.min(s + 1, TOTAL_STEPS));
  }

  function goBack() {
    setErrors({});
    setStep((s) => Math.max(s - 1, 1));
  }

  async function submit() {
    if (!checkStep(TOTAL_STEPS)) return;
    // Перед отправкой проверяем всё ещё раз (данные могли измениться на прошлых шагах)
    const invalidStep = findInvalidStep(data, usernameStatus);
    if (invalidStep) {
      setStep(invalidStep);
      setErrors(validateStep(invalidStep, data, usernameStatus));
      return;
    }
    setSubmitting(true);
    setSubmitError('');
    try {
      const result = await register(buildRegisterPayload(data));
      setRegisteredEmail(result.email);
    } catch {
      setSubmitError(texts.register.submitFailed);
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
