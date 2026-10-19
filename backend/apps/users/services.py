"""Сценарии работы с учётными записями: регистрация, подтверждение почты, сброс и смена пароля,
смена email, удаление аккаунта, сессии. Пароли и токены нигде не логируются."""

import logging
from types import SimpleNamespace

from django.conf import settings
from django.contrib.auth import password_validation, update_session_auth_hash
from django.contrib.auth.hashers import make_password
from django.contrib.sessions.models import Session
from django.core import signing
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.template.loader import render_to_string
from django.utils import timezone
from rest_framework.exceptions import ErrorDetail, ValidationError

from apps.profiles.models import Profile
from config.exceptions import InvalidToken

from .models import User
from .tokens import (
    decode_reset_uid,
    make_email_change_token,
    make_reset_token,
    make_reset_uid,
    make_verification_token,
    read_email_change_token,
    read_reset_token,
    read_verification_token,
    reset_token_matches,
)

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


def _first_name(user):
    return getattr(getattr(user, "profile", None), "first_name", "") or "there"


def send_verification_email(user):
    link = f"{_site_url()}/verify-email/{make_verification_token(user)}"
    log_demo_link(link)
    _send_email(
        user.email,
        "Confirm your NetworkIt email",
        "users/emails/verify_email.txt",
        {"link": link, "first_name": _first_name(user)},
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


def delete_user_sessions(user_ids, keep_session_key=None):
    """Завершает все живые сессии указанных пользователей (бан, смена и сброс пароля, удаление
    аккаунта). keep_session_key — сессия, которую нужно оставить (текущая при смене пароля).
    Backlog: перебор всех сессий не масштабируется, нужна связь «сессия → пользователь»."""
    ids = {str(pk) for pk in user_ids}
    keys = [
        session.session_key
        for session in Session.objects.filter(expire_date__gt=timezone.now())
        if session.session_key != keep_session_key
        and session.get_decoded().get("_auth_user_id") in ids
    ]
    Session.objects.filter(session_key__in=keys).delete()
    return len(keys)


# ── Пароль: проверка нового пароля, уведомление ──


def password_subject(user):
    """Данные пользователя для проверки «пароль слишком похож на email или имя»."""
    profile = getattr(user, "profile", None)
    return SimpleNamespace(
        email=user.email,
        username=getattr(profile, "username", ""),
        first_name=getattr(profile, "first_name", ""),
        last_name=getattr(profile, "last_name", ""),
        # Валидатору «похож на данные пользователя» нужно имя поля для текста ошибки
        _meta=SimpleNamespace(get_field=lambda name: SimpleNamespace(verbose_name=name)),
    )


def validate_new_password(password, user):
    """Все проверки нового пароля (сила не ниже Medium, сходство с email и именем, частые пароли).
    Бросает django ValidationError (в сериализаторе превращается в ошибку поля)."""
    password_validation.validate_password(password, user=password_subject(user))


def send_password_changed_email(user):
    """Уведомление «пароль изменён»: без ссылок на вход, только предупреждение."""
    _send_email(
        user.email,
        "Your password was changed",
        "users/emails/password_changed.txt",
        {"first_name": _first_name(user)},
    )


# ── Сброс пароля ──


def request_password_reset(email):
    """Письмо со ссылкой сброса — только существующему, подтверждённому и незабаненному пользователю.
    Для остальных делается эквивалентная работа (подпись и рендер), чтобы ответ не выдавал, есть ли
    аккаунт. Вызывающий всегда отвечает одинаково (202). Выравнивание времени отправки письма — позже,
    вместе с реальной почтой."""
    user = User.objects.filter(email=email).select_related("profile").first()
    eligible = user is not None and user.email_verified_at is not None and not user.is_banned
    if not eligible:
        dummy = signing.dumps({"x": 1}, salt="users.password-reset")
        render_to_string(
            "users/emails/reset_password.txt",
            {"link": f"{_site_url()}/reset-password/x/{dummy}", "first_name": "there"},
        )
        return
    link = f"{_site_url()}/reset-password/{make_reset_uid(user)}/{make_reset_token(user)}"
    log_demo_link(link)
    _send_email(
        user.email,
        "Reset your NetworkIt password",
        "users/emails/reset_password.txt",
        {"link": link, "first_name": _first_name(user)},
    )


def get_reset_user(uid, token):
    """Пользователь по ссылке сброса или InvalidToken: одинаково для просроченной, подделанной,
    использованной ссылки, чужого uid, забаненного и неподтверждённого пользователя."""
    if not isinstance(uid, str) or not isinstance(token, str):
        raise InvalidToken()
    data = read_reset_token(token.strip())
    user = User.objects.select_related("profile").filter(pk=decode_reset_uid(uid.strip())).first()
    if (
        user is None
        or user.is_banned
        or user.email_verified_at is None
        or not reset_token_matches(user, data)
    ):
        raise InvalidToken()
    return user


def reset_password(uid, token, get_new_password):
    """Сброс пароля по ссылке. get_new_password(user) возвращает новый пароль после его проверки;
    вызывается после проверки токена (неверный токен важнее слабого пароля). После смены удаляются
    ВСЕ сессии пользователя."""
    user = get_reset_user(uid, token)
    new_password = get_new_password(user)
    with transaction.atomic():
        locked = User.objects.select_for_update().get(pk=user.pk)
        if not reset_token_matches(locked, read_reset_token(token.strip())):
            raise InvalidToken()  # ссылку успели использовать параллельным запросом
        locked.set_password(new_password)
        locked.save(update_fields=["password"])
    delete_user_sessions([user.pk])
    send_password_changed_email(user)


# ── Смена пароля ──


def change_password(request, user, new_password):
    """Новый пароль для вошедшего: текущая сессия остаётся, остальные завершаются."""
    user.set_password(new_password)
    user.save(update_fields=["password"])
    update_session_auth_hash(request, user)  # обновляет хэш в текущей сессии (её ключ при этом меняется)
    delete_user_sessions([user.pk], keep_session_key=request.session.session_key)
    send_password_changed_email(user)


# ── Смена email ──


def request_email_change(user, new_email):
    """Запрос смены адреса: ссылка на НОВЫЙ адрес, уведомление на СТАРЫЙ. Если новый адрес совпадает с
    текущим или занят, наружу ничего не отличается: занятому адресу уходит письмо «адрес уже
    используется»."""
    if new_email == user.email:
        return
    first_name = _first_name(user)
    _send_email(
        user.email,
        "Someone asked to change your NetworkIt email",
        "users/emails/email_change_notice.txt",
        {"first_name": first_name, "new_email": new_email},
    )
    if User.objects.filter(email__iexact=new_email).exclude(pk=user.pk).exists():
        _send_email(
            new_email,
            "This email is already used on NetworkIt",
            "users/emails/email_in_use.txt",
            {},
        )
        return
    User.objects.filter(pk=user.pk).update(pending_email=new_email)
    link = f"{_site_url()}/confirm-email-change/{make_email_change_token(user, new_email)}"
    log_demo_link(link)
    _send_email(
        new_email,
        "Confirm your new NetworkIt email",
        "users/emails/email_change_confirm.txt",
        {"link": link, "first_name": first_name},
    )


def confirm_email_change(token):
    """Применяет смену адреса. Любая проблема — один и тот же InvalidToken. Токен одноразовый: после
    применения pending_email очищается; токен прежнего запроса не подходит, если адрес запрошен заново."""
    data = read_email_change_token(token)
    try:
        with transaction.atomic():
            user = (
                User.objects.select_for_update()
                .filter(pk=data["uid"], pending_email=data["new_email"])
                .first()
            )
            taken = (
                user is not None
                and User.objects.filter(email__iexact=data["new_email"]).exclude(pk=user.pk).exists()
            )
            if user is None or taken:
                raise InvalidToken()
            old_email = user.email
            user.email = data["new_email"]
            user.email_verified_at = timezone.now()  # адрес подтверждён самой ссылкой
            user.pending_email = None
            user.save(update_fields=["email", "email_verified_at", "pending_email"])
    except IntegrityError:
        raise InvalidToken() from None
    # Прежний адрес узнаёт о смене: если это не владелец, он успеет сбросить пароль
    _send_email(
        old_email,
        "Your email was changed",
        "users/emails/email_changed.txt",
        {"first_name": _first_name(user), "new_email": user.email},
    )
    return user


# ── Удаление аккаунта ──


def delete_account_files(user_id):
    """Точка расширения: удаление файлов аватара (появится в B4b). Вызывается после удаления."""


def delete_account(user):
    """Удаляет пользователя и все его сессии в одной транзакции. Каскадом уходят профиль, закладки
    (его и на него), диалоги с сообщениями; блокировки и жалобы (приложение moderation) — по их
    on_delete: жалобы автора остаются без автора, жалобы на человека удаляются."""
    user_id = user.pk
    with transaction.atomic():
        user.delete()
        delete_user_sessions([user_id])
        transaction.on_commit(lambda: delete_account_files(user_id))
