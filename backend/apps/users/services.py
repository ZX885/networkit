"""Сценарии работы с учётными записями: регистрация, подтверждение почты, сессии."""

import logging

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.sessions.models import Session
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.template.loader import render_to_string
from django.utils import timezone
from rest_framework.exceptions import ErrorDetail, ValidationError

from apps.profiles.models import Profile
from config.exceptions import InvalidToken

from .models import User
from .tokens import make_verification_token, read_verification_token

logger = logging.getLogger(__name__)

PROFILE_FIELDS = (
    "username",
    "first_name",
    "last_name",
    "date_of_birth",
    "gender",
    "country",
    "region",
    "city",
    "status",
    "school",
    "university",
    "field",
    "year_level",
    "bio",
    "interests",
    "languages",
    "goals",
)


def _site_url():
    return settings.SITE_URL.rstrip("/")


def _send_email(to_email, subject, template, context):
    """Отправка письма. Сбой почты не должен ломать запрос: человек сможет запросить письмо снова."""
    body = render_to_string(template, context)
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [to_email])
    except Exception:  # noqa: BLE001 — любая ошибка SMTP только пишется в лог
        logger.exception("Could not send email %r to user", subject)


def log_demo_link(link):
    """Ссылка из письма в лог одной строкой (в консольном письме длинные строки переносятся).
    Только при DEBUG или DEMO_LOG_VERIFY_LINKS (демо без SMTP); на боевом сайте не включать."""
    if settings.DEBUG or settings.DEMO_LOG_VERIFY_LINKS:
        logger.info("DEMO link: %s", link)


def send_verification_email(user):
    link = f"{_site_url()}/verify-email/{make_verification_token(user)}"
    log_demo_link(link)
    first_name = getattr(getattr(user, "profile", None), "first_name", "") or "there"
    _send_email(
        user.email,
        "Confirm your NetworkIt email",
        "users/emails/verify_email.txt",
        {"link": link, "first_name": first_name},
    )


def send_already_registered_email(user):
    _send_email(
        user.email,
        "You already have a NetworkIt account",
        "users/emails/already_registered.txt",
        {"login_link": f"{_site_url()}/login"},
    )


def _handle_existing_account(user, password):
    """Email уже занят: нового аккаунта нет, человеку уходит письмо. Ответ API тот же, что при успехе."""
    make_password(password)  # то же время, что и при создании аккаунта (не выдаём наличие email)
    if user.email_verified_at is None:
        send_verification_email(user)
    else:
        send_already_registered_email(user)


def register_account(data):
    """Создаёт User и Profile в одной транзакции и отправляет письмо подтверждения.

    data — проверенные данные RegisterSerializer. Если email уже занят, аккаунт не создаётся.
    """
    email = data["email"]
    existing = User.objects.filter(email=email).first()
    if existing:
        _handle_existing_account(existing, data["password"])
        return

    profile_data = {name: data[name] for name in PROFILE_FIELDS if name in data}
    profile_data.update(data.get("contacts", {}))
    try:
        with transaction.atomic():
            user = User.objects.create_user(email=email, password=data["password"])
            Profile.objects.create(user=user, **profile_data)
    except IntegrityError:
        # Параллельный запрос успел раньше: либо тот же email, либо тот же username
        existing = User.objects.filter(email=email).first()
        if existing:
            _handle_existing_account(existing, data["password"])
            return
        taken = ErrorDetail("This username is already taken.", code="taken")
        raise ValidationError({"username": [taken]}) from None

    send_verification_email(user)


def verify_email(token):
    """Подтверждает почту по токену. Любая проблема с токеном — один и тот же InvalidToken."""
    data = read_verification_token(token)
    # Одним запросом: сработает только пока почта не подтверждена (токен одноразовый)
    updated = User.objects.filter(
        pk=data["uid"], email=data["email"], email_verified_at__isnull=True
    ).update(email_verified_at=timezone.now())
    if not updated:
        raise InvalidToken()


def resend_verification(email):
    """Повторно шлёт письмо, если аккаунт есть и не подтверждён. Вызывающий всегда отвечает одинаково."""
    user = User.objects.filter(email=email, email_verified_at__isnull=True).first()
    if user and not user.is_banned:
        send_verification_email(user)


def delete_user_sessions(user_ids):
    """Завершает все живые сессии указанных пользователей (нужно при бане)."""
    ids = {str(pk) for pk in user_ids}
    keys = [
        session.session_key
        for session in Session.objects.filter(expire_date__gt=timezone.now())
        if session.get_decoded().get("_auth_user_id") in ids
    ]
    Session.objects.filter(session_key__in=keys).delete()
    return len(keys)
