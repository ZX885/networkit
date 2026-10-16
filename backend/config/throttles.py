"""Лимиты запросов. Числа лежат в settings.THROTTLE_RATES, включение — settings.THROTTLING_ENABLED."""

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


class BlockThrottle(SwitchableMixin, UserRateThrottle):
    """Блокировка и разблокировка (scope block)."""

    scope = "block"


class ReportThrottle(SwitchableMixin, UserRateThrottle):
    """Жалобы (scope report)."""

    scope = "report"


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


# Общие лимиты, которые нужно оставить у view, где throttle_classes задан явно
BASE_THROTTLES = [AnonThrottle, UserThrottle]
