// Сила пароля: Weak / Medium / Strong. Формула ЕДИНАЯ с backend (backend/apps/users/password_strength.py);
// общие тестовые пароли — backend/apps/users/tests/password_cases.json (проверяются обеими реализациями).
//
// Длина считается в кодовых точках Unicode ([...s].length, эмодзи — один символ). Классы символов:
// строчные, заглавные, цифры и «прочие» (пробел, знаки, иероглифы, эмодзи…).
//   Weak:   длина < 8, или классов < 2, или разных символов < 4;
//   Strong: (длина ≥ 12 и классов ≥ 3) или (длина ≥ 16 и классов ≥ 2);
//   Medium: всё остальное. Принимаются Medium и Strong.
// Модуль не зависит от React и текстов: подсказки возвращаются кодами, тексты лежат в texts/en.js.

export const PASSWORD_MIN_LENGTH = 8;
export const PASSWORD_MIN_CLASSES = 2;
export const PASSWORD_MIN_DISTINCT = 4;
const STRONG_LENGTH = 12;
const STRONG_CLASSES = 3;
const STRONG_LONG_LENGTH = 16;

const CLASS_PATTERNS = [/\p{Ll}/u, /\p{Lu}/u, /\p{Nd}/u];

// Сколько видов символов в пароле (0–4)
function countClasses(chars) {
  const found = new Set();
  chars.forEach((char) => {
    const index = CLASS_PATTERNS.findIndex((pattern) => pattern.test(char));
    found.add(index === -1 ? 3 : index);
  });
  return found.size;
}

// → { level: 'empty'|'weak'|'medium'|'strong', filled: 0–3 (сегментов полосы), hint: код подсказки | null }
// hint: minLength | moreVariety | addClass (слабый пароль) · addSymbolOrNumber | moreLength (чтобы стать Strong)
export function getPasswordStrength(password) {
  const chars = [...password];
  if (chars.length === 0) return { level: 'empty', filled: 0, hint: null };

  const length = chars.length;
  const classes = countClasses(chars);
  const distinct = new Set(chars).size;

  if (
    length < PASSWORD_MIN_LENGTH ||
    classes < PASSWORD_MIN_CLASSES ||
    distinct < PASSWORD_MIN_DISTINCT
  ) {
    let hint = 'addClass';
    if (length < PASSWORD_MIN_LENGTH) hint = 'minLength';
    else if (classes >= PASSWORD_MIN_CLASSES) hint = 'moreVariety';
    return { level: 'weak', filled: 1, hint };
  }
  if ((length >= STRONG_LENGTH && classes >= STRONG_CLASSES) || length >= STRONG_LONG_LENGTH) {
    return { level: 'strong', filled: 3, hint: null };
  }
  // Medium: подсказываем самый короткий путь к Strong
  const hint = classes < STRONG_CLASSES ? 'addSymbolOrNumber' : 'moreLength';
  return { level: 'medium', filled: 2, hint };
}

// Принимаются Medium и Strong
export const isPasswordAcceptable = (password) => {
  const { level } = getPasswordStrength(password);
  return level === 'medium' || level === 'strong';
};
