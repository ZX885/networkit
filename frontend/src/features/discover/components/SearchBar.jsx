import { useEffect, useRef, useState } from 'react';
import { Search } from 'lucide-react';
import { texts } from '../../../texts/en.js';
import styles from './SearchBar.module.css';

const t = texts.discover;
const DEBOUNCE_MS = 320;

// Строка поиска (legacy .sbar). Значение уходит наверх через 320 мс после последнего символа.
// value — текущее значение из адреса: если оно изменилось снаружи («Назад»), поле подстраивается.
export default function SearchBar({ value, onSearch }) {
  const [draft, setDraft] = useState(value);
  const [seenValue, setSeenValue] = useState(value);
  const timer = useRef(null);
  const [emitted, setEmitted] = useState(value); // что мы сами отправили наверх последним

  if (value !== seenValue) {
    setSeenValue(value);
    if (value !== emitted) setDraft(value);
  }

  useEffect(() => () => clearTimeout(timer.current), []);

  function handleChange(event) {
    const next = event.target.value;
    setDraft(next);
    clearTimeout(timer.current);
    timer.current = setTimeout(() => {
      setEmitted(next.trim());
      onSearch(next.trim());
    }, DEBOUNCE_MS);
  }

  return (
    <div className={styles.bar}>
      <Search size={18} className={styles.icon} aria-hidden="true" />
      <input
        type="search"
        className={styles.input}
        value={draft}
        placeholder={t.searchPlaceholder}
        aria-label={t.searchLabel}
        autoComplete="off"
        onChange={handleChange}
      />
    </div>
  );
}
