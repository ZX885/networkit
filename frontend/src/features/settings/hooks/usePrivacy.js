import { useEffect, useState } from 'react';
import { getPrivacy, updatePrivacy } from '../../../api/me.js';
import useAuth from '../../../app/providers/useAuth.js';
import useToast from '../../../components/ui/useToast.js';
import { apiErrorText, fieldErrorText } from '../../../lib/apiErrors.js';
import { texts } from '../../../texts/en.js';

// Настройки приватности через API: GET при открытии, PATCH сразу при переключении.
// Значение меняется на экране сразу, а при ошибке откатывается назад и показывается тост.
// Пока флаг сохраняется, его переключатель заблокирован (pending): быстрые клики не гоняются друг с другом.
export default function usePrivacy() {
  const { user, updateUser } = useAuth();
  const showToast = useToast();
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState({ attempt: null, values: null, error: null });
  const [pending, setPending] = useState([]);

  useEffect(() => {
    let ignore = false;
    getPrivacy().then(
      (values) => !ignore && setState({ attempt, values, error: null }),
      (error) => !ignore && setState({ attempt, values: null, error }),
    );
    return () => {
      ignore = true;
    };
  }, [attempt]);

  const loading = state.attempt !== attempt;

  async function toggle(key, next) {
    const previous = state.values[key];
    setState((current) => ({ ...current, values: { ...current.values, [key]: next } }));
    setPending((keys) => [...keys, key]);
    try {
      const saved = await updatePrivacy({ [key]: next });
      setState((current) => ({ ...current, values: saved }));
      updateUser({ ...user, privacy: saved }); // другие страницы видят актуальные флаги
      showToast(texts.app.saved, 'success');
    } catch (error) {
      setState((current) => ({ ...current, values: { ...current.values, [key]: previous } }));
      const item = error.fields?.[key]?.[0]; // например, not_allowed_for_minors
      showToast(item ? fieldErrorText(item) : apiErrorText(error), 'error');
    } finally {
      setPending((keys) => keys.filter((k) => k !== key));
    }
  }

  return {
    loading,
    error: loading ? null : state.error,
    values: loading ? null : state.values,
    pending,
    toggle,
    retry: () => setAttempt((n) => n + 1),
  };
}
