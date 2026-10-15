import { texts } from '../../../texts/en.js';
import styles from './MessageTabs.module.css';

const t = texts.messages;
const BOXES = ['chats', 'requests', 'sent'];

// Вкладки Chats / Requests / Sent. counts: { chats (непрочитанные), requests (входящие запросы) }.
export default function MessageTabs({ box, counts, onChange }) {
  return (
    <div className={styles.tabs} role="group" aria-label={t.tabsLabel}>
      {BOXES.map((name) => (
        <button
          key={name}
          type="button"
          className={[styles.tab, name === box && styles.active].filter(Boolean).join(' ')}
          aria-pressed={name === box}
          onClick={() => onChange(name)}
        >
          {t.tabs[name]}
          {counts[name] > 0 && (
            <span className={styles.badge}>
              {counts[name]}
              <span className="visually-hidden"> {t.newCount}</span>
            </span>
          )}
        </button>
      ))}
    </div>
  );
}
