import { useEffect, useRef } from 'react';

// Периодический опрос (realtime нет). Правила:
// - таймер работает только пока вкладка видна (Page Visibility); при возврате на вкладку опрос идёт сразу;
// - таймер снимается при размонтировании и при enabled=false (выход, смена диалога);
// - ошибка 401 останавливает опрос совсем (сессия закончилась);
// - callback берётся из ref, поэтому смена callback НЕ пересоздаёт таймер: интервалы не накапливаются.
// callback может быть async; его ошибки (кроме 401) игнорируются, следующий опрос попробует снова.
export default function usePolling(callback, intervalMs, enabled = true) {
  const callbackRef = useRef(callback);
  useEffect(() => {
    callbackRef.current = callback;
  });

  useEffect(() => {
    if (!enabled) return undefined;
    let timer = null;
    let halted = false; // после 401 больше не опрашиваем
    let running = false; // не запускаем новый опрос, пока не закончился предыдущий

    async function tick() {
      if (halted || running) return;
      running = true;
      try {
        await callbackRef.current();
      } catch (error) {
        if (error?.status === 401) stopTimer(true);
      } finally {
        running = false;
      }
    }

    function startTimer() {
      if (timer === null && !halted && !document.hidden) timer = setInterval(tick, intervalMs);
    }

    function stopTimer(forever = false) {
      if (forever) halted = true;
      if (timer !== null) clearInterval(timer);
      timer = null;
    }

    function handleVisibility() {
      if (document.hidden) {
        stopTimer();
      } else if (!halted) {
        tick(); // вкладка снова видна: обновляемся сразу
        startTimer();
      }
    }

    startTimer();
    document.addEventListener('visibilitychange', handleVisibility);
    return () => {
      stopTimer(true);
      document.removeEventListener('visibilitychange', handleVisibility);
    };
  }, [intervalMs, enabled]);
}
