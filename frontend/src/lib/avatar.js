// Цвет и инициалы аватара — как ac() и ah() в legacy app.js.
const AVATAR_COUNT = 8; // столько градиентов --avatar-N в tokens.css

// Номер градиента (1..8) по сумме кодов символов id — стабильно для одного пользователя.
export function getAvatarIndex(id) {
  if (!id) return 1;
  const sum = [...String(id)].reduce((acc, ch) => acc + ch.charCodeAt(0), 0);
  return (sum % AVATAR_COUNT) + 1;
}

// Две буквы: первая буква имени и первая буква фамилии.
export function getInitials(firstName, lastName) {
  const first = (firstName || '?')[0];
  const last = lastName ? lastName[0] : '';
  return (first + last).toUpperCase();
}
