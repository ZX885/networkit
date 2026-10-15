import { useState } from 'react';
import { saveProfile, unsaveProfile } from '../../api/saved.js';
import useMeta from '../../api/useMeta.js';
import { apiErrorText } from '../../lib/apiErrors.js';
import { texts } from '../../texts/en.js';
import useToast from '../ui/useToast.js';

// Закладка «сохранить профиль» (PUT/DELETE /api/saved/{username}/). Состояние меняется сразу, а при
// ошибке откатывается назад с тостом; пока запрос идёт, кнопка заблокирована (busy).
// При 409 saved_limit_reached тост называет лимит (meta.limits.saved_max), состояние остаётся прежним.
// onChange(next) вызывается сразу при нажатии, onRevert(previous) — если запрос не удался
// (список «Избранное» убирает карточку сразу и возвращает её при ошибке).
export default function useSavedToggle(username, initialSaved, { onChange, onRevert } = {}) {
  const [saved, setSaved] = useState(initialSaved);
  const [busy, setBusy] = useState(false);
  const showToast = useToast();
  const { meta } = useMeta();

  async function toggle() {
    if (busy) return;
    const next = !saved;
    setSaved(next);
    setBusy(true);
    onChange?.(next);
    try {
      await (next ? saveProfile(username) : unsaveProfile(username));
      showToast(next ? texts.card.savedToast : texts.card.unsavedToast, 'success');
    } catch (error) {
      setSaved(!next);
      onRevert?.(!next);
      const text =
        error.code === 'saved_limit_reached'
          ? texts.saved.limitReached(meta?.limits?.saved_max)
          : apiErrorText(error);
      showToast(text, 'error');
    } finally {
      setBusy(false);
    }
  }

  return { saved, busy, toggle };
}
