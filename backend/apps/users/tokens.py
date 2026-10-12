"""Токен подтверждения почты: подписанные данные (django.core.signing), без хранения в базе."""

from django.core import signing

from config.exceptions import InvalidToken

SALT = "users.verify-email"  # «соль»: токен от другого назначения не подойдёт
MAX_AGE_SECONDS = 3 * 24 * 60 * 60  # срок действия — 3 дня


def make_verification_token(user):
    return signing.dumps({"uid": user.pk, "email": user.email}, salt=SALT)


def read_verification_token(token):
    """Возвращает {"uid", "email"} или бросает InvalidToken (подделка, просрочка, мусор)."""
    try:
        data = signing.loads(token, salt=SALT, max_age=MAX_AGE_SECONDS)
    except (signing.BadSignature, ValueError, TypeError):
        raise InvalidToken() from None
    if not isinstance(data, dict) or "uid" not in data or "email" not in data:
        raise InvalidToken()
    return data
