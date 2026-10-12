import { Briefcase, Camera, Mail, MessageCircle, Send } from 'lucide-react';
import { texts } from '../../../texts/en.js';
import styles from './ContactButtons.module.css';

const t = texts.profile.contactLabels;
const stripAt = (value) => value.trim().replace(/^@/, '');

// Контакты → ссылки. Адрес всегда собираем сами из текста пользователя (с encodeURIComponent
// или префиксом https://), поэтому «javascript:» и подобное в ссылку попасть не может.
const CONTACTS = [
  { key: 'telegram', icon: Send, href: (v) => `https://t.me/${encodeURIComponent(stripAt(v))}` },
  {
    key: 'instagram',
    icon: Camera,
    href: (v) => `https://instagram.com/${encodeURIComponent(stripAt(v))}`,
  },
  {
    key: 'whatsapp',
    icon: MessageCircle,
    href: (v) => `https://wa.me/${v.replace(/\D/g, '')}`,
  },
  {
    key: 'linkedin',
    icon: Briefcase,
    href: (v) => `https://${v.trim().replace(/^https?:\/\//i, '')}`,
  },
  { key: 'public_email', icon: Mail, href: (v) => `mailto:${v.trim()}` },
];

// Кнопки контактов (legacy .slks/.slk): только заполненные. Нет контактов — ничего не рисуем.
export default function ContactButtons({ contacts }) {
  const items = CONTACTS.filter((item) => contacts?.[item.key]?.trim());
  if (items.length === 0) return null;

  return (
    <ul className={styles.list}>
      {items.map((item) => (
        <li key={item.key}>
          <a
            className={styles.link}
            href={item.href(contacts[item.key])}
            target="_blank"
            rel="noopener noreferrer"
          >
            <item.icon size={14} aria-hidden="true" />
            {t[item.key]}
          </a>
        </li>
      ))}
    </ul>
  );
}
