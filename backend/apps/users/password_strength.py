"""Сила пароля: Weak / Medium / Strong. Формула ЕДИНАЯ с frontend (frontend/src/lib/passwordStrength.js);
общие тестовые пароли лежат в tests/password_cases.json и проверяются обеими реализациями.

Считаем в кодовых точках Unicode (эмодзи — один символ). Классы символов (0–4):
строчные (Ll), заглавные (Lu), цифры (Nd) и «прочие» (пробел, знаки, иероглифы, эмодзи…).

- Weak:   длина < 8, или классов < 2, или разных символов < 4;
- Strong: (длина ≥ 12 и классов ≥ 3) или (длина ≥ 16 и классов ≥ 2);
- Medium: всё остальное.
Принимаются Medium и Strong.
"""

import unicodedata

MIN_LENGTH = 8
MIN_CLASSES = 2
MIN_DISTINCT = 4  # разных символов: «aaaaaaa1» — не пароль
STRONG_LENGTH = 12
STRONG_CLASSES = 3
STRONG_LONG_LENGTH = 16

WEAK, MEDIUM, STRONG = "weak", "medium", "strong"


def character_classes(password):
    """Сколько видов символов в пароле (0–4)."""
    found = set()
    for char in password:
        category = unicodedata.category(char)
        if category == "Ll":
            found.add("lower")
        elif category == "Lu":
            found.add("upper")
        elif category == "Nd":
            found.add("digit")
        else:
            found.add("other")
    return len(found)


def password_strength(password):
    """Уровень пароля: 'weak', 'medium' или 'strong'."""
    length = len(password)
    classes = character_classes(password)
    if length < MIN_LENGTH or classes < MIN_CLASSES or len(set(password)) < MIN_DISTINCT:
        return WEAK
    if (length >= STRONG_LENGTH and classes >= STRONG_CLASSES) or length >= STRONG_LONG_LENGTH:
        return STRONG
    return MEDIUM
