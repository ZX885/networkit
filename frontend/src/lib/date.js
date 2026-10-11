// Работа с датой рождения, введённой как три числа (день, месяц, год).

// Существует ли такая дата (31 февраля, месяц 13 и т.п. — нет)
export function isRealDate(year, month, day) {
  const date = new Date(year, month - 1, day);
  return date.getFullYear() === year && date.getMonth() === month - 1 && date.getDate() === day;
}

// Полных лет на сегодня (или на дату today — удобно для тестов)
export function getAge(year, month, day, today = new Date()) {
  let age = today.getFullYear() - year;
  const hadBirthday =
    today.getMonth() + 1 > month || (today.getMonth() + 1 === month && today.getDate() >= day);
  if (!hadBirthday) age -= 1;
  return age;
}

// Дата в формате YYYY-MM-DD для отправки на сервер
export function toIsoDate(year, month, day) {
  return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
}
