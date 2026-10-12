import { ChevronLeft } from 'lucide-react';
import { texts } from '../../texts/en.js';
import ButtonLink from '../ui/ButtonLink.jsx';

// Кнопка «Back» (legacy: ghost sm с шевроном) — ссылка на указанную страницу
export default function BackLink({ to }) {
  return (
    <ButtonLink to={to} variant="ghost" size="sm">
      <ChevronLeft size={16} aria-hidden="true" />
      {texts.app.back}
    </ButtonLink>
  );
}
