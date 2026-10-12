import { useState } from 'react';
import { setSaved } from '../../api/mock/people.js';
import { texts } from '../../texts/en.js';
import useToast from '../ui/useToast.js';

// Закладка «сохранить профиль» (MOCK: api/mock/people.js → PUT/DELETE /api/saved/{username}/).
// Возвращает { saved, busy, toggle }; onChange(saved) сообщает родителю (например, список Saved).
export default function useSavedToggle(username, initialSaved, onChange) {
  const [saved, setSavedState] = useState(initialSaved);
  const [busy, setBusy] = useState(false);
  const showToast = useToast();

  async function toggle() {
    const next = !saved;
    setBusy(true);
    try {
      await setSaved(username, next);
      setSavedState(next);
      showToast(next ? texts.card.savedToast : texts.card.unsavedToast, 'success');
      onChange?.(next);
    } catch {
      showToast(texts.app.errorTitle, 'error');
    } finally {
      setBusy(false);
    }
  }

  return { saved, busy, toggle };
}
