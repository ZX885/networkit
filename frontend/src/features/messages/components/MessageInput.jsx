import { useRef, useState } from 'react';
import { Send } from 'lucide-react';
import Spinner from '../../../components/ui/Spinner.jsx';
import useToast from '../../../components/ui/useToast.js';
import { texts } from '../../../texts/en.js';
import styles from './MessageInput.module.css';

const t = texts.messages;
const MAX_HEIGHT = 100;

// Поле ввода: Enter отправляет, Shift+Enter — перенос. Пока идёт отправка, кнопка заблокирована.
// onSend(body) — промис; при ошибке текст остаётся в поле, показывается тост.
export default function MessageInput({ onSend }) {
  const [value, setValue] = useState('');
  const [sending, setSending] = useState(false);
  const areaRef = useRef(null);
  const showToast = useToast();
  const body = value.trim();

  function resize() {
    const area = areaRef.current;
    area.style.height = 'auto';
    area.style.height = `${Math.min(area.scrollHeight, MAX_HEIGHT)}px`;
  }

  async function submit() {
    if (!body || sending) return;
    setSending(true);
    try {
      await onSend(body);
      setValue('');
      requestAnimationFrame(resize);
    } catch {
      showToast(t.sendFailed, 'error');
    } finally {
      setSending(false);
      areaRef.current?.focus();
    }
  }

  function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      submit();
    }
  }

  return (
    <div className={styles.bar}>
      <textarea
        ref={areaRef}
        className={styles.input}
        rows={1}
        value={value}
        placeholder={t.inputPlaceholder}
        aria-label={t.inputLabel}
        onChange={(event) => {
          setValue(event.target.value);
          resize();
        }}
        onKeyDown={handleKeyDown}
      />
      <button
        type="button"
        className={styles.send}
        aria-label={t.send}
        disabled={!body || sending}
        aria-busy={sending || undefined}
        onClick={submit}
      >
        {sending ? <Spinner size="sm" /> : <Send size={17} aria-hidden="true" />}
      </button>
    </div>
  );
}
