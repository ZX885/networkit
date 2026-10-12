// Форматы времени для сообщений (английские, как в legacy: toLocaleTimeString('en-US'))
export const formatTime = (iso) =>
  new Date(iso).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

// «Monday, Oct 12» — разделитель дней в чате
export const formatDay = (iso) =>
  new Date(iso).toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' });

// В списке диалогов: сегодня — время, раньше — «Oct 12»
export function formatListTime(iso) {
  if (!iso) return '';
  const date = new Date(iso);
  const isToday = date.toDateString() === new Date().toDateString();
  return isToday
    ? formatTime(iso)
    : date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}
