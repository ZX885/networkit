"""Токены (подтверждение почты, сброс пароля, смена email): подписанные данные (django.core.signing),
без хранения в базе. У каждого назначения своя «соль» и срок действия."""

import hashlib
import hmac

from django.core import signing
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

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


# ── Сброс пароля ──

RESET_SALT = "users.password-reset"  # отдельная соль: токен подтверждения почты сюда не подойдёт
RESET_MAX_AGE_SECONDS = 60 * 60  # срок действия — 1 час


def _password_fingerprint(user):
    """Отпечаток текущего хэша пароля: после смены пароля старые ссылки перестают работать."""
    return hashlib.sha256(user.password.encode()).hexdigest()[:20]


def make_reset_uid(user):
    return urlsafe_base64_encode(force_bytes(user.pk))


def make_reset_token(user):
    payload = {"uid": user.pk, "email": user.email, "ph": _password_fingerprint(user)}
    return signing.dumps(payload, salt=RESET_SALT)


def read_reset_token(token):
    """Возвращает payload или бросает InvalidToken (подделка, просрочка, мусор)."""
    try:
        data = signing.loads(token, salt=RESET_SALT, max_age=RESET_MAX_AGE_SECONDS)
    except (signing.BadSignature, ValueError, TypeError):
        raise InvalidToken() from None
    if not isinstance(data, dict) or not {"uid", "email", "ph"} <= set(data):
        raise InvalidToken()
    return data


def reset_token_matches(user, data):
    """Токен выдан именно для этого пользователя, этого email и ЭТОГО пароля."""
    return (
        data["uid"] == user.pk
        and data["email"] == user.email
        and hmac.compare_digest(str(data["ph"]), _password_fingerprint(user))
    )


def decode_reset_uid(uid):
    try:
        return int(force_str(urlsafe_base64_decode(uid)))
    except (ValueError, TypeError, OverflowError, UnicodeDecodeError):
        raise InvalidToken() from None


# ── Смена email ──

EMAIL_CHANGE_SALT = "users.confirm-email-change"
EMAIL_CHANGE_MAX_AGE_SECONDS = 3 * 24 * 60 * 60  # срок действия — 3 дня


def make_email_change_token(user, new_email):
    return signing.dumps({"uid": user.pk, "new_email": new_email}, salt=EMAIL_CHANGE_SALT)


def read_email_change_token(token):
    try:
        data = signing.loads(token, salt=EMAIL_CHANGE_SALT, max_age=EMAIL_CHANGE_MAX_AGE_SECONDS)
    except (signing.BadSignature, ValueError, TypeError):
        raise InvalidToken() from None
    if not isinstance(data, dict) or "uid" not in data or "new_email" not in data:
        raise InvalidToken()
    return data
