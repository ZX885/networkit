"""Лимиты запросов. Числа лежат в settings.THROTTLE_RATES, включение — settings.THROTTLING_ENABLED."""

import hashlib

from django.conf import settings
from rest_framework.throttling import AnonRateThrottle, SimpleRateThrottle, UserRateThrottle


class SwitchableMixin:
    """Позволяет отключить лимит настройкой (нужно тестам)."""

    def allow_request(self, request, view):
        if not settings.THROTTLING_ENABLED:
            return True
        return super().allow_request(request, view)


class AnonThrottle(SwitchableMixin, AnonRateThrottle):
    scope = "anon"


class UserThrottle(SwitchableMixin, UserRateThrottle):
    scope = "user"


class SearchThrottle(SwitchableMixin, UserRateThrottle):
    """Поиск людей: лимит на пользователя (scope search)."""

    scope = "search"


class SavedThrottle(SwitchableMixin, UserRateThrottle):
    """Добавление и удаление закладок: лимит на пользователя (scope saved)."""

    scope = "saved"


class MessageRequestThrottle(SwitchableMixin, UserRateThrottle):
    """Новые запросы на переписку: лимит на пользователя (scope message_request)."""

    scope = "message_request"


class MessageSendThrottle(SwitchableMixin, UserRateThrottle):
    """Сообщения в минуту (scope message_send)."""

    scope = "message_send"


class MessageSendDayThrottle(SwitchableMixin, UserRateThrottle):
    """Сообщения в сутки (scope message_send_day)."""

    scope = "message_send_day"


class AccountPasswordThrottle(SwitchableMixin, UserRateThrottle):
    """Проверки пароля (смена пароля, смена email, удаление аккаунта): общий лимит на пользователя,
    чтобы нельзя было подбирать пароль через разные адреса (scope account_password)."""

    scope = "account_password"


class IpThrottle(SwitchableMixin, SimpleRateThrottle):
    """Лимит по IP-адресу клиента (для входа, регистрации и т.п.)."""

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}


class LoginThrottle(IpThrottle):
    scope = "login"


class LoginHourThrottle(IpThrottle):
    scope = "login_hour"


class RegisterThrottle(IpThrottle):
    scope = "register"


class UsernameCheckThrottle(IpThrottle):
    scope = "username_check"


class EmailFlowThrottle(IpThrottle):
    """Письма сброса пароля и смены email: 5 в час по IP (scope email_flow)."""

    scope = "email_flow"


class EmailFlowDayThrottle(SwitchableMixin, SimpleRateThrottle):
    """Те же письма: 5 в сутки на адрес email из тела запроса (email или new_email), чтобы нельзя
    было засыпать письмами чужой ящик. Считается независимо от того, есть ли такой аккаунт."""

    scope = "email_flow_day"

    def get_cache_key(self, request, view):
        data = request.data if isinstance(request.data, dict) else {}
        value = data.get("email") or data.get("new_email")
        if not isinstance(value, str) or not value.strip():
            return None  # нет адреса — нечего считать (ошибку покажет валидация)
        digest = hashlib.sha256(value.strip().lower().encode()).hexdigest()
        return self.cache_format % {"scope": self.scope, "ident": digest}


class TokenConfirmThrottle(IpThrottle):
    """Подтверждение по ссылке из письма: лимит по IP против перебора токенов (scope token_confirm)."""

    scope = "token_confirm"


# Общие лимиты, которые нужно оставить у view, где throttle_classes задан явно
BASE_THROTTLES = [AnonThrottle, UserThrottle]
