import re
import unicodedata
from datetime import date

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from .age import calculate_age

# Формат username: строчные латинские буквы, цифры, _; начинается с буквы; длина 3–30
USERNAME_REGEX = r"^[a-z][a-z0-9_]{2,29}$"

# Нельзя занимать: совпадает с адресами сайта и служебными именами (docs/SPEC.md §5,
# тот же список в frontend/src/constants/rules.js)
RESERVED_USERNAMES = {
    "admin",
    "api",
    "me",
    "settings",
    "login",
    "register",
    "support",
    "staff",
    "networkit",
}


def validate_username(value):
    if not re.fullmatch(USERNAME_REGEX, value):
        raise ValidationError(
            "Use 3–30 characters: lowercase letters, digits and _, starting with a letter.",
            code="invalid_format",
        )
    if "__" in value:
        raise ValidationError("Two underscores in a row are not allowed.", code="invalid_format")
    if value in RESERVED_USERNAMES:
        raise ValidationError("This username is not available.", code="reserved")


def validate_unique_items(value):
    """В списке (интересы, языки, цели) не должно быть повторов."""
    if len(set(value)) != len(value):
        raise ValidationError("Duplicate values are not allowed.", code="duplicate")


def validate_birth_date(value):
    """Дата рождения: не в будущем, возраст от MIN_AGE до MAX_AGE (из settings)."""
    if value > date.today():
        raise ValidationError("Date of birth cannot be in the future.", code="future")
    age = calculate_age(value)
    if age < settings.MIN_AGE:
        raise ValidationError(
            f"You must be at least {settings.MIN_AGE} years old.", code="too_young"
        )
    if age > settings.MAX_AGE:
        raise ValidationError("Please check the year of birth.", code="too_old")


# ── Валидаторы для API (регистрация, редактирование профиля) ──


def validate_person_name(value):
    """Имя и фамилия: буквы любого алфавита, пробел, дефис, апостроф, точка; начинается с буквы."""
    name = value.strip()
    allowed_extra = " '’.-"
    valid = (
        bool(name)
        and name[0].isalpha()
        and all(
            ch.isalpha() or ch in allowed_extra or unicodedata.category(ch).startswith("M")
            for ch in name
        )
    )
    if not valid:
        raise ValidationError(
            "Use letters, spaces, hyphens, apostrophes or dots only.", code="invalid_characters"
        )


def validate_no_angle_brackets(value):
    if "<" in value or ">" in value:
        raise ValidationError("The characters < and > are not allowed.", code="invalid_characters")


# Контакты. Каждая функция возвращает значение в том виде, в котором оно хранится,
# или бросает ValidationError(code="invalid").
def _invalid(message):
    raise ValidationError(message, code="invalid")


def clean_telegram(value):
    handle = value.strip().lstrip("@")
    if not re.fullmatch(r"[A-Za-z0-9_]{5,32}", handle):
        _invalid("Telegram: 5–32 letters, digits or underscores.")
    return handle


def clean_instagram(value):
    handle = value.strip().lstrip("@")
    if not re.fullmatch(r"[A-Za-z0-9._]{1,30}", handle):
        _invalid("Instagram: up to 30 letters, digits, dots or underscores.")
    return handle


def clean_whatsapp(value):
    number = re.sub(r"[\s()-]", "", value)
    if not re.fullmatch(r"\+[1-9][0-9]{6,14}", number):
        _invalid("WhatsApp: use international format, e.g. +998901234567.")
    return number


def clean_linkedin(value):
    match = re.fullmatch(
        r"(?:https?://)?(?:www\.)?(?:linkedin\.com/in/)?([\w%-]{3,100})/?", value.strip(), re.I
    )
    if not match:
        _invalid("LinkedIn: use a link like linkedin.com/in/your-name.")
    return f"https://www.linkedin.com/in/{match.group(1)}"


def clean_public_email(value):
    email = value.strip()
    try:
        validate_email(email)
    except ValidationError:
        _invalid("Enter a valid email address.")
    return email[:254]


CONTACT_CLEANERS = {
    "telegram": clean_telegram,
    "instagram": clean_instagram,
    "whatsapp": clean_whatsapp,
    "linkedin": clean_linkedin,
    "public_email": clean_public_email,
}
