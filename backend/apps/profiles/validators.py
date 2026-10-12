import re
from datetime import date

from django.conf import settings
from django.core.exceptions import ValidationError

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
