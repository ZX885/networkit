"""Валидатор силы пароля для AUTH_PASSWORD_VALIDATORS: слабый пароль отклоняется, нужен минимум Medium.
Подключается в настройках, поэтому работает везде, где вызывается validate_password (регистрация, позже
смена и сброс пароля). Пароль не попадает ни в текст ошибки, ни в параметры."""

from django.core.exceptions import ValidationError

from .password_strength import WEAK, password_strength

MESSAGE = (
    "This password is too weak. Use at least 8 characters, at least 4 different ones, "
    "and mix at least two kinds: lowercase, uppercase, digits or symbols."
)


class PasswordStrengthValidator:
    def validate(self, password, user=None):
        if password_strength(password) == WEAK:
            # Код password_too_weak; клиенту он приходит как too_weak (config.exceptions.normalize_code)
            raise ValidationError(MESSAGE, code="password_too_weak")

    def get_help_text(self):
        return "Your password must be at least Medium strength."
