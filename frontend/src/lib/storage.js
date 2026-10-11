// Безопасная работа с localStorage: в приватном режиме или при запрете доступ бросает исключение.
export function readStorage(key) {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

export function writeStorage(key, value) {
  try {
    localStorage.setItem(key, value);
  } catch {
    // Хранилище недоступно — работаем без сохранения выбора.
  }
}
