import { useEffect, useState } from 'react';
import { resendVerification } from '../../../api/auth.js';
import { apiErrorText } from '../../../lib/apiErrors.js';
import { texts } from '../../../texts/en.js';

const COOLDOWN_SECONDS = 60;

// Повторная отправка письма с подтверждением. После отправки — пауза 60 секунд.
// Сообщение об успехе нейтральное и не зависит от того, есть ли такой email.
// Возвращает { resend, loading, secondsLeft, message: { tone: 'success' | 'error' | null, text } }.
export default function useResendEmail(email) {
  const [secondsLeft, setSecondsLeft] = useState(0);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ tone: null, text: '' });

  useEffect(() => {
    if (secondsLeft <= 0) return undefined;
    const timer = setTimeout(() => setSecondsLeft((seconds) => seconds - 1), 1000);
    return () => clearTimeout(timer);
  }, [secondsLeft]);

  async function resend() {
    if (loading || secondsLeft > 0) return;
    setLoading(true);
    setMessage({ tone: null, text: '' });
    try {
      await resendVerification(email);
      setMessage({ tone: 'success', text: texts.resend.sent });
      setSecondsLeft(COOLDOWN_SECONDS);
    } catch (error) {
      // Лимит сервера: честно говорим об этом и ждём столько, сколько просит сервер
      setMessage({ tone: 'error', text: apiErrorText(error) });
      if (error.code === 'throttled' && error.retryAfter) setSecondsLeft(error.retryAfter);
    } finally {
      setLoading(false);
    }
  }

  return { resend, loading, secondsLeft, message };
}
