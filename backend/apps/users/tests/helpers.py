"""Общие помощники для тестов API."""

import re

from django.core import mail
from django.utils import timezone

from apps.profiles.tests.factories import birth_date_for_age, make_profile, make_user

PASSWORD = "S3cure-pass-77"

# Ключи ответа Own-профиля (GET /api/me/ и вход): ровно этот набор, лишнее наружу не уходит
OWN_KEYS = {
    "email",
    "email_verified",
    "username",
    "first_name",
    "last_name",
    "date_of_birth",
    "age",
    "is_minor",
    "gender",
    "country",
    "country_label",
    "region",
    "city",
    "status",
    "status_label",
    "school",
    "university",
    "field",
    "field_label",
    "year_level",
    "bio",
    "interests",
    "languages",
    "goals",
    "contacts",
    "avatar_url",
    "privacy",
    "created_at",
}


def registration_payload(**overrides):
    """Правильное тело запроса регистрации (совершеннолетний человек)."""
    data = {
        "email": "jane@example.com",
        "password": PASSWORD,
        "username": "janedoe",
        "first_name": "Jane",
        "last_name": "Doe",
        "date_of_birth": birth_date_for_age(25).isoformat(),
        "country": "UZ",
        "city": "Tashkent",
        "status": "student",
        "field": "computer_science",
        "accepted_terms": True,
    }
    data.update(overrides)
    return data


def make_account(email="user@example.com", password=PASSWORD, verified=True, **profile_overrides):
    """Пользователь с профилем. По умолчанию почта подтверждена, пароль — PASSWORD."""
    user = make_user(
        email=email, password=password, email_verified_at=timezone.now() if verified else None
    )
    make_profile(user=user, **profile_overrides)
    return user


def error_of(response):
    """Блок "error" из JSON-ответа."""
    return response.json()["error"]


def field_codes(response, field):
    """Коды ошибок конкретного поля (ответ validation_error)."""
    return [item["code"] for item in error_of(response)["fields"][field]]


def token_from_last_email():
    """Токен подтверждения из ссылки в последнем отправленном письме."""
    return re.search(r"/verify-email/(\S+)", mail.outbox[-1].body).group(1)
