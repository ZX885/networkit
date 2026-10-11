// Превращает список названий в список { code, label }, код — snake_case от названия:
// 'Computer Science' → 'computer_science'. Нужен для справочников без готовых кодов.
export function toOptions(labels) {
  return labels.map((label) => ({
    code: label
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '_')
      .replace(/^_|_$/g, ''),
    label,
  }));
}
